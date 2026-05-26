#define _POSIX_C_SOURCE 199309L

#include <libiec61850/iec61850_client.h>
#include <libiec61850/iec61850_common.h>

#include <errno.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define MAX_LINE_LEN 8192
#define MAX_VALUE_TEXT_LEN 512

/* ── Forward declarations ─────────────────────────────────────────── */

static int64_t monotonic_now_ms(void);
static void millisleep(uint32_t ms);
static void sanitize_field(const char *input, char *output, size_t output_size);
static void format_mms_value(MmsValue *value, char *buf, size_t buf_size);
static void report_callback(void *parameter, ClientReport report);
static int run_subscription(const char *host, int port,
                            const char *ied_name, const char *rcb_name,
                            int duration_s);
static void print_version(void);

/* ── Global state ─────────────────────────────────────────────────── */

static volatile int g_running = 1;

/* ════════════════════════════════════════════════════════════════════ */

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
    if (output_size == 0) return;
    if (input == NULL || input[0] == '\0') {
        output[0] = '-';
        output[1] = '\0';
        return;
    }
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
    case MMS_OCTET_STRING:
        snprintf(buf, buf_size, "octets(%d)", MmsValue_getOctetStringSize(value));
        break;
    case MMS_ARRAY:
    case MMS_STRUCTURE:
        snprintf(buf, buf_size, "complex(%d)", (int)MmsValue_getArraySize(value));
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

static void report_callback(void *parameter, ClientReport report) {
    (void)parameter;

    MmsValue *values = ClientReport_getDataSetValues(report);
    uint32_t array_size = (values != NULL) ? MmsValue_getArraySize(values) : 0;

    const char *rcb_ref = ClientReport_getRcbReference(report);
    if (rcb_ref == NULL) rcb_ref = "-";
    char rcb_sanitized[256];
    sanitize_field(rcb_ref, rcb_sanitized, sizeof(rcb_sanitized));

    int64_t ts_ms = 0;
    if (ClientReport_hasTimestamp(report))
        ts_ms = (int64_t)ClientReport_getTimestamp(report);

    uint16_t seq_num = 0;
    if (ClientReport_hasSeqNum(report))
        seq_num = ClientReport_getSeqNum(report);

    /* Format: REPORT\t<rcb_ref>\t<timestamp_ms>\t<seq_num>\t<array_size>\t<v1>\t<v2>... */
    printf("REPORT\t%s\t%lld\t%u\t%u",
           rcb_sanitized,
           (long long)ts_ms,
           (unsigned int)seq_num,
           (unsigned int)array_size);

    /* Print each data set value */
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
}

/* ══════════════════════════════════════════════════════════════════ */

static int run_subscription(const char *host, int port,
                            const char *ied_name, const char *rcb_name,
                            int duration_s) {
    /* Build RCB object reference */
    char rcb_ref[512];
    if (strchr(rcb_name, '.') != NULL) {
        snprintf(rcb_ref, sizeof(rcb_ref), "%s", rcb_name);
    } else {
        snprintf(rcb_ref, sizeof(rcb_ref), "%s/LLN0.RP.%s", ied_name, rcb_name);
    }

    IedClientError error = IED_ERROR_OK;
    IedConnection con = IedConnection_create();
    if (con == NULL) {
        fprintf(stderr, "Failed to create IedConnection\n");
        return 1;
    }

    IedConnection_setConnectTimeout(con, 5000);
    IedConnection_setRequestTimeout(con, 5000);

    IedConnection_connect(con, &error, host, port);
    if (error != IED_ERROR_OK) {
        fprintf(stderr, "Connect failed: %s\n", IedClientError_toString(error));
        printf("ERROR\tconnect_failed:%s\n", IedClientError_toString(error));
        fflush(stdout);
        IedConnection_destroy(con);
        return 1;
    }

    /* Get RCB values */
    ClientReportControlBlock rcb = IedConnection_getRCBValues(con, &error, rcb_ref, NULL);
    if (error != IED_ERROR_OK || rcb == NULL) {
        fprintf(stderr, "Failed to read RCB values: %s\n", IedClientError_toString(error));
        printf("ERROR\tget_rcb_failed:%s\n", IedClientError_toString(error));
        fflush(stdout);
        IedConnection_close(con);
        IedConnection_destroy(con);
        return 1;
    }

    /* Install report handler */
    const char *rcb_rptid = ClientReportControlBlock_getRptId(rcb);
    IedConnection_installReportHandler(con, rcb_ref, rcb_rptid, report_callback, NULL);

    /* Reserve and enable report */
    ClientReportControlBlock_setResv(rcb, true);
    IedConnection_setRCBValues(con, &error, rcb, RCB_ELEMENT_RESV, true);
    if (error != IED_ERROR_OK) {
        fprintf(stderr, "Failed to reserve report: %s\n", IedClientError_toString(error));
        printf("ERROR\treserve_failed:%s\n", IedClientError_toString(error));
        fflush(stdout);
        ClientReportControlBlock_destroy(rcb);
        IedConnection_close(con);
        IedConnection_destroy(con);
        return 1;
    }

    ClientReportControlBlock_setRptEna(rcb, true);
    IedConnection_setRCBValues(con, &error, rcb, RCB_ELEMENT_RPT_ENA, true);
    if (error != IED_ERROR_OK) {
        fprintf(stderr, "Failed to enable report: %s\n", IedClientError_toString(error));
        printf("ERROR\tenable_failed:%s\n", IedClientError_toString(error));
        fflush(stdout);
        ClientReportControlBlock_destroy(rcb);
        IedConnection_close(con);
        IedConnection_destroy(con);
        return 1;
    }

    /* Signal ready — subscription is active */
    printf("READY\n");
    fflush(stdout);

    /* Main loop: check stdin for QUIT, respect duration limit */
    int64_t end_ms = (duration_s > 0)
        ? monotonic_now_ms() + (int64_t)duration_s * 1000LL
        : INT64_MAX;

    struct pollfd stdin_poll = { .fd = STDIN_FILENO, .events = POLLIN };
    char quit_buf[64];

    while (g_running && monotonic_now_ms() < end_ms) {
        int poll_rc = poll(&stdin_poll, 1, 100);  /* 100ms tick */
        if (poll_rc > 0 && (stdin_poll.revents & POLLIN)) {
            if (fgets(quit_buf, sizeof(quit_buf), stdin) != NULL) {
                if (strncmp(quit_buf, "QUIT", 4) == 0) {
                    fprintf(stderr, "Received QUIT, stopping report subscription\n");
                    break;
                }
            }
        }
    }

    /* Disable report */
    ClientReportControlBlock_setRptEna(rcb, false);
    IedConnection_setRCBValues(con, &error, rcb, RCB_ELEMENT_RPT_ENA, true);

    /* Uninstall handler */
    IedConnection_uninstallReportHandler(con, rcb_ref);

    ClientReportControlBlock_destroy(rcb);

    printf("STOPPED\n");
    fflush(stdout);

    IedConnection_close(con);
    IedConnection_destroy(con);
    return 0;
}

/* ══════════════════════════════════════════════════════════════════ */

static void print_version(void) {
    printf("iec61850_report_runner 1.0.0\n");
    printf("protocol: iec61850 report subscription via libiec61850\n");
    printf("stdout prefixes: READY, REPORT, ERROR, STOPPED\n");
}

int main(int argc, char **argv) {
    if (argc == 2 && (strcmp(argv[1], "--version") == 0 || strcmp(argv[1], "-v") == 0)) {
        print_version();
        return 0;
    }

    if (argc < 5 || argc > 6) {
        fprintf(stderr,
                "Usage: %s [--version|-v]\n"
                "   or: %s <host> <port> <ied_name> <rcb_ref> [duration_s]\n",
                argv[0], argv[0]);
        return 2;
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    const char *ied_name = argv[3];
    const char *rcb_ref = argv[4];
    int duration_s = (argc >= 6) ? atoi(argv[5]) : 0;

    if (port <= 0) {
        fprintf(stderr, "Invalid port: %s\n", argv[2]);
        return 2;
    }

    return run_subscription(host, port, ied_name, rcb_ref, duration_s);
}
