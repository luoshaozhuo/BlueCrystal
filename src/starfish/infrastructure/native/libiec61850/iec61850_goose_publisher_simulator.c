#define _POSIX_C_SOURCE 199309L

#include <libiec61850/goose_publisher.h>
#include <libiec61850/iec61850_common.h>
#include <libiec61850/linked_list.h>
#include <libiec61850/mms_value.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ── Forward declarations ─────────────────────────────────────────── */

static int64_t monotonic_now_ms(void);
static void millisleep(uint32_t ms);

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

/* ══════════════════════════════════════════════════════════════════ */

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <interface> <app_id> <interval_ms>\n", argv[0]);
        return 2;
    }

    const char *interface_id = argv[1];
    uint16_t app_id = (uint16_t)atoi(argv[2]);
    int interval_ms = atoi(argv[3]);

    if (interval_ms <= 0) {
        fprintf(stderr, "Invalid interval\n");
        return 2;
    }

    /* ── Communication parameters ────────────────────────────────── */
    CommParameters params;
    memset(&params, 0, sizeof(params));
    params.vlanPriority = 4;
    params.vlanId = 0;
    params.appId = app_id;
    /* Default multicast MAC: 01-0C-CD-01-00-00 + appId low byte */
    params.dstAddress[0] = 0x01;
    params.dstAddress[1] = 0x0C;
    params.dstAddress[2] = 0xCD;
    params.dstAddress[3] = 0x01;
    params.dstAddress[4] = 0x00;
    params.dstAddress[5] = (uint8_t)(app_id & 0xFF);

    /* ── Publisher ────────────────────────────────────────────────── */
    GoosePublisher pub = GoosePublisher_createEx(&params, interface_id, true);
    if (pub == NULL) {
        fprintf(stderr, "Failed to create GoosePublisher\n");
        return 1;
    }

    GoosePublisher_setGoID(pub, "GOOSESimulator");
    GoosePublisher_setGoCbRef(pub, "Simulator/LLN0$GO$gcbEvents");
    GoosePublisher_setDataSetRef(pub, "Simulator/LLN0$Events");
    GoosePublisher_setConfRev(pub, 1);
    GoosePublisher_setTimeAllowedToLive(pub, (uint32_t)(interval_ms * 4));

    printf("READY\n");
    fflush(stdout);

    /* ── Create data set with counter value ────────────────────────── */
    LinkedList dataSet = LinkedList_create();
    if (dataSet == NULL) {
        fprintf(stderr, "Failed to create data list\n");
        GoosePublisher_destroy(pub);
        return 1;
    }

    /* Add a single 32-bit integer element (stVal) */
    MmsValue *counter_val = MmsValue_newIntegerFromInt32(0);
    LinkedList_add(dataSet, counter_val);

    int publish_count = 0;
    int error_count = 0;

    while (1) {
        int64_t tick_start = monotonic_now_ms();

        /* Update counter */
        MmsValue_setInt32(counter_val, publish_count);

        /* Publish */
        int result = GoosePublisher_publish(pub, dataSet);
        if (result == 0) {
            printf("SAMPLE\t%d\t%lld\n", publish_count, (long long)tick_start);
            fflush(stdout);
            publish_count++;
        } else {
            error_count++;
            fprintf(stderr, "Publish failed (result=%d) at count=%d\n", result, publish_count);
        }

        millisleep((uint32_t)interval_ms);
    }

    /* Cleanup (unreachable in current loop) */
    LinkedList_destroy(dataSet);
    MmsValue_delete(counter_val);
    GoosePublisher_destroy(pub);

    return 0;
}
