/*
 * open62541_source_simulator.c
 * ----------------------------
 * 中文说明：
 * 1. 这是一个基于 open62541 的轻量 OPC UA 模拟服务端。
 * 2. 它从 TSV 配置文件读取 endpoint、namespace、节点定义和更新策略，
 *    然后在本地启动一个可被测试代码连接的 OPC UA 服务器。
 * 3. 服务端既支持通过 stdin 接收外部 write 命令主动写值，
 *    也支持按固定间隔执行内部自动更新，用于压测采集链路。
 * 4. 地址空间会按逻辑路径自动补齐对象层级，再挂载变量节点。
 * 5. 本文件重点关注“快速搭建可重复的测试服务器”，而不是通用工业建模能力。
 */
#define _POSIX_C_SOURCE 200809L

#include <open62541/server.h>
#include <open62541/server_config_default.h>

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <time.h>
#include <unistd.h>

#define MAX_LINE_LEN 8192

typedef struct NodeConfig {
    char *node_id;
    char *browse_name;
    char *display_name;
    char *data_type;
    char *initial_value;
    unsigned long update_counter;
    struct NodeConfig *next;
} NodeConfig;

typedef struct AppConfig {
    char *endpoint;
    char *namespace_uri;
    bool update_enabled;
    unsigned long update_interval_ms;
    bool update_all;
    NodeConfig *nodes;
} AppConfig;

typedef struct StringSetItem {
    char *value;
    struct StringSetItem *next;
} StringSetItem;

static volatile UA_Boolean running = true;
static UA_Logger g_null_logger = {0};

static void disable_server_logging(UA_ServerConfig *config) {
    if (config == NULL) {
        return;
    }
    config->logging = &g_null_logger;
    if (config->eventLoop != NULL) {
        config->eventLoop->logger = &g_null_logger;
    }
}

/* 收到终止信号后退出主循环，走正常 shutdown 路径释放资源。 */
static void stop_handler(int sig) {
    (void)sig;
    running = false;
}

/* strdup 的本地包装，统一处理分配失败。 */
static char *xstrdup(const char *value) {
    size_t len = strlen(value);
    char *copy = (char *)malloc(len + 1);
    if (copy == NULL) {
        return NULL;
    }
    memcpy(copy, value, len + 1);
    return copy;
}

/* 解析配置中的布尔文本，兼容常见 true/false 写法。 */
static bool parse_bool(const char *value) {
    if (value == NULL) {
        return false;
    }

    return strcmp(value, "1") == 0 ||
           strcmp(value, "true") == 0 ||
           strcmp(value, "TRUE") == 0 ||
           strcmp(value, "yes") == 0 ||
           strcmp(value, "YES") == 0 ||
           strcmp(value, "on") == 0 ||
           strcmp(value, "ON") == 0;
}

/* 去掉配置行或 stdin 命令行末尾的换行符。 */
static void strip_newline(char *line) {
    size_t len = strlen(line);
    while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r')) {
        line[len - 1] = '\0';
        len--;
    }
}

/* 按制表符切分 TSV 记录或 stdin 文本命令。 */
static bool split_fields(char *line, char **fields, int max_fields, int *field_count) {
    int count = 0;
    char *cursor = line;

    while (cursor != NULL && count < max_fields) {
        fields[count++] = cursor;

        char *tab = strchr(cursor, '\t');
        if (tab == NULL) {
            break;
        }

        *tab = '\0';
        cursor = tab + 1;
    }

    *field_count = count;
    return true;
}

/* 释放整份配置及其节点链表。 */
static void free_config(AppConfig *config) {
    if (config == NULL) {
        return;
    }

    free(config->endpoint);
    free(config->namespace_uri);

    NodeConfig *node = config->nodes;
    while (node != NULL) {
        NodeConfig *next = node->next;
        free(node->node_id);
        free(node->browse_name);
        free(node->display_name);
        free(node->data_type);
        free(node->initial_value);
        free(node);
        node = next;
    }

    config->endpoint = NULL;
    config->namespace_uri = NULL;
    config->nodes = NULL;
}

/* 解析单条 node 记录并追加到配置链表。 */
static bool append_node_config(AppConfig *config, char **fields, int field_count) {
    if (field_count != 6) {
        fprintf(stderr, "Invalid node line: expected 6 fields, got %d\n", field_count);
        return false;
    }

    if (
        strcmp(fields[4], "Double") != 0 &&
        strcmp(fields[4], "Int32") != 0 &&
        strcmp(fields[4], "Boolean") != 0 &&
        strcmp(fields[4], "String") != 0
    ) {
        fprintf(stderr, "Unsupported node data_type in config: %s\n", fields[4]);
        return false;
    }

    NodeConfig *node = (NodeConfig *)calloc(1, sizeof(NodeConfig));
    if (node == NULL) {
        return false;
    }

    node->node_id = xstrdup(fields[1]);
    node->browse_name = xstrdup(fields[2]);
    node->display_name = xstrdup(fields[3]);
    node->data_type = xstrdup(fields[4]);
    node->initial_value = xstrdup(fields[5]);
    node->update_counter = 0;

    if (
        node->node_id == NULL ||
        node->browse_name == NULL ||
        node->display_name == NULL ||
        node->data_type == NULL ||
        node->initial_value == NULL
    ) {
        free(node->node_id);
        free(node->browse_name);
        free(node->display_name);
        free(node->data_type);
        free(node->initial_value);
        free(node);
        return false;
    }

    node->next = config->nodes;
    config->nodes = node;
    return true;
}

/* 从 TSV 配置文件加载服务端基础配置和节点列表。 */
static bool load_config(const char *path, AppConfig *config) {
    config->update_enabled = false;
    config->update_interval_ms = 1000;
    config->update_all = true;

    FILE *fp = fopen(path, "r");
    if (fp == NULL) {
        perror("Failed to open config file");
        return false;
    }

    char line[MAX_LINE_LEN];

    while (fgets(line, sizeof(line), fp) != NULL) {
        strip_newline(line);

        if (line[0] == '\0' || line[0] == '#') {
            continue;
        }

        char *fields[8] = {0};
        int field_count = 0;
        split_fields(line, fields, 8, &field_count);

        if (field_count <= 0) {
            continue;
        }

        if (strcmp(fields[0], "endpoint") == 0) {
            if (field_count != 2) {
                fprintf(stderr, "Invalid endpoint line\n");
                fclose(fp);
                return false;
            }
            config->endpoint = xstrdup(fields[1]);
        } else if (strcmp(fields[0], "namespace_uri") == 0) {
            if (field_count != 2) {
                fprintf(stderr, "Invalid namespace_uri line\n");
                fclose(fp);
                return false;
            }
            config->namespace_uri = xstrdup(fields[1]);
        } else if (strcmp(fields[0], "update_enabled") == 0) {
            if (field_count != 2) {
                fprintf(stderr, "Invalid update_enabled line\n");
                fclose(fp);
                return false;
            }
            config->update_enabled = parse_bool(fields[1]);
        } else if (strcmp(fields[0], "update_interval_ms") == 0) {
            if (field_count != 2) {
                fprintf(stderr, "Invalid update_interval_ms line\n");
                fclose(fp);
                return false;
            }
            long interval = strtol(fields[1], NULL, 10);
            config->update_interval_ms = interval > 0 ? (unsigned long)interval : 1000;
        } else if (strcmp(fields[0], "update_all") == 0) {
            if (field_count != 2) {
                fprintf(stderr, "Invalid update_all line\n");
                fclose(fp);
                return false;
            }
            config->update_all = parse_bool(fields[1]);
        } else if (strcmp(fields[0], "node") == 0) {
            if (!append_node_config(config, fields, field_count)) {
                fclose(fp);
                return false;
            }
        } else {
            fprintf(stderr, "Unknown TSV record type: %s\n", fields[0]);
            fclose(fp);
            return false;
        }
    }

    fclose(fp);

    if (config->endpoint == NULL || config->namespace_uri == NULL) {
        fprintf(stderr, "Config requires endpoint and namespace_uri\n");
        return false;
    }

    if (config->nodes == NULL) {
        fprintf(stderr, "Config requires at least one node\n");
        return false;
    }

    return true;
}

/* 从 endpoint 文本中提取端口；解析失败时退回 4840。 */
static unsigned short parse_endpoint_port(const char *endpoint) {
    const char *colon = strrchr(endpoint, ':');
    if (colon == NULL || *(colon + 1) == '\0') {
        return 4840;
    }

    long port = strtol(colon + 1, NULL, 10);
    if (port <= 0 || port > 65535) {
        return 4840;
    }

    return (unsigned short)port;
}

/* 以下 string set 用于记录已经创建过的对象层级，避免重复建树。 */
static bool string_set_contains(StringSetItem *head, const char *value) {
    for (StringSetItem *item = head; item != NULL; item = item->next) {
        if (strcmp(item->value, value) == 0) {
            return true;
        }
    }
    return false;
}

static bool string_set_add(StringSetItem **head, const char *value) {
    if (string_set_contains(*head, value)) {
        return true;
    }

    StringSetItem *item = (StringSetItem *)calloc(1, sizeof(StringSetItem));
    if (item == NULL) {
        return false;
    }

    item->value = xstrdup(value);
    if (item->value == NULL) {
        free(item);
        return false;
    }

    item->next = *head;
    *head = item;
    return true;
}

static void free_string_set(StringSetItem *head) {
    while (head != NULL) {
        StringSetItem *next = head->next;
        free(head->value);
        free(head);
        head = next;
    }
}

/* 使用点号拼接逻辑层级片段，例如 IED.LD.LN。 */
static char *join_parts(char **parts, int count) {
    size_t len = 0;

    for (int i = 0; i < count; i++) {
        len += strlen(parts[i]);
        if (i > 0) {
            len += 1;
        }
    }

    char *result = (char *)calloc(len + 1, sizeof(char));
    if (result == NULL) {
        return NULL;
    }

    for (int i = 0; i < count; i++) {
        if (i > 0) {
            strcat(result, ".");
        }
        strcat(result, parts[i]);
    }

    return result;
}

/* 把类似 WindFarm.WT01.MMXU.TotW 的逻辑路径按点切分。 */
static int split_node_id_parts(const char *node_id, char **parts, int max_parts) {
    char *copy = xstrdup(node_id);
    if (copy == NULL) {
        return 0;
    }

    int count = 0;
    char *cursor = copy;

    while (cursor != NULL && count < max_parts) {
        parts[count++] = cursor;

        char *dot = strchr(cursor, '.');
        if (dot == NULL) {
            break;
        }

        *dot = '\0';
        cursor = dot + 1;
    }

    for (int i = 0; i < count; i++) {
        parts[i] = xstrdup(parts[i]);
    }

    free(copy);

    for (int i = 0; i < count; i++) {
        if (parts[i] == NULL) {
            for (int j = 0; j < i; j++) {
                free(parts[j]);
            }
            return 0;
        }
    }

    return count;
}

static void free_parts(char **parts, int count) {
    for (int i = 0; i < count; i++) {
        free(parts[i]);
    }
}

/* 从变量节点路径反推出其父对象路径。 */
static char *parent_path_from_node_id(const char *node_id) {
    const char *last_dot = strrchr(node_id, '.');
    if (last_dot == NULL || last_dot == node_id) {
        return NULL;
    }

    size_t len = (size_t)(last_dot - node_id);
    char *parent = (char *)calloc(len + 1, sizeof(char));
    if (parent == NULL) {
        return NULL;
    }

    memcpy(parent, node_id, len);
    parent[len] = '\0';
    return parent;
}

/* 向地址空间添加对象节点，用于构建 IED/LD/LN 层级。 */
static UA_StatusCode add_object_node(
    UA_Server *server,
    UA_UInt16 ns_idx,
    const char *node_id,
    const char *browse_name,
    const char *display_name,
    const char *parent_node_id,
    bool parent_is_objects_folder,
    bool use_organizes_ref
) {
    UA_ObjectAttributes attr = UA_ObjectAttributes_default;
    attr.displayName = UA_LOCALIZEDTEXT_ALLOC("en-US", display_name);

    UA_NodeId requested = UA_NODEID_STRING_ALLOC(ns_idx, node_id);
    UA_QualifiedName qn = UA_QUALIFIEDNAME_ALLOC(ns_idx, browse_name);

    UA_NodeId parent;
    if (parent_is_objects_folder) {
        parent = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER);
    } else {
        parent = UA_NODEID_STRING_ALLOC(ns_idx, parent_node_id);
    }

    UA_NodeId ref = use_organizes_ref
        ? UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES)
        : UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT);

    UA_NodeId type_definition = use_organizes_ref
        ? UA_NODEID_NUMERIC(0, UA_NS0ID_FOLDERTYPE)
        : UA_NODEID_NUMERIC(0, UA_NS0ID_BASEOBJECTTYPE);

    UA_StatusCode status = UA_Server_addObjectNode(
        server,
        requested,
        parent,
        ref,
        qn,
        type_definition,
        attr,
        NULL,
        NULL
    );

    UA_ObjectAttributes_clear(&attr);
    UA_NodeId_clear(&requested);
    UA_QualifiedName_clear(&qn);

    if (!parent_is_objects_folder) {
        UA_NodeId_clear(&parent);
    }

    return status;
}

/* 根据 TSV 中的文本值和数据类型构造 UA_Variant。 */
static UA_StatusCode build_variant_from_text(
    UA_Variant *variant,
    UA_NodeId *data_type,
    const char *type_name,
    const char *value
) {
    UA_Variant_init(variant);

    if (strcmp(type_name, "Double") == 0) {
        UA_Double parsed = strtod(value, NULL);
        *data_type = UA_TYPES[UA_TYPES_DOUBLE].typeId;
        return UA_Variant_setScalarCopy(variant, &parsed, &UA_TYPES[UA_TYPES_DOUBLE]);
    }

    if (strcmp(type_name, "Int32") == 0) {
        UA_Int32 parsed = (UA_Int32)strtol(value, NULL, 10);
        *data_type = UA_TYPES[UA_TYPES_INT32].typeId;
        return UA_Variant_setScalarCopy(variant, &parsed, &UA_TYPES[UA_TYPES_INT32]);
    }

    if (strcmp(type_name, "Boolean") == 0) {
        UA_Boolean parsed = parse_bool(value);
        *data_type = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
        return UA_Variant_setScalarCopy(variant, &parsed, &UA_TYPES[UA_TYPES_BOOLEAN]);
    }

    if (strcmp(type_name, "String") == 0) {
        UA_String parsed = UA_STRING((char *)value);
        *data_type = UA_TYPES[UA_TYPES_STRING].typeId;
        return UA_Variant_setScalarCopy(variant, &parsed, &UA_TYPES[UA_TYPES_STRING]);
    }

    return UA_STATUSCODE_BADTYPEMISMATCH;
}

/* 统一封装节点写值，确保 value/status/timestamp 一起写入。 */
static UA_StatusCode write_node_value(
    UA_Server *server,
    UA_UInt16 ns_idx,
    const char *node_id,
    const char *data_type,
    const char *value
) {
    UA_NodeId target = UA_NODEID_STRING_ALLOC(ns_idx, node_id);

    UA_Variant variant;
    UA_NodeId type_id = UA_NODEID_NULL;
    UA_StatusCode status = build_variant_from_text(&variant, &type_id, data_type, value);
    if (status != UA_STATUSCODE_GOOD) {
        UA_NodeId_clear(&target);
        fprintf(stderr, "Failed to build variant for %s type=%s value=%s: 0x%08x\n",
                node_id, data_type, value, status);
        return status;
    }

    UA_DateTime now = UA_DateTime_now();

    UA_DataValue data_value;
    UA_DataValue_init(&data_value);
    data_value.hasValue = true;
    data_value.value = variant;
    data_value.hasStatus = true;
    data_value.status = UA_STATUSCODE_GOOD;
    data_value.hasSourceTimestamp = true;
    data_value.sourceTimestamp = now;

    status = UA_Server_writeDataValue(server, target, data_value);

    UA_DataValue_clear(&data_value);
    UA_NodeId_clear(&target);

    if (status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "Failed to write node %s: 0x%08x\n", node_id, status);
    }

    return status;
}

/* 把一个变量节点挂到已经建立好的父对象层级下。 */
static UA_StatusCode add_variable_node(
    UA_Server *server,
    UA_UInt16 ns_idx,
    const NodeConfig *node
) {
    char *parent_path = parent_path_from_node_id(node->node_id);
    if (parent_path == NULL) {
        fprintf(stderr, "Invalid variable node_id, cannot build parent path: %s\n", node->node_id);
        return UA_STATUSCODE_BADNODEIDINVALID;
    }

    UA_VariableAttributes attr = UA_VariableAttributes_default;
    attr.displayName = UA_LOCALIZEDTEXT_ALLOC("en-US", node->display_name);
    attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;

    UA_NodeId data_type = UA_NODEID_NULL;
    UA_StatusCode status = build_variant_from_text(
        &attr.value,
        &data_type,
        node->data_type,
        node->initial_value
    );
    if (status != UA_STATUSCODE_GOOD) {
        free(parent_path);
        UA_VariableAttributes_clear(&attr);
        return status;
    }
    attr.dataType = data_type;

    UA_NodeId requested = UA_NODEID_STRING_ALLOC(ns_idx, node->node_id);
    UA_NodeId parent = UA_NODEID_STRING_ALLOC(ns_idx, parent_path);
    UA_QualifiedName qn = UA_QUALIFIEDNAME_ALLOC(ns_idx, node->browse_name);

    status = UA_Server_addVariableNode(
        server,
        requested,
        parent,
        UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT),
        qn,
        UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE),
        attr,
        NULL,
        NULL
    );

    if (status == UA_STATUSCODE_GOOD) {
        status = write_node_value(
            server,
            ns_idx,
            node->node_id,
            node->data_type,
            node->initial_value
        );
    }

    UA_NodeId_clear(&requested);
    UA_NodeId_clear(&parent);
    UA_QualifiedName_clear(&qn);
    UA_VariableAttributes_clear(&attr);
    free(parent_path);

    return status;
}

/*
 * 根据变量的逻辑路径确保对象层级存在。
 * 这里默认根对象是 WindFarm，之后逐级创建 IED、LD、LN。
 */
static bool ensure_object_hierarchy(
    UA_Server *server,
    UA_UInt16 ns_idx,
    const char *variable_node_id,
    StringSetItem **created_objects
) {
    if (!string_set_contains(*created_objects, "WindFarm")) {
        UA_StatusCode status = add_object_node(
            server,
            ns_idx,
            "WindFarm",
            "WindFarm",
            "WindFarm",
            NULL,
            true,
            true
        );
        if (status != UA_STATUSCODE_GOOD) {
            fprintf(stderr, "Failed to add WindFarm object: 0x%08x\n", status);
            return false;
        }
        string_set_add(created_objects, "WindFarm");
    }

    char *parts[8] = {0};
    int count = split_node_id_parts(variable_node_id, parts, 8);
    if (count < 4) {
        fprintf(stderr, "Invalid logical node_id: %s\n", variable_node_id);
        free_parts(parts, count);
        return false;
    }

    char *ied = join_parts(parts, 1);
    char *ld = join_parts(parts, 2);
    char *ln = join_parts(parts, 3);

    if (ied == NULL || ld == NULL || ln == NULL) {
        free(ied);
        free(ld);
        free(ln);
        free_parts(parts, count);
        return false;
    }

    if (!string_set_contains(*created_objects, ied)) {
        UA_StatusCode status = add_object_node(
            server,
            ns_idx,
            ied,
            parts[0],
            parts[0],
            "WindFarm",
            false,
            false
        );
        if (status != UA_STATUSCODE_GOOD) {
            fprintf(stderr, "Failed to add IED object %s: 0x%08x\n", ied, status);
            free(ied);
            free(ld);
            free(ln);
            free_parts(parts, count);
            return false;
        }
        string_set_add(created_objects, ied);
    }

    if (!string_set_contains(*created_objects, ld)) {
        UA_StatusCode status = add_object_node(
            server,
            ns_idx,
            ld,
            parts[1],
            parts[1],
            ied,
            false,
            false
        );
        if (status != UA_STATUSCODE_GOOD) {
            fprintf(stderr, "Failed to add LD object %s: 0x%08x\n", ld, status);
            free(ied);
            free(ld);
            free(ln);
            free_parts(parts, count);
            return false;
        }
        string_set_add(created_objects, ld);
    }

    if (!string_set_contains(*created_objects, ln)) {
        UA_StatusCode status = add_object_node(
            server,
            ns_idx,
            ln,
            parts[2],
            parts[2],
            ld,
            false,
            false
        );
        if (status != UA_STATUSCODE_GOOD) {
            fprintf(stderr, "Failed to add LN object %s: 0x%08x\n", ln, status);
            free(ied);
            free(ld);
            free(ln);
            free_parts(parts, count);
            return false;
        }
        string_set_add(created_objects, ln);
    }

    free(ied);
    free(ld);
    free(ln);
    free_parts(parts, count);
    return true;
}

/* 先建对象层级，再建变量节点，完成整个测试地址空间。 */
static bool build_address_space(UA_Server *server, UA_UInt16 ns_idx, AppConfig *config) {
    StringSetItem *created_objects = NULL;

    for (NodeConfig *node = config->nodes; node != NULL; node = node->next) {
        if (!ensure_object_hierarchy(server, ns_idx, node->node_id, &created_objects)) {
            free_string_set(created_objects);
            return false;
        }
    }

    for (NodeConfig *node = config->nodes; node != NULL; node = node->next) {
        UA_StatusCode status = add_variable_node(server, ns_idx, node);
        if (status != UA_STATUSCODE_GOOD) {
            fprintf(stderr, "Failed to add variable %s: 0x%08x\n", node->node_id, status);
            free_string_set(created_objects);
            return false;
        }
    }

    free_string_set(created_objects);
    return true;
}

/* 把 stdin 设为非阻塞，避免影响服务端主循环节拍。 */
static int set_stdin_nonblocking(void) {
    int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
    if (flags == -1) {
        return -1;
    }

    return fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);
}

/* 检查 stdin 是否有命令待处理。 */
static bool stdin_has_data(void) {
    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(STDIN_FILENO, &read_fds);

    struct timeval timeout;
    timeout.tv_sec = 0;
    timeout.tv_usec = 0;

    int result = select(STDIN_FILENO + 1, &read_fds, NULL, NULL, &timeout);
    return result > 0 && FD_ISSET(STDIN_FILENO, &read_fds);
}

/* 处理外部 write 命令，允许测试驱动直接覆盖节点值。 */
static void process_write_command(
    UA_Server *server,
    UA_UInt16 ns_idx,
    char **fields,
    int field_count
) {
    if (field_count != 4) {
        fprintf(stderr, "Invalid write command: expected 4 fields, got %d\n", field_count);
        return;
    }

    const char *node_id = fields[1];
    const char *data_type = fields[2];
    const char *value = fields[3];

    if (
        strcmp(data_type, "Double") != 0 &&
        strcmp(data_type, "Int32") != 0 &&
        strcmp(data_type, "Boolean") != 0 &&
        strcmp(data_type, "String") != 0
    ) {
        fprintf(stderr, "Unsupported write data_type: %s\n", data_type);
        return;
    }

    (void)write_node_value(server, ns_idx, node_id, data_type, value);
}

/* 读取并执行所有已到达的 stdin 命令。 */
static void process_stdin_commands(UA_Server *server, UA_UInt16 ns_idx) {
    if (!stdin_has_data()) {
        return;
    }

    char line[MAX_LINE_LEN];

    while (fgets(line, sizeof(line), stdin) != NULL) {
        strip_newline(line);

        if (line[0] == '\0') {
            continue;
        }

        char *fields[8] = {0};
        int field_count = 0;
        split_fields(line, fields, 8, &field_count);

        if (field_count <= 0) {
            continue;
        }

        if (strcmp(fields[0], "write") == 0) {
            process_write_command(server, ns_idx, fields, field_count);
        } else {
            fprintf(stderr, "Unknown stdin command: %s\n", fields[0]);
        }
    }

    if (ferror(stdin)) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            clearerr(stdin);
        } else {
            perror("stdin read failed");
            clearerr(stdin);
        }
    }

    if (feof(stdin)) {
        clearerr(stdin);
    }
}

/* 单调纳秒时钟用于内部更新节拍控制。 */
static int64_t monotonic_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);

    return ((int64_t)ts.tv_sec * 1000000000LL) + (int64_t)ts.tv_nsec;
}

static void sleep_ns(int64_t delay_ns) {
    if (delay_ns <= 0) {
        return;
    }
    struct timespec ts;
    ts.tv_sec = (time_t)(delay_ns / 1000000000LL);
    ts.tv_nsec = (long)(delay_ns % 1000000000LL);
    nanosleep(&ts, NULL);
}

/* 根据节点数据类型生成下一次内部更新值。 */
static void build_internal_update_value(
    NodeConfig *node,
    char *buffer,
    size_t buffer_size
) {
    node->update_counter++;

    if (strcmp(node->data_type, "Double") == 0) {
        snprintf(buffer, buffer_size, "%.3f", (double)node->update_counter);
        return;
    }

    if (strcmp(node->data_type, "Int32") == 0) {
        snprintf(buffer, buffer_size, "%lu", node->update_counter % 100000UL);
        return;
    }

    if (strcmp(node->data_type, "Boolean") == 0) {
        snprintf(buffer, buffer_size, "%s", (node->update_counter % 2UL) == 0 ? "false" : "true");
        return;
    }

    if (strcmp(node->data_type, "String") == 0) {
        snprintf(buffer, buffer_size, "value_%lu", node->update_counter);
        return;
    }

    snprintf(buffer, buffer_size, "0");
}

/* 按配置决定是否执行一轮内部自动更新。 */
static void maybe_run_internal_update(
    UA_Server *server,
    UA_UInt16 ns_idx,
    AppConfig *config,
    int64_t *next_update_due_ns
) {
    if (!config->update_enabled) {
        return;
    }

    int64_t interval_ns = (int64_t)config->update_interval_ms * 1000000LL;
    if (interval_ns <= 0) {
        interval_ns = 1000000LL;
    }

    int64_t now_ns = monotonic_ns();
    if (*next_update_due_ns <= 0) {
        *next_update_due_ns = now_ns;
    }
    if (now_ns < *next_update_due_ns) {
        return;
    }

    int updated_count = 0;
    char value_buffer[256];

    for (NodeConfig *node = config->nodes; node != NULL; node = node->next) {
        build_internal_update_value(node, value_buffer, sizeof(value_buffer));
        (void)write_node_value(server, ns_idx, node->node_id, node->data_type, value_buffer);

        updated_count++;

        if (!config->update_all && updated_count >= 1) {
            break;
        }
    }

    *next_update_due_ns += interval_ns;
    while (*next_update_due_ns <= now_ns) {
        *next_update_due_ns += interval_ns;
    }
}

/* 进程入口：加载配置、启动服务端、循环处理外部命令和内部更新。 */
int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <config.tsv>\n", argv[0]);
        return EXIT_FAILURE;
    }

    int protocol_stdout_fd = dup(STDOUT_FILENO);
    if (protocol_stdout_fd < 0) {
        perror("Failed to duplicate stdout");
        return EXIT_FAILURE;
    }
    FILE *protocol_stdout = fdopen(protocol_stdout_fd, "w");
    if (protocol_stdout == NULL) {
        perror("Failed to open protocol stdout");
        close(protocol_stdout_fd);
        return EXIT_FAILURE;
    }
    if (dup2(STDERR_FILENO, STDOUT_FILENO) < 0) {
        perror("Failed to redirect stdout to stderr");
        fclose(protocol_stdout);
        return EXIT_FAILURE;
    }

    signal(SIGINT, stop_handler);
    signal(SIGTERM, stop_handler);

    AppConfig app_config = {0};

    if (!load_config(argv[1], &app_config)) {
        free_config(&app_config);
        return EXIT_FAILURE;
    }

    unsigned short port = parse_endpoint_port(app_config.endpoint);

    UA_Server *server = UA_Server_new();
    UA_ServerConfig *server_config = UA_Server_getConfig(server);
    disable_server_logging(server_config);

    UA_StatusCode status = UA_ServerConfig_setMinimal(server_config, port, NULL);
    if (status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "Failed to configure server: 0x%08x\n", status);
        UA_Server_delete(server);
        free_config(&app_config);
        return EXIT_FAILURE;
    }
#ifdef UA_ENABLE_SUBSCRIPTIONS
    /*
     * Subscribe capacity scans sweep 10Hz/20Hz/... sample rates. The simulator
     * must not clamp those requests back to a larger default minimum.
     */
    server_config->publishingIntervalLimits.min = 5.0;
    server_config->samplingIntervalLimits.min = 5.0;
#endif
    disable_server_logging(server_config);

    UA_UInt16 ns_idx = UA_Server_addNamespace(server, app_config.namespace_uri);

    if (!build_address_space(server, ns_idx, &app_config)) {
        UA_Server_delete(server);
        free_config(&app_config);
        return EXIT_FAILURE;
    }

    if (set_stdin_nonblocking() != 0) {
        perror("Failed to set stdin nonblocking");
    }

    status = UA_Server_run_startup(server);
    if (status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "Failed to start server: 0x%08x\n", status);
        UA_Server_delete(server);
        free_config(&app_config);
        return EXIT_FAILURE;
    }

    fprintf(protocol_stdout, "READY\n");
    fflush(protocol_stdout);

    int64_t next_update_due_ns = 0;

    while (running) {
        UA_Server_run_iterate(server, false);
        process_stdin_commands(server, ns_idx);
        maybe_run_internal_update(server, ns_idx, &app_config, &next_update_due_ns);

        int64_t sleep_budget_ns = 500000LL;
        if (app_config.update_enabled && next_update_due_ns > 0) {
            int64_t until_update_ns = next_update_due_ns - monotonic_ns();
            if (until_update_ns < sleep_budget_ns) {
                sleep_budget_ns = until_update_ns;
            }
        }
        sleep_ns(sleep_budget_ns);
    }

    status = UA_Server_run_shutdown(server);

    UA_Server_delete(server);
    free_config(&app_config);
    fclose(protocol_stdout);

    return status == UA_STATUSCODE_GOOD ? EXIT_SUCCESS : EXIT_FAILURE;
}
