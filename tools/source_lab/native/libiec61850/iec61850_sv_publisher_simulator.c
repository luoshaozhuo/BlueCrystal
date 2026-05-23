#define _POSIX_C_SOURCE 199309L

#include <libiec61850/sv_publisher.h>
#include <libiec61850/iec61850_common.h>

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
        fprintf(stderr, "Usage: %s <interface> <app_id> <sample_rate>\n", argv[0]);
        return 2;
    }

    const char *interface_id = argv[1];
    uint16_t app_id = (uint16_t)atoi(argv[2]);
    int sample_rate = atoi(argv[3]);

    if (sample_rate <= 0) {
        fprintf(stderr, "Invalid sample_rate (must be > 0 Hz)\n");
        return 2;
    }

    int interval_ms = 1000 / sample_rate;
    if (interval_ms < 1) interval_ms = 1;

    /* ── Communication parameters ────────────────────────────────── */
    CommParameters params;
    memset(&params, 0, sizeof(params));
    params.vlanPriority = 4;
    params.vlanId = 0;
    params.appId = app_id;
    params.dstAddress[0] = 0x01;
    params.dstAddress[1] = 0x0C;
    params.dstAddress[2] = 0xCD;
    params.dstAddress[3] = 0x04;
    params.dstAddress[4] = 0x00;
    params.dstAddress[5] = (uint8_t)(app_id & 0xFF);

    /* ── Publisher ────────────────────────────────────────────────── */
    SVPublisher pub = SVPublisher_createEx(&params, interface_id, false);
    if (pub == NULL) {
        fprintf(stderr, "Failed to create SVPublisher\n");
        return 1;
    }

    /* Add one ASDU with two FLOAT32 values (voltage, current) */
    SVPublisher_ASDU asdu = SVPublisher_addASDU(pub, "SVPubSimulator", "Simulator/LLN0$PhVMeas", 1);
    if (asdu == NULL) {
        fprintf(stderr, "Failed to add ASDU\n");
        SVPublisher_destroy(pub);
        return 1;
    }

    SVPublisher_ASDU_setSmpMod(asdu, IEC61850_SV_SMPMOD_SAMPLES_PER_SECOND);
    SVPublisher_ASDU_setSmpRate(asdu, (uint16_t)sample_rate);

    /* Add data elements */
    int idx_voltage = SVPublisher_ASDU_addFLOAT(asdu);
    int idx_current = SVPublisher_ASDU_addFLOAT(asdu);

    if (idx_voltage < 0 || idx_current < 0) {
        fprintf(stderr, "Failed to add ASDU data elements\n");
        SVPublisher_destroy(pub);
        return 1;
    }

    /* Enable refresh time */
    SVPublisher_ASDU_enableRefrTm(asdu);

    /* Finalize ASDU configuration */
    SVPublisher_setupComplete(pub);

    printf("READY\n");
    fflush(stdout);

    /* ── Publishing loop ───────────────────────────────────────────── */
    uint16_t smp_cnt = 0;
    double volts = 230.0;
    double amps = 10.0;
    int publish_count = 0;
    int error_count = 0;

    while (1) {
        int64_t tick_start = monotonic_now_ms();

        /* Update values with some variation */
        volts = 230.0 + (smp_cnt % 10) * 0.5;
        amps = 10.0 + (smp_cnt % 20) * 0.2;

        SVPublisher_ASDU_setFLOAT(asdu, idx_voltage, (float)volts);
        SVPublisher_ASDU_setFLOAT(asdu, idx_current, (float)amps);
        SVPublisher_ASDU_setSmpCnt(asdu, smp_cnt);
        SVPublisher_ASDU_setRefrTm(asdu, (msSinceEpoch)tick_start);

        SVPublisher_publish(pub);

        printf("SAMPLE\t%u\t%.6f\t%.6f\t%lld\n",
               smp_cnt,
               volts,
               amps,
               (long long)tick_start);
        fflush(stdout);

        smp_cnt++;
        publish_count++;

        millisleep((uint32_t)interval_ms);
    }

    /* Cleanup (unreachable) */
    SVPublisher_destroy(pub);
    return 0;
}
