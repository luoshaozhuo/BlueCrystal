#define _POSIX_C_SOURCE 200809L

#include <open62541/client.h>
#include <open62541/client_config_default.h>

#include <errno.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_LINE_LEN 8192
#define MAX_VALUE_TEXT_LEN 512
#define MAX_STATUS_TEXT_LEN 64

typedef struct ReadValueSnapshot {
    bool has_value;
    double source_timestamp_s;
    double server_timestamp_s;
    char status_code[MAX_STATUS_TEXT_LEN];
    char value_text[MAX_VALUE_TEXT_LEN];
} ReadValueSnapshot;

typedef struct ReadExecutionResult {
    bool success;
    size_t value_count;
    double response_timestamp_s;
    const char *detail;
    int64_t read_start_ts_ns;
    int64_t read_end_ts_ns;
    ReadValueSnapshot *values;
    size_t results_size;
} ReadExecutionResult;

typedef struct SerialEndpointPlan {
    int local_index;
    int global_index;
    char *endpoint_url;
    char *namespace_uri;
    char *node_file_path;
    int64_t offset_ns;
    UA_Client *client;
    UA_UInt16 namespace_index;
    UA_NodeId *node_ids;
    size_t node_count;
    int64_t next_due_ns;
    int64_t tick_index;
    int64_t missed_ticks;
} SerialEndpointPlan;

static UA_Logger g_null_logger = {0};

static void disable_client_logging(UA_ClientConfig *config) {
    if(config == NULL) {
        return;
    }
    config->logging = &g_null_logger;
    if(config->eventLoop != NULL) {
        config->eventLoop->logger = &g_null_logger;
    }
}

static char *xstrdup(const char *value) {
    size_t len = strlen(value);
    char *copy = (char *)malloc(len + 1);
    if(copy == NULL) {
        return NULL;
    }
    memcpy(copy, value, len + 1);
    return copy;
}

static void strip_newline(char *line) {
    size_t len = strlen(line);
    while(len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r')) {
        line[len - 1] = '\0';
        len--;
    }
}

static int split_fields(char *line, char **fields, int max_fields) {
    int count = 0;
    char *cursor = line;
    while(cursor != NULL && count < max_fields) {
        fields[count++] = cursor;
        char *tab = strchr(cursor, '\t');
        if(tab == NULL) {
            break;
        }
        *tab = '\0';
        cursor = tab + 1;
    }
    return count;
}

static int64_t monotonic_now_ns(void) {
    struct timespec ts;
    if(clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return ((int64_t)ts.tv_sec * 1000000000LL) + (int64_t)ts.tv_nsec;
}

static double ua_datetime_to_unix_seconds(UA_DateTime value) {
    if(value <= 0) {
        return 0.0;
    }
    return ((double)(value - UA_DATETIME_UNIX_EPOCH)) / ((double)UA_DATETIME_SEC);
}

static void sanitize_protocol_field(
    const char *input,
    char *output,
    size_t output_size
) {
    if(output_size == 0) {
        return;
    }
    if(input == NULL || input[0] == '\0') {
        snprintf(output, output_size, "-");
        return;
    }

    size_t write_index = 0;
    for(size_t read_index = 0; input[read_index] != '\0' && write_index + 1 < output_size; ++read_index) {
        char ch = input[read_index];
        if(ch == '\t' || ch == '\n' || ch == '\r') {
            ch = ' ';
        }
        output[write_index++] = ch;
    }
    output[write_index] = '\0';
}

static bool serialize_variant_value(
    const UA_Variant *variant,
    char *buffer,
    size_t buffer_size
) {
    if(buffer_size == 0) {
        return false;
    }
    if(variant == NULL || !variant->data || variant->type == NULL) {
        snprintf(buffer, buffer_size, "-");
        return false;
    }
    if(!UA_Variant_isScalar(variant)) {
        snprintf(buffer, buffer_size, "[unsupported_array]");
        return false;
    }

    const UA_DataType *type = variant->type;
    if(type == &UA_TYPES[UA_TYPES_BOOLEAN]) {
        snprintf(buffer, buffer_size, "%s", (*(UA_Boolean *)variant->data) ? "true" : "false");
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_SBYTE]) {
        snprintf(buffer, buffer_size, "%d", (int)(*(UA_SByte *)variant->data));
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_BYTE]) {
        snprintf(buffer, buffer_size, "%u", (unsigned int)(*(UA_Byte *)variant->data));
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_INT16]) {
        snprintf(buffer, buffer_size, "%d", (int)(*(UA_Int16 *)variant->data));
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_UINT16]) {
        snprintf(buffer, buffer_size, "%u", (unsigned int)(*(UA_UInt16 *)variant->data));
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_INT32]) {
        snprintf(buffer, buffer_size, "%d", *(UA_Int32 *)variant->data);
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_UINT32]) {
        snprintf(buffer, buffer_size, "%u", *(UA_UInt32 *)variant->data);
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_INT64]) {
        snprintf(buffer, buffer_size, "%lld", (long long)(*(UA_Int64 *)variant->data));
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_UINT64]) {
        snprintf(buffer, buffer_size, "%llu", (unsigned long long)(*(UA_UInt64 *)variant->data));
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_FLOAT]) {
        snprintf(buffer, buffer_size, "%.9g", (double)(*(UA_Float *)variant->data));
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_DOUBLE]) {
        snprintf(buffer, buffer_size, "%.17g", *(UA_Double *)variant->data);
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_STRING]) {
        UA_String *value = (UA_String *)variant->data;
        size_t copy_len = value->length < (buffer_size - 1) ? value->length : (buffer_size - 1);
        memcpy(buffer, value->data, copy_len);
        buffer[copy_len] = '\0';
        sanitize_protocol_field(buffer, buffer, buffer_size);
        return true;
    }
    if(type == &UA_TYPES[UA_TYPES_DATETIME]) {
        snprintf(
            buffer,
            buffer_size,
            "%.6f",
            ua_datetime_to_unix_seconds(*(UA_DateTime *)variant->data)
        );
        return true;
    }

    sanitize_protocol_field(type->typeName, buffer, buffer_size);
    return false;
}

static void snapshot_data_value(
    const UA_DataValue *value,
    ReadValueSnapshot *snapshot
) {
    memset(snapshot, 0, sizeof(*snapshot));
    sanitize_protocol_field(
        value->hasStatus ? UA_StatusCode_name(value->status) : "GOOD",
        snapshot->status_code,
        sizeof(snapshot->status_code)
    );
    snapshot->source_timestamp_s = value->hasSourceTimestamp
        ? ua_datetime_to_unix_seconds(value->sourceTimestamp)
        : 0.0;
    snapshot->server_timestamp_s = value->hasServerTimestamp
        ? ua_datetime_to_unix_seconds(value->serverTimestamp)
        : 0.0;
    snapshot->has_value = value->hasValue && value->value.type != NULL;
    if(!snapshot->has_value) {
        snprintf(snapshot->value_text, sizeof(snapshot->value_text), "-");
        return;
    }
    serialize_variant_value(&value->value, snapshot->value_text, sizeof(snapshot->value_text));
}

static UA_StatusCode parse_or_build_node_id(
    const char *text,
    UA_UInt16 namespace_index,
    UA_NodeId *node_id
) {
    UA_NodeId_init(node_id);
    if(
        strncmp(text, "ns=", 3) == 0 ||
        strncmp(text, "nsu=", 4) == 0 ||
        strncmp(text, "s=", 2) == 0 ||
        strncmp(text, "i=", 2) == 0 ||
        strncmp(text, "g=", 2) == 0 ||
        strncmp(text, "b=", 2) == 0
    ) {
        return UA_NodeId_parse(node_id, UA_STRING((char *)(uintptr_t)text));
    }
    *node_id = UA_NODEID_STRING_ALLOC(namespace_index, text);
    return UA_NodeId_isNull(node_id) ? UA_STATUSCODE_BADOUTOFMEMORY : UA_STATUSCODE_GOOD;
}

static bool load_plan_nodes(
    const char *path,
    UA_UInt16 namespace_index,
    UA_NodeId **node_ids_out,
    size_t *node_count_out,
    char *error,
    size_t error_size
) {
    FILE *fp = fopen(path, "r");
    if(fp == NULL) {
        snprintf(error, error_size, "failed to open node file: %s", path);
        return false;
    }

    size_t capacity = 16;
    size_t count = 0;
    UA_NodeId *node_ids = (UA_NodeId *)calloc(capacity, sizeof(UA_NodeId));
    if(node_ids == NULL) {
        fclose(fp);
        snprintf(error, error_size, "failed to allocate node id array");
        return false;
    }

    char line[MAX_LINE_LEN];
    while(fgets(line, sizeof(line), fp) != NULL) {
        strip_newline(line);
        if(line[0] == '\0') {
            continue;
        }
        if(count == capacity) {
            size_t next_capacity = capacity * 2;
            UA_NodeId *resized = (UA_NodeId *)realloc(node_ids, next_capacity * sizeof(UA_NodeId));
            if(resized == NULL) {
                snprintf(error, error_size, "failed to resize node id array");
                goto fail;
            }
            node_ids = resized;
            memset(node_ids + capacity, 0, (next_capacity - capacity) * sizeof(UA_NodeId));
            capacity = next_capacity;
        }
        UA_StatusCode status = parse_or_build_node_id(line, namespace_index, &node_ids[count]);
        if(status != UA_STATUSCODE_GOOD) {
            snprintf(error, error_size, "failed to parse node id %s: %s", line, UA_StatusCode_name(status));
            goto fail;
        }
        count++;
    }

    fclose(fp);
    *node_ids_out = node_ids;
    *node_count_out = count;
    return true;

fail:
    fclose(fp);
    for(size_t i = 0; i < count; ++i) {
        UA_NodeId_clear(&node_ids[i]);
    }
    free(node_ids);
    return false;
}

static bool execute_read_node_ids(
    UA_Client *client,
    UA_NodeId *node_ids,
    size_t node_count,
    ReadExecutionResult *result
) {
    UA_ReadValueId *nodes_to_read = (UA_ReadValueId *)calloc(node_count, sizeof(UA_ReadValueId));
    if(nodes_to_read == NULL) {
        result->success = false;
        result->value_count = 0;
        result->response_timestamp_s = 0.0;
        result->detail = "alloc_failed";
        result->read_start_ts_ns = 0;
        result->read_end_ts_ns = 0;
        result->values = NULL;
        result->results_size = 0;
        return false;
    }

    for(size_t i = 0; i < node_count; ++i) {
        UA_ReadValueId_init(&nodes_to_read[i]);
        if(UA_NodeId_copy(&node_ids[i], &nodes_to_read[i].nodeId) != UA_STATUSCODE_GOOD) {
            for(size_t j = 0; j <= i; ++j) {
                UA_ReadValueId_clear(&nodes_to_read[j]);
            }
            free(nodes_to_read);
            result->success = false;
            result->value_count = 0;
            result->response_timestamp_s = 0.0;
            result->detail = "nodeid_copy_failed";
            result->read_start_ts_ns = 0;
            result->read_end_ts_ns = 0;
            result->values = NULL;
            result->results_size = 0;
            return false;
        }
        nodes_to_read[i].attributeId = UA_ATTRIBUTEID_VALUE;
    }

    UA_ReadRequest request;
    UA_ReadRequest_init(&request);
    request.nodesToRead = nodes_to_read;
    request.nodesToReadSize = node_count;
    request.timestampsToReturn = UA_TIMESTAMPSTORETURN_BOTH;

    int64_t read_start_ts_ns = monotonic_now_ns();
    UA_ReadResponse response = UA_Client_Service_read(client, request);
    int64_t read_end_ts_ns = monotonic_now_ns();
    ReadValueSnapshot *snapshots = NULL;

    bool success = response.responseHeader.serviceResult == UA_STATUSCODE_GOOD;
    size_t value_count = 0;
    if(success) {
        snapshots = (ReadValueSnapshot *)calloc(response.resultsSize, sizeof(ReadValueSnapshot));
        if(snapshots == NULL && response.resultsSize > 0) {
            success = false;
            result->detail = "alloc_failed";
        }
        for(size_t i = 0; i < response.resultsSize; ++i) {
            const UA_DataValue *value = &response.results[i];
            if(snapshots != NULL) {
                snapshot_data_value(value, &snapshots[i]);
            }
            if(value->hasValue && value->value.type != NULL) {
                value_count++;
            }
        }
    }

    result->success = success;
    result->value_count = success ? value_count : 0;
    result->response_timestamp_s = ua_datetime_to_unix_seconds(response.responseHeader.timestamp);
    result->detail = success
        ? (result->detail != NULL ? result->detail : "-")
        : (result->detail != NULL ? result->detail : UA_StatusCode_name(response.responseHeader.serviceResult));
    result->read_start_ts_ns = read_start_ts_ns;
    result->read_end_ts_ns = read_end_ts_ns;
    result->values = success ? snapshots : NULL;
    result->results_size = success ? response.resultsSize : 0;

    UA_ReadResponse_clear(&response);
    UA_ReadRequest_clear(&request);
    if(!success && snapshots != NULL) {
        free(snapshots);
    }
    return success;
}

static void free_serial_endpoint(SerialEndpointPlan *endpoint) {
    if(endpoint->client != NULL) {
        UA_Client_disconnect(endpoint->client);
        UA_Client_delete(endpoint->client);
    }
    if(endpoint->node_ids != NULL) {
        for(size_t i = 0; i < endpoint->node_count; ++i) {
            UA_NodeId_clear(&endpoint->node_ids[i]);
        }
        free(endpoint->node_ids);
    }
    free(endpoint->endpoint_url);
    free(endpoint->namespace_uri);
    free(endpoint->node_file_path);
}

static bool serial_connect_endpoint(
    SerialEndpointPlan *endpoint,
    double read_timeout_s,
    char *error,
    size_t error_size
) {
    endpoint->client = UA_Client_new();
    if(endpoint->client == NULL) {
        snprintf(error, error_size, "failed to create client");
        return false;
    }

    UA_ClientConfig *config = UA_Client_getConfig(endpoint->client);
    UA_ClientConfig_setDefault(config);
    disable_client_logging(config);
    config->timeout = (UA_UInt32)(read_timeout_s * 1000.0);
    config->requestedSessionTimeout = (UA_UInt32)(read_timeout_s * 2000.0);

    UA_StatusCode connect_status = UA_Client_connect(endpoint->client, endpoint->endpoint_url);
    if(connect_status != UA_STATUSCODE_GOOD) {
        snprintf(error, error_size, "connect failed: %s", UA_StatusCode_name(connect_status));
        return false;
    }

    endpoint->namespace_index = 0;
    if(endpoint->namespace_uri != NULL && strcmp(endpoint->namespace_uri, "-") != 0) {
        UA_StatusCode ns_status = UA_Client_getNamespaceIndex(
            endpoint->client,
            UA_STRING((char *)(uintptr_t)endpoint->namespace_uri),
            &endpoint->namespace_index
        );
        if(ns_status != UA_STATUSCODE_GOOD) {
            snprintf(error, error_size, "namespace lookup failed: %s", UA_StatusCode_name(ns_status));
            return false;
        }
    }

    return load_plan_nodes(
        endpoint->node_file_path,
        endpoint->namespace_index,
        &endpoint->node_ids,
        &endpoint->node_count,
        error,
        error_size
    );
}

static bool read_serial_endpoint(
    SerialEndpointPlan *endpoint,
    int worker_index,
    int64_t scheduled_ns,
    int64_t measure_started_ns,
    int64_t measure_ended_ns,
    int64_t *total_reads,
    int64_t *ok_reads,
    int64_t *bad_reads,
    int64_t *read_errors,
    int64_t *missing_response_timestamps,
    int64_t *warmup_reads,
    int64_t *warmup_errors,
    double *warmup_max_lag_ms,
    double *warmup_max_read_ms,
    double *max_lag_ms,
    double *max_read_ms
) {
    ReadExecutionResult result;
    memset(&result, 0, sizeof(result));
    execute_read_node_ids(endpoint->client, endpoint->node_ids, endpoint->node_count, &result);
    bool in_measurement = scheduled_ns >= measure_started_ns && scheduled_ns < measure_ended_ns;
    const char *error_code = "OK";
    if(!result.success) {
        error_code = result.detail;
        if(in_measurement) {
            (*read_errors)++;
        } else {
            (*warmup_errors)++;
        }
    } else if(result.value_count != endpoint->node_count) {
        error_code = "batch_mismatch";
        if(in_measurement) {
            (*bad_reads)++;
        }
    } else if(result.response_timestamp_s <= 0.0) {
        error_code = "missing_response_timestamp";
        if(in_measurement) {
            (*bad_reads)++;
            (*missing_response_timestamps)++;
        }
    } else {
        if(in_measurement) {
            (*ok_reads)++;
        }
    }

    double lag_ms = ((double)(result.read_start_ts_ns - scheduled_ns)) / 1000000.0;
    double read_ms = ((double)(result.read_end_ts_ns - result.read_start_ts_ns)) / 1000000.0;
    if(in_measurement) {
        if(lag_ms > *max_lag_ms) {
            *max_lag_ms = lag_ms;
        }
        if(read_ms > *max_read_ms) {
            *max_read_ms = read_ms;
        }
    } else {
        if(lag_ms > *warmup_max_lag_ms) {
            *warmup_max_lag_ms = lag_ms;
        }
        if(read_ms > *warmup_max_read_ms) {
            *warmup_max_read_ms = read_ms;
        }
    }

    if(in_measurement) {
        printf(
            "RESULT\t%d\t%d\t%d\t%lld\t%lld\t%lld\t%lld\t%s\t%.3f\t%.3f\t%zu\t%.6f\n",
            worker_index,
            endpoint->local_index,
            endpoint->global_index,
            (long long)endpoint->tick_index,
            (long long)scheduled_ns,
            (long long)result.read_start_ts_ns,
            (long long)result.read_end_ts_ns,
            error_code,
            lag_ms,
            read_ms,
            result.value_count,
            result.response_timestamp_s > 0.0 ? result.response_timestamp_s : -1.0
        );
        if(result.success) {
            for(size_t i = 0; i < result.results_size; ++i) {
                const ReadValueSnapshot *snapshot = &result.values[i];
                printf(
                    "VALUE\t%d\t%d\t%d\t%zu\t%s\t%s\t%.6f\t%.6f\n",
                    worker_index,
                    endpoint->local_index,
                    endpoint->global_index,
                    i,
                    snapshot->status_code,
                    snapshot->value_text,
                    snapshot->source_timestamp_s > 0.0 ? snapshot->source_timestamp_s : -1.0,
                    snapshot->server_timestamp_s > 0.0 ? snapshot->server_timestamp_s : -1.0
                );
            }
        }
        fflush(stdout);
        (*total_reads)++;
    } else {
        (*warmup_reads)++;
    }

    if(result.values != NULL) {
        free(result.values);
    }
    endpoint->tick_index++;
    return true;
}

static bool maybe_consume_stop_command(bool *stop_requested, bool *quit_requested) {
    struct pollfd poll_fd = {.fd = 0, .events = POLLIN, .revents = 0};
    int poll_result = poll(&poll_fd, 1, 0);
    if(poll_result <= 0 || (poll_fd.revents & POLLIN) == 0) {
        return true;
    }

    char line[MAX_LINE_LEN];
    if(fgets(line, sizeof(line), stdin) == NULL) {
        *quit_requested = true;
        return false;
    }
    strip_newline(line);
    if(strcmp(line, "STOP_POLL") == 0) {
        *stop_requested = true;
        return true;
    }
    if(strcmp(line, "QUIT") == 0) {
        *quit_requested = true;
        return false;
    }
    return true;
}

static int run_serial_loop(void) {
    printf("READY\n");
    fflush(stdout);

    char line[MAX_LINE_LEN];
    while(fgets(line, sizeof(line), stdin) != NULL) {
        strip_newline(line);
        if(line[0] == '\0') {
            continue;
        }
        if(strcmp(line, "QUIT") == 0) {
            return 0;
        }

        char *fields[8] = {0};
        int field_count = split_fields(line, fields, 8);
        if(field_count != 8 || strcmp(fields[0], "START_SERIAL_POLL") != 0) {
            printf("ERROR\tserial\tinvalid_start_serial_poll\n");
            fflush(stdout);
            continue;
        }

        int worker_index = atoi(fields[1]);
        int64_t period_ns = strtoll(fields[3], NULL, 10);
        double warmup_s = strtod(fields[4], NULL);
        double duration_s = strtod(fields[5], NULL);
        double read_timeout_s = strtod(fields[6], NULL);
        int endpoint_count = atoi(fields[7]);
        if(period_ns <= 0 || duration_s <= 0.0 || warmup_s < 0.0 || read_timeout_s <= 0.0 || endpoint_count <= 0) {
            printf("ERROR\tserial\tinvalid_serial_poll_parameters\n");
            fflush(stdout);
            continue;
        }

        SerialEndpointPlan *endpoints =
            (SerialEndpointPlan *)calloc((size_t)endpoint_count, sizeof(SerialEndpointPlan));
        if(endpoints == NULL) {
            printf("ERROR\tserial\talloc_failed\n");
            fflush(stdout);
            continue;
        }

        bool config_ok = true;
        for(int i = 0; i < endpoint_count; ++i) {
            if(fgets(line, sizeof(line), stdin) == NULL) {
                config_ok = false;
                break;
            }
            strip_newline(line);
            char *endpoint_fields[8] = {0};
            int endpoint_field_count = split_fields(line, endpoint_fields, 8);
            if(endpoint_field_count != 8 || strcmp(endpoint_fields[0], "ENDPOINT") != 0) {
                config_ok = false;
                break;
            }
            endpoints[i].local_index = i;
            endpoints[i].global_index = atoi(endpoint_fields[1]);
            endpoints[i].endpoint_url = xstrdup(endpoint_fields[2]);
            endpoints[i].namespace_uri = xstrdup(endpoint_fields[3]);
            endpoints[i].node_file_path = xstrdup(endpoint_fields[6]);
            endpoints[i].offset_ns = strtoll(endpoint_fields[7], NULL, 10);
        }
        if(config_ok) {
            if(fgets(line, sizeof(line), stdin) == NULL) {
                config_ok = false;
            } else {
                strip_newline(line);
                config_ok = strcmp(line, "END_SERIAL_POLL") == 0;
            }
        }
        if(!config_ok) {
            printf("ERROR\tserial\tinvalid_endpoint_plan\n");
            fflush(stdout);
            for(int i = 0; i < endpoint_count; ++i) {
                free_serial_endpoint(&endpoints[i]);
            }
            free(endpoints);
            continue;
        }

        char error[512] = {0};
        bool connect_ok = true;
        for(int i = 0; i < endpoint_count; ++i) {
            if(!serial_connect_endpoint(&endpoints[i], read_timeout_s, error, sizeof(error))) {
                connect_ok = false;
                break;
            }
        }
        if(!connect_ok) {
            printf("ERROR\tserial\t%s\n", error);
            fflush(stdout);
            for(int i = 0; i < endpoint_count; ++i) {
                free_serial_endpoint(&endpoints[i]);
            }
            free(endpoints);
            continue;
        }

        int64_t start_ns = monotonic_now_ns() + 1000000LL;
        int64_t measure_started_ns = start_ns + (int64_t)(warmup_s * 1000000000.0);
        int64_t end_ns = measure_started_ns + (int64_t)(duration_s * 1000000000.0);
        for(int i = 0; i < endpoint_count; ++i) {
            endpoints[i].next_due_ns = start_ns + endpoints[i].offset_ns;
            endpoints[i].tick_index = 0;
            endpoints[i].missed_ticks = 0;
        }

        int64_t total_reads = 0;
        int64_t ok_reads = 0;
        int64_t bad_reads = 0;
        int64_t read_errors = 0;
        int64_t missing_response_timestamps = 0;
        int64_t warmup_reads = 0;
        int64_t warmup_errors = 0;
        int64_t missed_ticks = 0;
        double warmup_max_lag_ms = 0.0;
        double warmup_max_read_ms = 0.0;
        double max_lag_ms = 0.0;
        double max_read_ms = 0.0;
        bool stop_requested = false;
        bool quit_requested = false;

        while(!stop_requested && !quit_requested) {
            int64_t next_due_ns = 0;
            for(int i = 0; i < endpoint_count; ++i) {
                if(endpoints[i].next_due_ns >= end_ns) {
                    continue;
                }
                if(next_due_ns == 0 || endpoints[i].next_due_ns < next_due_ns) {
                    next_due_ns = endpoints[i].next_due_ns;
                }
            }
            if(next_due_ns == 0) {
                break;
            }

            if(maybe_consume_stop_command(&stop_requested, &quit_requested) == false) {
                break;
            }

            struct timespec sleep_ts = {
                .tv_sec = (time_t)(next_due_ns / 1000000000LL),
                .tv_nsec = (long)(next_due_ns % 1000000000LL),
            };
            int sleep_rc = 0;
            do {
                sleep_rc = clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &sleep_ts, NULL);
            } while(sleep_rc == EINTR);
            if(sleep_rc != 0) {
                printf("ERROR\tserial\tclock_nanosleep_failed\n");
                fflush(stdout);
                break;
            }

            int64_t now_ns = monotonic_now_ns();
            for(int i = 0; i < endpoint_count; ++i) {
                if(endpoints[i].next_due_ns < end_ns && endpoints[i].next_due_ns <= now_ns) {
                    int64_t scheduled_ns = endpoints[i].next_due_ns;
                    read_serial_endpoint(
                        &endpoints[i],
                        worker_index,
                        scheduled_ns,
                        measure_started_ns,
                        end_ns,
                        &total_reads,
                        &ok_reads,
                        &bad_reads,
                        &read_errors,
                        &missing_response_timestamps,
                        &warmup_reads,
                        &warmup_errors,
                        &warmup_max_lag_ms,
                        &warmup_max_read_ms,
                        &max_lag_ms,
                        &max_read_ms
                    );
                    endpoints[i].next_due_ns += period_ns;
                    while(endpoints[i].next_due_ns < end_ns && endpoints[i].next_due_ns <= now_ns) {
                        endpoints[i].next_due_ns += period_ns;
                        endpoints[i].missed_ticks++;
                        missed_ticks++;
                    }
                }
            }
        }

        printf(
            "RUNNER_SUMMARY\t%d\t%d\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%.3f\t%.3f\t%lld\t%lld\t%.3f\t%.3f\n",
            worker_index,
            endpoint_count,
            (long long)total_reads,
            (long long)ok_reads,
            (long long)bad_reads,
            (long long)read_errors,
            (long long)missing_response_timestamps,
            (long long)missed_ticks,
            max_lag_ms,
            max_read_ms,
            (long long)warmup_reads,
            (long long)warmup_errors,
            warmup_max_lag_ms,
            warmup_max_read_ms
        );
        printf("POLL_DONE\t%d\n", worker_index);
        fflush(stdout);

        for(int i = 0; i < endpoint_count; ++i) {
            free_serial_endpoint(&endpoints[i]);
        }
        free(endpoints);
        if(quit_requested) {
            return 0;
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if(argc != 1) {
        fprintf(stderr, "usage: %s\n", argv[0]);
        return 2;
    }
    return run_serial_loop();
}
