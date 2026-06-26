#define _POSIX_C_SOURCE 199309L

#include <libiec61850/goose_receiver.h>
#include <libiec61850/goose_subscriber.h>
#include <libiec61850/iec61850_common.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ── Forward declarations ─────────────────────────────────────────── */

static int64_t monotonic_now_us(void);
static int64_t monotonic_now_ms(void);
static void millisleep(uint32_t ms);
static void sanitize_field(const char *input, char *output, size_t output_size);
static void format_mms_value(MmsValue *value, char *buf, size_t buf_size);
static void goose_listener(GooseSubscriber subscriber, void *parameter);

/* ── Global counters ──────────────────────────────────────────────── */

static volatile int g_msg_count = 0;
static volatile int g_msg_errors = 0;

/* ════════════════════════════════════════════════════════════════════ */

static int64_t monotonic_now_us(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return ((int64_t)ts.tv_sec * 1000000LL) + ((int64_t)ts.tv_nsec / 1000LL);
}

static int64_t monotonic_now_ms(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return ((int64_t)ts.tv_sec * 1000LL) + ((int64_t)ts.tv_nsec / 1000000LL);
}

static void millisleep(uint32_t ms) {
    struct timespec req;
    req.tv_sec = ms / 1000;
    req.tv_nsec = (long)(ms % 1000) * 1000000L;
    struct timespec rem;
    while (nanosleep(&req, &rem) != 0 && errno == EINTR) {
        req = rem;
    }
}

static void sanitize_field(const char *input, char *output, size_t output_size) {
    size_t i, j = 0;
    for (i = 0; input[i] != '\0' && j + 1 < output_size; i++) {
        char ch = input[i];
        if (ch == '\t' || ch == '\n' || ch == '\r') ch = ' ';
        output[j++] = ch;
    }
    output[j] = '\0';
}

static void format_mms_value(MmsValue *value, char *buf, size_t buf_size) {
    if (value == NULL) { snprintf(buf, buf_size, "-"); return; }
    MmsType t = MmsValue_getType(value);
    switch (t) {
    case MMS_BOOLEAN:
        snprintf(buf, buf_size, "%s", MmsValue_getBoolean(value) ? "true" : "false");
        break;
    case MMS_INTEGER:
    case MMS_UNSIGNED:
        snprintf(buf, buf_size, "%lld", (long long)MmsValue_toInt64(value));
        break;
    case MMS_FLOAT:
        snprintf(buf, buf_size, "%.9g", MmsValue_toDouble(value));
        break;
    case MMS_VISIBLE_STRING:
    case MMS_STRING: {
        const char *s = MmsValue_toString(value);
        snprintf(buf, buf_size, "%s", s ? s : "-");
        break;
    }
    case MMS_UTC_TIME:
        snprintf(buf, buf_size, "%llu", (unsigned long long)MmsValue_getUtcTimeInMs(value));
        break;
    case MMS_BIT_STRING:
        snprintf(buf, buf_size, "0x%x", MmsValue_getBitStringAsInteger(value));
        break;
    default: {
        char tmp[128];
        MmsValue_printToBuffer((MmsValue *)value, tmp, sizeof(tmp));
        sanitize_field(tmp, buf, buf_size);
        break;
    }
    }
}

/* ══════════════════════════════════════════════════════════════════ */

static void goose_listener(GooseSubscriber subscriber, void *parameter) {
    (void)parameter;

    /* Extract metadata */
    char *go_id = GooseSubscriber_getGoId(subscriber);
    char *gocb_ref = GooseSubscriber_getGoCbRef(subscriber);
    char *dataset = GooseSubscriber_getDataSet(subscriber);
    uint32_t stnum = GooseSubscriber_getStNum(subscriber);
    uint32_t sqnum = GooseSubscriber_getSqNum(subscriber);
    uint64_t ts = GooseSubscriber_getTimestamp(subscriber);
    uint32_t app_id = (uint32_t)GooseSubscriber_getAppId(subscriber);
    bool valid = GooseSubscriber_isValid(subscriber);

    /* Data set values */
    MmsValue *values = GooseSubscriber_getDataSetValues(subscriber);
    uint32_t array_size = (values != NULL) ? MmsValue_getArraySize(values) : 0;

    char go_id_buf[128] = "-";
    char gocb_ref_buf[256] = "-";
    char dataset_buf[256] = "-";
    if (go_id) sanitize_field(go_id, go_id_buf, sizeof(go_id_buf));
    if (gocb_ref) sanitize_field(gocb_ref, gocb_ref_buf, sizeof(gocb_ref_buf));
    if (dataset) sanitize_field(dataset, dataset_buf, sizeof(dataset_buf));

    printf("NOTIFY\t%u\t%s\t%s\t%s\t%u\t%u\t%llu\t%d\t%u",
           app_id,
           go_id_buf,
           gocb_ref_buf,
           dataset_buf,
           stnum,
           sqnum,
           (unsigned long long)ts,
           valid ? 1 : 0,
           array_size);

    /* Print each value */
    if (values != NULL) {
        for (uint32_t i = 0; i < array_size; i++) {
            MmsValue *elem = MmsValue_getElement(values, (int)i);
            char elem_buf[256];
            format_mms_value(elem, elem_buf, sizeof(elem_buf));
            printf("\t%s", elem_buf);
        }
    }
    printf("\n");
    fflush(stdout);

    g_msg_count++;

    /* Check parse error */
    GooseParseError pe = GooseSubscriber_getParseError(subscriber);
    if (pe != GOOSE_PARSE_ERROR_NO_ERROR) {
        g_msg_errors++;
    }
}

/* ══════════════════════════════════════════════════════════════════ */

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <interface> <app_id> <duration_s>\n", argv[0]);
        return 2;
    }

    const char *interface_id = argv[1];
    uint16_t app_id = (uint16_t)atoi(argv[2]);
    int duration_s = atoi(argv[3]);

    if (duration_s <= 0) {
        fprintf(stderr, "Invalid duration\n");
        return 2;
    }

    /* Create receiver */
    GooseReceiver receiver = GooseReceiver_create();
    if (receiver == NULL) {
        fprintf(stderr, "Failed to create GooseReceiver\n");
        return 1;
    }

    GooseReceiver_setInterfaceId(receiver, interface_id);

    /* Create subscriber in observer mode to listen to any source */
    GooseSubscriber subscriber = GooseSubscriber_create(NULL, NULL);
    if (subscriber == NULL) {
        fprintf(stderr, "Failed to create GooseSubscriber\n");
        GooseReceiver_destroy(receiver);
        return 1;
    }

    GooseSubscriber_setObserver(subscriber);
    GooseSubscriber_setAppId(subscriber, app_id);
    GooseSubscriber_setListener(subscriber, goose_listener, NULL);

    GooseReceiver_addSubscriber(receiver, subscriber);

    GooseReceiver_start(receiver);

    /* Check if running */
    if (!GooseReceiver_isRunning(receiver)) {
        fprintf(stderr, "GooseReceiver failed to start\n");
        GooseReceiver_destroy(receiver);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    /* Wait for duration */
    int64_t end_ms = monotonic_now_ms() + (int64_t)duration_s * 1000LL;
    while (monotonic_now_ms() < end_ms) {
        millisleep(100);
    }

    /* Stop and cleanup */
    GooseReceiver_stop(receiver);
    GooseReceiver_destroy(receiver); /* also destroys subscriber */

    printf("STREAM_SUMMARY\t%d\t%d\n", g_msg_count, g_msg_errors);
    fflush(stdout);

    printf("DONE\n");
    fflush(stdout);

    return 0;
}
