#define _POSIX_C_SOURCE 199309L

#include <libiec61850/sv_subscriber.h>
#include <libiec61850/iec61850_common.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ── Forward declarations ─────────────────────────────────────────── */

static int64_t monotonic_now_ms(void);
static int64_t monotonic_now_us(void);
static void millisleep(uint32_t ms);
static void sv_update_listener(SVSubscriber subscriber, void *parameter, SVSubscriber_ASDU asdu);

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

/* ══════════════════════════════════════════════════════════════════ */

static void sv_update_listener(SVSubscriber subscriber, void *parameter, SVSubscriber_ASDU asdu) {
    (void)subscriber;
    (void)parameter;

    uint16_t smp_cnt = SVSubscriber_ASDU_getSmpCnt(asdu);
    const char *sv_id = SVSubscriber_ASDU_getSvId(asdu);
    const char *dat_set = SVSubscriber_ASDU_getDatSet(asdu);
    uint32_t conf_rev = SVSubscriber_ASDU_getConfRev(asdu);
    int data_size = SVSubscriber_ASDU_getDataSize(asdu);
    uint64_t refr_tm = 0;
    if (SVSubscriber_ASDU_hasRefrTm(asdu)) {
        refr_tm = SVSubscriber_ASDU_getRefrTmAsMs(asdu);
    }

    if (sv_id == NULL) sv_id = "-";
    if (dat_set == NULL) dat_set = "-";

    /* Get the first FLOAT32 value if data is large enough */
    float val0 = 0.0f;
    int val_count = 0;
    if (data_size >= 4) {
        val0 = SVSubscriber_ASDU_getFLOAT32(asdu, 0);
        val_count = data_size / 4;
    }

    printf("NOTIFY\t%u\t%s\t%s\t%u\t%u\t%d\t%llu\t%.9g\t%d\n",
           smp_cnt,
           sv_id,
           dat_set,
           conf_rev,
           (unsigned int)data_size,
           val_count,
           (unsigned long long)refr_tm,
           (double)val0,
           val_count);
    fflush(stdout);

    g_msg_count++;
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
    SVReceiver receiver = SVReceiver_create();
    if (receiver == NULL) {
        fprintf(stderr, "Failed to create SVReceiver\n");
        return 1;
    }

    SVReceiver_setInterfaceId(receiver, interface_id);

    /* Create subscriber with no ethAddr filter (NULL) and given appID */
    SVSubscriber subscriber = SVSubscriber_create(NULL, app_id);
    if (subscriber == NULL) {
        fprintf(stderr, "Failed to create SVSubscriber\n");
        SVReceiver_destroy(receiver);
        return 1;
    }

    SVSubscriber_setListener(subscriber, sv_update_listener, NULL);

    SVReceiver_addSubscriber(receiver, subscriber);

    SVReceiver_start(receiver);

    if (!SVReceiver_isRunning(receiver)) {
        fprintf(stderr, "SVReceiver failed to start\n");
        SVReceiver_destroy(receiver);
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
    SVReceiver_stop(receiver);
    SVReceiver_destroy(receiver); /* also destroys subscriber */

    printf("STREAM_SUMMARY\t%d\t%d\n", g_msg_count, g_msg_errors);
    fflush(stdout);

    printf("DONE\n");
    fflush(stdout);

    return 0;
}
