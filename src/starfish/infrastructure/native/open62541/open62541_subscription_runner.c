#define _POSIX_C_SOURCE 200809L

#include <open62541/client.h>
#include <open62541/client_config_default.h>
#include <open62541/client_subscriptions.h>

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_LINE_LEN 8192
#define MAX_FIELDS 16
#define REQUESTED_MAX_KEEPALIVE_COUNT 10U
#define RECONNECT_REASON_LEN 64

typedef struct SubscribeSessionConfig {
    int worker_index;
    double publishing_interval_ms;
    double sampling_interval_ms;
    double duration_s;
    double read_timeout_s;
    int endpoint_count;
    unsigned int queue_size;
    unsigned int startup_stagger_ms;
    unsigned int reconnect_stagger_ms;
    unsigned int monitored_item_batch_size;
    unsigned int monitored_item_batch_gap_ms;
} SubscribeSessionConfig;

typedef struct EndpointState EndpointState;

typedef struct MonitoredItemContext {
    EndpointState *endpoint;
    struct MonitoredItemContext *next;
} MonitoredItemContext;

struct EndpointState {
    int local_index;
    int global_index;
    char *endpoint_url;
    char *namespace_uri;
    char *node_file_path;
    UA_Client *client;
    UA_UInt16 namespace_index;
    UA_NodeId *node_ids;
    size_t node_count;
    UA_UInt32 subscription_id;
    bool active;

    size_t monitored_created;
    size_t monitored_failed;

    bool pending;
    size_t pending_value_count;
    size_t pending_bad_count;
    size_t pending_missing_ts_count;
    double pending_latest_timestamp_s;
    bool pending_has_timestamp;
    int64_t pending_latest_notify_ns;
    int64_t pending_first_notify_ns;

    int64_t local_notify_seq;
    int64_t notification_count;
    int64_t value_count;
    int64_t bad_count;
    int64_t missing_ts_count;
    int64_t reserved_sequence_gap_count;
    int64_t reserved_queue_overflow_count;
    int64_t keepalive_count;
    int64_t keepalive_miss_count;
    int64_t publish_timeout_count;
    int64_t reconnect_count;
    int64_t resubscribe_count;
    int64_t resubscribe_success_count;
    int64_t resubscribe_failure_count;
    bool unrecovered;
    char last_reconnect_reason[RECONNECT_REASON_LEN];
    double last_recovery_duration_ms;
    int64_t last_notify_ns;
    int64_t last_activity_ns;
    int64_t last_data_notify_ns;
    int64_t last_keepalive_ns;
    int64_t last_publish_ns;
    int64_t consecutive_keepalive_miss_count;
    int64_t next_iterate_due_ns;
    int64_t last_iterate_started_ns;
    int64_t run_iterate_count;
    int64_t max_dispatch_gap_ns;
    int64_t max_run_iterate_duration_ns;
    double revised_publishing_interval_ms;
    double revised_sampling_interval_ms;
    double max_data_age_ms;
    double max_publish_gap_ms;
    unsigned int startup_stagger_ms;
    unsigned int reconnect_stagger_ms;
    MonitoredItemContext *monitored_contexts;
};

typedef struct SubscribeSummary {
    int worker_index;
    int endpoint_count;
    int subscription_count;
    int monitored_expected;
    int monitored_created;
    int monitored_failed;
    int64_t notification_count;
    int64_t value_count;
    int64_t bad_count;
    int64_t missing_ts_count;
    int64_t reserved_sequence_gap_count;
    int64_t reserved_queue_overflow_count;
    int64_t keepalive_count;
    int64_t keepalive_miss_count;
    int64_t publish_timeout_count;
    int64_t reconnect_count;
    int64_t resubscribe_count;
    int64_t resubscribe_success_count;
    int64_t resubscribe_failure_count;
    int64_t unrecovered_endpoint_count;
    const char *last_reconnect_reason;
    double recovery_duration_ms;
    double max_data_age_ms;
    double max_publish_gap_ms;
} SubscribeSummary;

static void flush_endpoint_notify(int worker_index, EndpointState *endpoint);
static void run_endpoint_iterate(int worker_index, EndpointState *endpoint);
static bool recover_endpoint(
    const SubscribeSessionConfig *config,
    EndpointState *endpoint,
    const char *reason
);

static int64_t clamp_i64(int64_t value, int64_t minimum, int64_t maximum) {
    if(value < minimum) {
        return minimum;
    }
    if(value > maximum) {
        return maximum;
    }
    return value;
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

static double realtime_now_s(void) {
    struct timespec ts;
    if(clock_gettime(CLOCK_REALTIME, &ts) != 0) {
        return 0.0;
    }
    return (double)ts.tv_sec + (((double)ts.tv_nsec) / 1000000000.0);
}

static void sleep_ms(unsigned int delay_ms) {
    if(delay_ms == 0) {
        return;
    }
    struct timespec ts;
    ts.tv_sec = (time_t)(delay_ms / 1000U);
    ts.tv_nsec = (long)((delay_ms % 1000U) * 1000000U);
    nanosleep(&ts, NULL);
}

static void sleep_ns(int64_t delay_ns) {
    if(delay_ns <= 0) {
        return;
    }
    struct timespec ts;
    ts.tv_sec = (time_t)(delay_ns / 1000000000LL);
    ts.tv_nsec = (long)(delay_ns % 1000000000LL);
    nanosleep(&ts, NULL);
}

static double ua_datetime_to_unix_seconds(UA_DateTime value) {
    if(value <= 0) {
        return 0.0;
    }
    return ((double)(value - UA_DATETIME_UNIX_EPOCH)) / ((double)UA_DATETIME_SEC);
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
    size_t *node_count_out
) {
    FILE *fp = fopen(path, "r");
    if(fp == NULL) {
        return false;
    }

    size_t capacity = 16;
    size_t count = 0;
    UA_NodeId *node_ids = (UA_NodeId *)calloc(capacity, sizeof(UA_NodeId));
    if(node_ids == NULL) {
        fclose(fp);
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
                for(size_t i = 0; i < count; ++i) {
                    UA_NodeId_clear(&node_ids[i]);
                }
                free(node_ids);
                fclose(fp);
                return false;
            }
            node_ids = resized;
            memset(node_ids + capacity, 0, (next_capacity - capacity) * sizeof(UA_NodeId));
            capacity = next_capacity;
        }
        if(parse_or_build_node_id(line, namespace_index, &node_ids[count]) != UA_STATUSCODE_GOOD) {
            for(size_t i = 0; i < count; ++i) {
                UA_NodeId_clear(&node_ids[i]);
            }
            free(node_ids);
            fclose(fp);
            return false;
        }
        count++;
    }

    fclose(fp);
    *node_ids_out = node_ids;
    *node_count_out = count;
    return true;
}

static void subscription_status_callback(
    UA_Client *client,
    UA_UInt32 subId,
    void *subContext,
    UA_StatusChangeNotification *notification
) {
    (void)client;
    (void)subId;
    if(subContext == NULL || notification == NULL) {
        return;
    }

    EndpointState *endpoint = (EndpointState *)subContext;
    endpoint->last_activity_ns = monotonic_now_ns();
    if(notification->status != UA_STATUSCODE_GOOD) {
        endpoint->publish_timeout_count++;
        snprintf(
            endpoint->last_reconnect_reason,
            sizeof(endpoint->last_reconnect_reason),
            "status_change"
        );
        fprintf(
            stderr,
            "[source-lab] subscription status change global=%d status=0x%08x\n",
            endpoint->global_index,
            notification->status
        );
        fflush(stderr);
    }
}

static void subscription_delete_callback(
    UA_Client *client,
    UA_UInt32 subId,
    void *subContext
) {
    (void)client;
    (void)subId;
    (void)subContext;
}

static void unlink_monitored_context(
    EndpointState *endpoint,
    MonitoredItemContext *target
) {
    if(endpoint == NULL || target == NULL) {
        return;
    }

    MonitoredItemContext **cursor = &endpoint->monitored_contexts;
    while(*cursor != NULL) {
        if(*cursor == target) {
            *cursor = target->next;
            target->next = NULL;
            return;
        }
        cursor = &(*cursor)->next;
    }
}

static void free_monitored_context(
    EndpointState *endpoint,
    MonitoredItemContext *context
) {
    if(context == NULL) {
        return;
    }

    unlink_monitored_context(endpoint, context);
    context->endpoint = NULL;
    context->next = NULL;
    free(context);
}

static void free_monitored_contexts(EndpointState *endpoint) {
    if(endpoint == NULL) {
        return;
    }

    MonitoredItemContext *context = endpoint->monitored_contexts;
    endpoint->monitored_contexts = NULL;
    while(context != NULL) {
        MonitoredItemContext *next = context->next;
        context->endpoint = NULL;
        context->next = NULL;
        free(context);
        context = next;
    }
}

static void monitored_item_delete_callback(
    UA_Client *client,
    UA_UInt32 subId,
    void *subContext,
    UA_UInt32 monId,
    void *monContext
) {
    (void)client;
    (void)subId;
    (void)subContext;
    (void)monId;
    if(monContext == NULL) {
        return;
    }

    MonitoredItemContext *context = (MonitoredItemContext *)monContext;
    EndpointState *endpoint = context->endpoint;
    free_monitored_context(endpoint, context);
}

static void data_change_callback(
    UA_Client *client,
    UA_UInt32 subId,
    void *subContext,
    UA_UInt32 monId,
    void *monContext,
    UA_DataValue *value
) {
    (void)client;
    (void)subId;
    (void)subContext;
    (void)monId;
    if(monContext == NULL || value == NULL) {
        return;
    }

    MonitoredItemContext *context = (MonitoredItemContext *)monContext;
    EndpointState *endpoint = context->endpoint;
    if(endpoint == NULL) {
        return;
    }

    endpoint->pending = true;
    int64_t notify_ns = monotonic_now_ns();
    endpoint->last_activity_ns = notify_ns;
    endpoint->last_data_notify_ns = notify_ns;
    if(endpoint->pending_first_notify_ns <= 0 || notify_ns < endpoint->pending_first_notify_ns) {
        endpoint->pending_first_notify_ns = notify_ns;
    }
    if(notify_ns > endpoint->pending_latest_notify_ns) {
        endpoint->pending_latest_notify_ns = notify_ns;
    }
    if(value->hasValue && value->value.type != NULL) {
        endpoint->pending_value_count++;
    }

    if(!value->hasStatus || value->status == UA_STATUSCODE_GOOD) {
        /* no-op */
    } else {
        endpoint->pending_bad_count++;
    }

    if(value->hasSourceTimestamp) {
        double ts = ua_datetime_to_unix_seconds(value->sourceTimestamp);
        if(ts > 0.0 && (!endpoint->pending_has_timestamp || ts > endpoint->pending_latest_timestamp_s)) {
            endpoint->pending_latest_timestamp_s = ts;
            endpoint->pending_has_timestamp = true;
        }
    } else if(value->hasServerTimestamp) {
        double ts = ua_datetime_to_unix_seconds(value->serverTimestamp);
        if(ts > 0.0 && (!endpoint->pending_has_timestamp || ts > endpoint->pending_latest_timestamp_s)) {
            endpoint->pending_latest_timestamp_s = ts;
            endpoint->pending_has_timestamp = true;
        }
    } else {
        endpoint->pending_missing_ts_count++;
    }
}

static void begin_endpoint_iterate(EndpointState *endpoint) {
    endpoint->pending = false;
    endpoint->pending_value_count = 0;
    endpoint->pending_bad_count = 0;
    endpoint->pending_missing_ts_count = 0;
    endpoint->pending_latest_timestamp_s = 0.0;
    endpoint->pending_has_timestamp = false;
    endpoint->pending_latest_notify_ns = 0;
    endpoint->pending_first_notify_ns = 0;
}

static void reset_endpoint_measurement(EndpointState *endpoint) {
    begin_endpoint_iterate(endpoint);
    endpoint->local_notify_seq = 0;
    endpoint->notification_count = 0;
    endpoint->value_count = 0;
    endpoint->bad_count = 0;
    endpoint->missing_ts_count = 0;
    endpoint->reserved_sequence_gap_count = 0;
    endpoint->reserved_queue_overflow_count = 0;
    endpoint->keepalive_count = 0;
    endpoint->keepalive_miss_count = 0;
    endpoint->publish_timeout_count = 0;
    endpoint->reconnect_count = 0;
    endpoint->resubscribe_count = 0;
    endpoint->resubscribe_success_count = 0;
    endpoint->resubscribe_failure_count = 0;
    endpoint->unrecovered = false;
    endpoint->last_reconnect_reason[0] = '\0';
    endpoint->last_recovery_duration_ms = 0.0;
    endpoint->last_notify_ns = 0;
    endpoint->last_activity_ns = monotonic_now_ns();
    endpoint->last_data_notify_ns = 0;
    endpoint->last_keepalive_ns = 0;
    endpoint->last_publish_ns = 0;
    endpoint->consecutive_keepalive_miss_count = 0;
    endpoint->next_iterate_due_ns = 0;
    endpoint->last_iterate_started_ns = 0;
    endpoint->run_iterate_count = 0;
    endpoint->max_dispatch_gap_ns = 0;
    endpoint->max_run_iterate_duration_ns = 0;
    endpoint->max_data_age_ms = 0.0;
    endpoint->max_publish_gap_ms = 0.0;
}

static double endpoint_base_interval_ms(
    const SubscribeSessionConfig *config,
    const EndpointState *endpoint
) {
    double base_interval_ms = config->publishing_interval_ms;
    if(endpoint->revised_publishing_interval_ms > 0.0) {
        base_interval_ms = endpoint->revised_publishing_interval_ms;
    }
    if(endpoint->revised_sampling_interval_ms > base_interval_ms) {
        base_interval_ms = endpoint->revised_sampling_interval_ms;
    } else if(config->sampling_interval_ms > base_interval_ms) {
        base_interval_ms = config->sampling_interval_ms;
    }
    if(base_interval_ms <= 0.0) {
        base_interval_ms = 100.0;
    }
    return base_interval_ms;
}

static int64_t endpoint_inactivity_timeout_ns(
    const SubscribeSessionConfig *config,
    const EndpointState *endpoint
) {
    double timeout_ms = endpoint_base_interval_ms(config, endpoint) * (double)REQUESTED_MAX_KEEPALIVE_COUNT * 2.0;
    double read_timeout_ms = config->read_timeout_s * 1000.0;
    if(read_timeout_ms > timeout_ms) {
        timeout_ms = read_timeout_ms;
    }
    if(timeout_ms <= 0.0) {
        timeout_ms = 1000.0;
    }
    return (int64_t)(timeout_ms * 1000000.0);
}

static int64_t dispatch_interval_ns_for_config(const SubscribeSessionConfig *config) {
    double base_interval_ms = config->publishing_interval_ms;
    if(config->sampling_interval_ms > 0.0 && config->sampling_interval_ms < base_interval_ms) {
        base_interval_ms = config->sampling_interval_ms;
    }
    if(base_interval_ms <= 0.0) {
        base_interval_ms = 5.0;
    }
    return clamp_i64((int64_t)((base_interval_ms * 1000000.0) / 4.0), 1000000LL, 2000000LL);
}

static void run_due_endpoints_until(
    const SubscribeSessionConfig *config,
    EndpointState *endpoints,
    int64_t finished_ns
) {
    int64_t dispatch_interval_ns = dispatch_interval_ns_for_config(config);
    int next_index = 0;
    while(monotonic_now_ns() < finished_ns) {
        bool any_active = false;
        bool ran_due_endpoint = false;
        int64_t now_ns = monotonic_now_ns();
        int64_t nearest_due_ns = 0;

        for(int offset = 0; offset < config->endpoint_count; ++offset) {
            int index = (next_index + offset) % config->endpoint_count;
            EndpointState *endpoint = &endpoints[index];
            if(
                endpoint->client == NULL ||
                endpoint->subscription_id == 0U ||
                !endpoint->active ||
                endpoint->unrecovered
            ) {
                continue;
            }
            any_active = true;
            if(
                endpoint->last_activity_ns > 0 &&
                (now_ns - endpoint->last_activity_ns) > endpoint_inactivity_timeout_ns(config, endpoint)
            ) {
                endpoint->keepalive_miss_count++;
                endpoint->publish_timeout_count++;
                if(!recover_endpoint(config, endpoint, "publish_timeout")) {
                    now_ns = monotonic_now_ns();
                    continue;
                }
                now_ns = monotonic_now_ns();
            }
            if(endpoint->next_iterate_due_ns <= 0) {
                endpoint->next_iterate_due_ns = now_ns;
            }
            if(endpoint->next_iterate_due_ns > now_ns) {
                if(nearest_due_ns <= 0 || endpoint->next_iterate_due_ns < nearest_due_ns) {
                    nearest_due_ns = endpoint->next_iterate_due_ns;
                }
                continue;
            }

            run_endpoint_iterate(config->worker_index, endpoint);
            ran_due_endpoint = true;
            next_index = (index + 1) % config->endpoint_count;

            if(endpoint->next_iterate_due_ns <= 0) {
                endpoint->next_iterate_due_ns = endpoint->last_iterate_started_ns + dispatch_interval_ns;
            } else {
                endpoint->next_iterate_due_ns += dispatch_interval_ns;
            }
            if(endpoint->next_iterate_due_ns <= endpoint->last_iterate_started_ns) {
                endpoint->next_iterate_due_ns = endpoint->last_iterate_started_ns + dispatch_interval_ns;
            }

            now_ns = monotonic_now_ns();
        }
        if(!any_active) {
            sleep_ms(1U);
            continue;
        }
        if(ran_due_endpoint) {
            continue;
        }
        if(nearest_due_ns <= 0) {
            sleep_ns(dispatch_interval_ns);
            continue;
        }
        sleep_ns(clamp_i64(nearest_due_ns - monotonic_now_ns(), 0LL, dispatch_interval_ns));
    }
}

static void warmup_subscriptions(
    const SubscribeSessionConfig *config,
    EndpointState *endpoints
) {
    int64_t warmup_duration_ns = (int64_t)(config->publishing_interval_ms * 3.0 * 1000000.0);
    if(warmup_duration_ns <= 0) {
        warmup_duration_ns = 100000000LL;
    }
    run_due_endpoints_until(config, endpoints, monotonic_now_ns() + warmup_duration_ns);
    for(int i = 0; i < config->endpoint_count; ++i) {
        reset_endpoint_measurement(&endpoints[i]);
    }
}

static void free_endpoint(EndpointState *endpoint) {
    if(endpoint->client != NULL) {
        UA_Client_disconnect(endpoint->client);
        UA_Client_delete(endpoint->client);
        endpoint->client = NULL;
    }
    /*
     * The client normally frees monitored-item contexts through delete callbacks
     * during disconnect/delete. Any contexts still linked here are fallback
     * cleanup for failed create paths or library shutdown paths that skip the
     * callback.
     */
    free_monitored_contexts(endpoint);
    if(endpoint->node_ids != NULL) {
        for(size_t i = 0; i < endpoint->node_count; ++i) {
            UA_NodeId_clear(&endpoint->node_ids[i]);
        }
        free(endpoint->node_ids);
        endpoint->node_ids = NULL;
    }
    free(endpoint->endpoint_url);
    free(endpoint->namespace_uri);
    free(endpoint->node_file_path);
    endpoint->endpoint_url = NULL;
    endpoint->namespace_uri = NULL;
    endpoint->node_file_path = NULL;
}

static void clear_endpoint_runtime(EndpointState *endpoint) {
    if(endpoint->client != NULL) {
        UA_Client_disconnect(endpoint->client);
        UA_Client_delete(endpoint->client);
        endpoint->client = NULL;
    }
    free_monitored_contexts(endpoint);
    if(endpoint->node_ids != NULL) {
        for(size_t i = 0; i < endpoint->node_count; ++i) {
            UA_NodeId_clear(&endpoint->node_ids[i]);
        }
        free(endpoint->node_ids);
        endpoint->node_ids = NULL;
    }
    endpoint->node_count = 0U;
    endpoint->namespace_index = 0U;
    endpoint->subscription_id = 0U;
    endpoint->active = false;
    endpoint->monitored_created = 0U;
    endpoint->monitored_failed = 0U;
    endpoint->revised_publishing_interval_ms = 0.0;
    endpoint->revised_sampling_interval_ms = 0.0;
    begin_endpoint_iterate(endpoint);
    endpoint->last_activity_ns = monotonic_now_ns();
    endpoint->last_data_notify_ns = 0;
    endpoint->last_keepalive_ns = 0;
    endpoint->last_publish_ns = 0;
    endpoint->next_iterate_due_ns = 0;
}

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

static bool connect_endpoint(EndpointState *endpoint, double read_timeout_s) {
    endpoint->client = UA_Client_new();
    if(endpoint->client == NULL) {
        return false;
    }

    UA_ClientConfig *config = UA_Client_getConfig(endpoint->client);
    UA_ClientConfig_setDefault(config);
    disable_client_logging(config);
    config->timeout = (UA_UInt32)(read_timeout_s * 1000.0);
    config->requestedSessionTimeout = (UA_UInt32)(read_timeout_s * 2000.0);

    if(UA_Client_connect(endpoint->client, endpoint->endpoint_url) != UA_STATUSCODE_GOOD) {
        return false;
    }

    endpoint->namespace_index = 0;
    if(endpoint->namespace_uri != NULL && strcmp(endpoint->namespace_uri, "-") != 0) {
        if(
            UA_Client_getNamespaceIndex(
                endpoint->client,
                UA_STRING((char *)(uintptr_t)endpoint->namespace_uri),
                &endpoint->namespace_index
            ) != UA_STATUSCODE_GOOD
        ) {
            return false;
        }
    }

    if(!load_plan_nodes(endpoint->node_file_path, endpoint->namespace_index, &endpoint->node_ids, &endpoint->node_count)) {
        return false;
    }
    return true;
}

static bool create_subscription_for_endpoint(
    EndpointState *endpoint,
    const SubscribeSessionConfig *config
) {
    UA_CreateSubscriptionRequest request = UA_CreateSubscriptionRequest_default();
    request.requestedPublishingInterval = config->publishing_interval_ms;
    request.requestedMaxKeepAliveCount = REQUESTED_MAX_KEEPALIVE_COUNT;

    UA_CreateSubscriptionResponse response = UA_Client_Subscriptions_create(
        endpoint->client,
        request,
        endpoint,
        subscription_status_callback,
        subscription_delete_callback
    );
    if(response.responseHeader.serviceResult != UA_STATUSCODE_GOOD) {
        endpoint->monitored_failed = endpoint->node_count;
        UA_CreateSubscriptionResponse_clear(&response);
        return false;
    }

    endpoint->subscription_id = response.subscriptionId;
    endpoint->revised_publishing_interval_ms = response.revisedPublishingInterval;
    endpoint->last_activity_ns = monotonic_now_ns();
    UA_CreateSubscriptionResponse_clear(&response);

    unsigned int batch_size = config->monitored_item_batch_size;
    if(batch_size == 0U) {
        batch_size = 1U;
    }

    for(size_t start = 0; start < endpoint->node_count; start += batch_size) {
        size_t current_batch = batch_size;
        if(start + current_batch > endpoint->node_count) {
            current_batch = endpoint->node_count - start;
        }
        size_t valid_count = 0;

        UA_CreateMonitoredItemsRequest request;
        UA_CreateMonitoredItemsRequest_init(&request);
        request.subscriptionId = endpoint->subscription_id;
        request.timestampsToReturn = UA_TIMESTAMPSTORETURN_BOTH;
        request.itemsToCreate = (UA_MonitoredItemCreateRequest *)calloc(
            current_batch,
            sizeof(UA_MonitoredItemCreateRequest)
        );
        void **contexts = (void **)calloc(current_batch, sizeof(void *));
        UA_Client_DataChangeNotificationCallback *callbacks =
            (UA_Client_DataChangeNotificationCallback *)calloc(current_batch, sizeof(*callbacks));
        UA_Client_DeleteMonitoredItemCallback *delete_callbacks =
            (UA_Client_DeleteMonitoredItemCallback *)calloc(current_batch, sizeof(*delete_callbacks));
        if(
            request.itemsToCreate == NULL ||
            contexts == NULL ||
            callbacks == NULL ||
            delete_callbacks == NULL
        ) {
            free(request.itemsToCreate);
            free(contexts);
            free(callbacks);
            free(delete_callbacks);
            endpoint->monitored_failed += current_batch;
            continue;
        }

        for(size_t i = 0; i < current_batch; ++i) {
            size_t node_index = start + i;
            MonitoredItemContext *context = NULL;
            UA_MonitoredItemCreateRequest item = UA_MonitoredItemCreateRequest_default(UA_NODEID_NULL);
            if(
                UA_NodeId_copy(
                    &endpoint->node_ids[node_index],
                    &item.itemToMonitor.nodeId
                ) != UA_STATUSCODE_GOOD
            ) {
                endpoint->monitored_failed++;
                continue;
            }
            context = (MonitoredItemContext *)calloc(1, sizeof(MonitoredItemContext));
            if(context == NULL) {
                UA_MonitoredItemCreateRequest_clear(&item);
                endpoint->monitored_failed++;
                continue;
            }
            item.requestedParameters.samplingInterval = config->sampling_interval_ms;
            item.requestedParameters.queueSize = config->queue_size;
            context->endpoint = endpoint;
            context->next = endpoint->monitored_contexts;
            endpoint->monitored_contexts = context;

            request.itemsToCreate[valid_count] = item;
            contexts[valid_count] = context;
            callbacks[valid_count] = data_change_callback;
            delete_callbacks[valid_count] = monitored_item_delete_callback;
            valid_count++;
        }

        request.itemsToCreateSize = valid_count;
        if(valid_count == 0U) {
            free(request.itemsToCreate);
            free(contexts);
            free(callbacks);
            free(delete_callbacks);
            continue;
        }

        UA_CreateMonitoredItemsResponse response = UA_Client_MonitoredItems_createDataChanges(
            endpoint->client,
            request,
            contexts,
            callbacks,
            delete_callbacks
        );
        if(response.responseHeader.serviceResult != UA_STATUSCODE_GOOD) {
            endpoint->monitored_failed += valid_count;
            for(size_t i = 0; i < valid_count; ++i) {
                free_monitored_context(endpoint, (MonitoredItemContext *)contexts[i]);
            }
        } else {
            for(size_t i = 0; i < valid_count; ++i) {
                bool created = (
                    i < response.resultsSize &&
                    response.results[i].statusCode == UA_STATUSCODE_GOOD
                );
                if(created) {
                    endpoint->monitored_created++;
                    if(response.results[i].revisedSamplingInterval > endpoint->revised_sampling_interval_ms) {
                        endpoint->revised_sampling_interval_ms = response.results[i].revisedSamplingInterval;
                    }
                } else {
                    endpoint->monitored_failed++;
                    free_monitored_context(endpoint, (MonitoredItemContext *)contexts[i]);
                }
            }
        }

        UA_CreateMonitoredItemsResponse_clear(&response);
        UA_CreateMonitoredItemsRequest_clear(&request);
        free(contexts);
        free(callbacks);
        free(delete_callbacks);

        if(config->monitored_item_batch_gap_ms > 0U && (start + current_batch) < endpoint->node_count) {
            sleep_ms(config->monitored_item_batch_gap_ms);
        }
    }

    endpoint->active = endpoint->monitored_created > 0;
    return endpoint->active;
}

static void flush_endpoint_notify(int worker_index, EndpointState *endpoint) {
    if(!endpoint->pending) {
        return;
    }

    int64_t flush_ns = monotonic_now_ns();
    double recv_ts_s = realtime_now_s();
    int64_t notify_ns = endpoint->pending_first_notify_ns > 0 ? endpoint->pending_first_notify_ns : flush_ns;
    double notify_ts_s = notify_ns > 0 ? ((double)notify_ns / 1000000000.0) : 0.0;
    double flush_ts_s = flush_ns > 0 ? ((double)flush_ns / 1000000000.0) : 0.0;
    double publish_gap_ms = 0.0;
    if(endpoint->last_notify_ns > 0) {
        publish_gap_ms = ((double)(notify_ns - endpoint->last_notify_ns)) / 1000000.0;
        if(publish_gap_ms > endpoint->max_publish_gap_ms) {
            endpoint->max_publish_gap_ms = publish_gap_ms;
        }
    }
    endpoint->last_notify_ns = notify_ns;
    endpoint->last_publish_ns = notify_ns;

    endpoint->local_notify_seq++;
    endpoint->notification_count++;
    endpoint->value_count += (int64_t)endpoint->pending_value_count;
    endpoint->bad_count += (int64_t)endpoint->pending_bad_count;
    endpoint->missing_ts_count += (int64_t)endpoint->pending_missing_ts_count;

    double publish_ts_s = endpoint->pending_has_timestamp ? endpoint->pending_latest_timestamp_s : 0.0;
    double data_age_ms = -1.0;
    if(endpoint->pending_has_timestamp) {
        data_age_ms = (recv_ts_s - endpoint->pending_latest_timestamp_s) * 1000.0;
        if(data_age_ms > endpoint->max_data_age_ms) {
            endpoint->max_data_age_ms = data_age_ms;
        }
    }

    printf(
        "NOTIFY\t%d\t%d\t%d\t%u\t%zu\t%zu\t%zu\t%zu\t%lld\t%.6f\t%.6f\t%.6f\t%.6f\t%.3f\n",
        worker_index,
        endpoint->local_index,
        endpoint->global_index,
        endpoint->subscription_id,
        endpoint->monitored_created,
        endpoint->pending_value_count,
        endpoint->pending_bad_count,
        endpoint->pending_missing_ts_count,
        (long long)endpoint->local_notify_seq,
        publish_ts_s,
        notify_ts_s,
        flush_ts_s,
        recv_ts_s,
        data_age_ms
    );
    fflush(stdout);

    endpoint->pending = false;
    endpoint->pending_value_count = 0;
    endpoint->pending_bad_count = 0;
    endpoint->pending_missing_ts_count = 0;
    endpoint->pending_latest_timestamp_s = 0.0;
    endpoint->pending_has_timestamp = false;
    endpoint->pending_latest_notify_ns = 0;
    endpoint->pending_first_notify_ns = 0;
}

static bool recover_endpoint(
    const SubscribeSessionConfig *config,
    EndpointState *endpoint,
    const char *reason
) {
    int64_t recovery_started_ns = monotonic_now_ns();
    unsigned int stagger_ms = endpoint->reconnect_stagger_ms;

    endpoint->resubscribe_count++;
    endpoint->consecutive_keepalive_miss_count++;
    endpoint->unrecovered = false;
    snprintf(endpoint->last_reconnect_reason, sizeof(endpoint->last_reconnect_reason), "%s", reason);

    if(stagger_ms > 0U) {
        sleep_ms(stagger_ms);
    }

    clear_endpoint_runtime(endpoint);
    endpoint->reconnect_count++;
    if(!connect_endpoint(endpoint, config->read_timeout_s) || !create_subscription_for_endpoint(endpoint, config)) {
        clear_endpoint_runtime(endpoint);
        endpoint->resubscribe_failure_count++;
        endpoint->unrecovered = true;
        endpoint->last_recovery_duration_ms =
            ((double)(monotonic_now_ns() - recovery_started_ns)) / 1000000.0;
        fprintf(
            stderr,
            "[source-lab] endpoint recovery failed global=%d reason=%s duration_ms=%.3f\n",
            endpoint->global_index,
            endpoint->last_reconnect_reason,
            endpoint->last_recovery_duration_ms
        );
        fflush(stderr);
        return false;
    }

    endpoint->resubscribe_success_count++;
    endpoint->consecutive_keepalive_miss_count = 0;
    endpoint->last_recovery_duration_ms =
        ((double)(monotonic_now_ns() - recovery_started_ns)) / 1000000.0;
    endpoint->last_activity_ns = monotonic_now_ns();
    endpoint->next_iterate_due_ns = endpoint->last_activity_ns;
    fprintf(
        stderr,
        "[source-lab] endpoint recovered global=%d reason=%s duration_ms=%.3f\n",
        endpoint->global_index,
        endpoint->last_reconnect_reason,
        endpoint->last_recovery_duration_ms
    );
    fflush(stderr);
    return true;
}

static void run_endpoint_iterate(int worker_index, EndpointState *endpoint) {
    int64_t iterate_started_ns = monotonic_now_ns();
    if(endpoint->last_iterate_started_ns > 0) {
        int64_t dispatch_gap_ns = iterate_started_ns - endpoint->last_iterate_started_ns;
        if(dispatch_gap_ns > endpoint->max_dispatch_gap_ns) {
            endpoint->max_dispatch_gap_ns = dispatch_gap_ns;
        }
    }
    endpoint->last_iterate_started_ns = iterate_started_ns;
    endpoint->run_iterate_count++;

    begin_endpoint_iterate(endpoint);
    UA_Client_run_iterate(endpoint->client, 0);

    int64_t iterate_finished_ns = monotonic_now_ns();
    int64_t iterate_duration_ns = iterate_finished_ns - iterate_started_ns;
    if(iterate_duration_ns > endpoint->max_run_iterate_duration_ns) {
        endpoint->max_run_iterate_duration_ns = iterate_duration_ns;
    }
    flush_endpoint_notify(worker_index, endpoint);
}

static SubscribeSummary run_subscription_session(
    const SubscribeSessionConfig *config,
    EndpointState *endpoints
) {
    SubscribeSummary summary;
    memset(&summary, 0, sizeof(summary));
    summary.worker_index = config->worker_index;
    summary.endpoint_count = config->endpoint_count;
    summary.last_reconnect_reason = "-";

    for(int i = 0; i < config->endpoint_count; ++i) {
        EndpointState *endpoint = &endpoints[i];
        endpoint->startup_stagger_ms = config->startup_stagger_ms * (unsigned int)i;
        endpoint->reconnect_stagger_ms = config->reconnect_stagger_ms * (unsigned int)i;
        if(!connect_endpoint(endpoint, config->read_timeout_s)) {
            endpoint->monitored_failed = endpoint->node_count;
            endpoint->unrecovered = true;
            snprintf(endpoint->last_reconnect_reason, sizeof(endpoint->last_reconnect_reason), "startup_connect");
            summary.monitored_expected += (int)endpoint->node_count;
            summary.monitored_failed += (int)endpoint->node_count;
            if(config->startup_stagger_ms > 0U) {
                sleep_ms(config->startup_stagger_ms);
            }
            continue;
        }
        summary.monitored_expected += (int)endpoint->node_count;
        if(create_subscription_for_endpoint(endpoint, config)) {
            summary.subscription_count++;
        } else {
            endpoint->unrecovered = true;
            snprintf(endpoint->last_reconnect_reason, sizeof(endpoint->last_reconnect_reason), "startup_subscribe");
        }
        summary.monitored_created += (int)endpoint->monitored_created;
        summary.monitored_failed += (int)endpoint->monitored_failed;
        if(config->startup_stagger_ms > 0U) {
            sleep_ms(config->startup_stagger_ms);
        }
    }

    warmup_subscriptions(config, endpoints);

    int64_t started_ns = monotonic_now_ns();
    int64_t finished_ns = started_ns + (int64_t)(config->duration_s * 1000000000.0);
    run_due_endpoints_until(config, endpoints, finished_ns);

    for(int i = 0; i < config->endpoint_count; ++i) {
        EndpointState *endpoint = &endpoints[i];
        if(endpoint->client != NULL && endpoint->subscription_id != 0U) {
            run_endpoint_iterate(config->worker_index, endpoint);
        }
        summary.notification_count += endpoint->notification_count;
        summary.value_count += endpoint->value_count;
        summary.bad_count += endpoint->bad_count;
        summary.missing_ts_count += endpoint->missing_ts_count;
        summary.reserved_sequence_gap_count += endpoint->reserved_sequence_gap_count;
        summary.reserved_queue_overflow_count += endpoint->reserved_queue_overflow_count;
        summary.keepalive_count += endpoint->keepalive_count;
        summary.keepalive_miss_count += endpoint->keepalive_miss_count;
        summary.publish_timeout_count += endpoint->publish_timeout_count;
        summary.reconnect_count += endpoint->reconnect_count;
        summary.resubscribe_count += endpoint->resubscribe_count;
        summary.resubscribe_success_count += endpoint->resubscribe_success_count;
        summary.resubscribe_failure_count += endpoint->resubscribe_failure_count;
        if(endpoint->unrecovered) {
            summary.unrecovered_endpoint_count++;
        }
        if(endpoint->last_recovery_duration_ms > summary.recovery_duration_ms) {
            summary.recovery_duration_ms = endpoint->last_recovery_duration_ms;
            summary.last_reconnect_reason =
                endpoint->last_reconnect_reason[0] == '\0' ? "-" : endpoint->last_reconnect_reason;
        }
        if(endpoint->max_data_age_ms > summary.max_data_age_ms) {
            summary.max_data_age_ms = endpoint->max_data_age_ms;
        }
        if(endpoint->max_publish_gap_ms > summary.max_publish_gap_ms) {
            summary.max_publish_gap_ms = endpoint->max_publish_gap_ms;
        }
        printf(
            "SUB_ENDPOINT_DIAG\t%d\t%d\t%d\t%lld\t%lld\t%.3f\t%.3f\t%.3f\t%.3f\n",
            config->worker_index,
            endpoint->local_index,
            endpoint->global_index,
            (long long)endpoint->notification_count,
            (long long)endpoint->run_iterate_count,
            ((double)endpoint->max_dispatch_gap_ns) / 1000000.0,
            ((double)endpoint->max_run_iterate_duration_ns) / 1000000.0,
            endpoint->revised_publishing_interval_ms,
            endpoint->revised_sampling_interval_ms
        );
    }
    if(summary.unrecovered_endpoint_count > 0 && strcmp(summary.last_reconnect_reason, "-") == 0) {
        for(int i = 0; i < config->endpoint_count; ++i) {
            if(endpoints[i].unrecovered && endpoints[i].last_reconnect_reason[0] != '\0') {
                summary.last_reconnect_reason = endpoints[i].last_reconnect_reason;
                break;
            }
        }
    }

    printf(
        "SUB_SUMMARY\t%d\t%d\t%d\t%d\t%d\t%d\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%lld\t%s\t%.3f\t%.3f\t%.3f\n",
        summary.worker_index,
        summary.endpoint_count,
        summary.subscription_count,
        summary.monitored_expected,
        summary.monitored_created,
        summary.monitored_failed,
        (long long)summary.notification_count,
        (long long)summary.value_count,
        (long long)summary.bad_count,
        (long long)summary.missing_ts_count,
        (long long)summary.reserved_sequence_gap_count,
        (long long)summary.reserved_queue_overflow_count,
        (long long)summary.keepalive_count,
        (long long)summary.keepalive_miss_count,
        (long long)summary.publish_timeout_count,
        (long long)summary.reconnect_count,
        (long long)summary.resubscribe_count,
        (long long)summary.resubscribe_success_count,
        (long long)summary.resubscribe_failure_count,
        (long long)summary.unrecovered_endpoint_count,
        summary.last_reconnect_reason,
        summary.recovery_duration_ms,
        summary.max_data_age_ms,
        summary.max_publish_gap_ms
    );
    printf("SUB_DONE\t%d\n", summary.worker_index);
    fflush(stdout);
    return summary;
}

static bool parse_start_subscribe(char **fields, int count, SubscribeSessionConfig *config) {
    if(count != 11) {
        return false;
    }
    config->worker_index = atoi(fields[1]);
    config->publishing_interval_ms = atof(fields[2]);
    config->sampling_interval_ms = atof(fields[3]);
    config->duration_s = atof(fields[4]);
    config->read_timeout_s = atof(fields[5]);
    config->endpoint_count = atoi(fields[6]);
    config->queue_size = (unsigned int)strtoul(fields[7], NULL, 10);
    config->startup_stagger_ms = (unsigned int)strtoul(fields[8], NULL, 10);
    config->reconnect_stagger_ms = config->startup_stagger_ms;
    config->monitored_item_batch_size = (unsigned int)strtoul(fields[9], NULL, 10);
    config->monitored_item_batch_gap_ms = (unsigned int)strtoul(fields[10], NULL, 10);
    return config->endpoint_count >= 0;
}

static bool parse_endpoint_line(
    EndpointState *endpoint,
    int local_index,
    char **fields,
    int count
) {
    if(count != 7) {
        return false;
    }
    memset(endpoint, 0, sizeof(*endpoint));
    endpoint->local_index = local_index;
    endpoint->global_index = atoi(fields[1]);
    endpoint->endpoint_url = xstrdup(fields[2]);
    endpoint->namespace_uri = xstrdup(fields[3]);
    endpoint->node_file_path = xstrdup(fields[6]);
    endpoint->startup_stagger_ms = 0U;
    endpoint->reconnect_stagger_ms = 0U;
    endpoint->last_reconnect_reason[0] = '\0';
    return endpoint->endpoint_url != NULL && endpoint->namespace_uri != NULL && endpoint->node_file_path != NULL;
}

int main(void) {
    char line[MAX_LINE_LEN];
    char *fields[MAX_FIELDS];
    bool running = true;

    printf("READY\n");
    fflush(stdout);

    while(running && fgets(line, sizeof(line), stdin) != NULL) {
        strip_newline(line);
        if(line[0] == '\0') {
            continue;
        }
        int field_count = split_fields(line, fields, MAX_FIELDS);
        if(field_count <= 0) {
            continue;
        }

        if(strcmp(fields[0], "QUIT") == 0) {
            break;
        }
        if(strcmp(fields[0], "STOP_SUBSCRIBE") == 0) {
            continue;
        }
        if(strcmp(fields[0], "START_SUBSCRIBE") != 0) {
            printf("ERROR\tunexpected_command\t%s\n", fields[0]);
            fflush(stdout);
            continue;
        }

        SubscribeSessionConfig config;
        memset(&config, 0, sizeof(config));
        if(!parse_start_subscribe(fields, field_count, &config)) {
            printf("ERROR\tinvalid_start_subscribe\n");
            fflush(stdout);
            continue;
        }

        EndpointState *endpoints = (EndpointState *)calloc((size_t)config.endpoint_count, sizeof(EndpointState));
        if(endpoints == NULL) {
            printf("ERROR\talloc_endpoints_failed\n");
            fflush(stdout);
            continue;
        }

        bool input_error = false;
        int local_index = 0;
        while(fgets(line, sizeof(line), stdin) != NULL) {
            strip_newline(line);
            int endpoint_field_count = split_fields(line, fields, MAX_FIELDS);
            if(endpoint_field_count <= 0) {
                continue;
            }
            if(strcmp(fields[0], "END_SUBSCRIBE") == 0) {
                break;
            }
            if(strcmp(fields[0], "ENDPOINT") != 0 || local_index >= config.endpoint_count) {
                input_error = true;
                break;
            }
            if(!parse_endpoint_line(&endpoints[local_index], local_index, fields, endpoint_field_count)) {
                input_error = true;
                break;
            }
            local_index++;
        }

        if(input_error || local_index != config.endpoint_count) {
            printf("ERROR\tinvalid_endpoint_block\n");
            fflush(stdout);
            for(int i = 0; i < config.endpoint_count; ++i) {
                free_endpoint(&endpoints[i]);
            }
            free(endpoints);
            continue;
        }

        (void)run_subscription_session(&config, endpoints);
        for(int i = 0; i < config.endpoint_count; ++i) {
            free_endpoint(&endpoints[i]);
        }
        free(endpoints);
        return 0;
    }

    return 0;
}
