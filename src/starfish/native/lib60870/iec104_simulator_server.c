/*
 * iec104_simulator_server.c
 *
 * Simple IEC 104 server simulator. Binds to a TCP port and responds to
 * interrogation commands with test ASDUs containing measured values and
 * single points.
 *
 * CLI: <port>
 *
 * Stdout: READY on start, DONE on shutdown.
 * All diagnostics go to stderr.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <signal.h>

#include <lib60870/cs104_slave.h>
#include <lib60870/iec60870_common.h>
#include <lib60870/cs101_information_objects.h>
#include <lib60870/hal_time.h>

static volatile bool g_running = true;

static void stop_handler(int sig)
{
    (void)sig;
    g_running = false;
}

static bool interrogation_handler(void *parameter, IMasterConnection connection,
                                  CS101_ASDU asdu, uint8_t qoi)
{
    (void)parameter;
    (void)qoi;

    int ca = CS101_ASDU_getCA(asdu);
    CS101_AppLayerParameters al_params = IMasterConnection_getApplicationLayerParameters(connection);

    fprintf(stderr, "INFO: interrogation received, ca=%d, qoi=%d\n", ca, qoi);

    /* Create ASDU with measured short values (M_ME_NC_1) */
    CS101_ASDU resp_asdu = CS101_ASDU_create(al_params, false,
        CS101_COT_INTERROGATED_BY_STATION, 0, ca, false, false);

    if (resp_asdu) {
        /* Add some test values */
        for (int ioa = 1; ioa <= 10; ioa++) {
            MeasuredValueShort mv = MeasuredValueShort_create(
                NULL, ioa, (float)(ioa * 100 + ioa * 10), IEC60870_QUALITY_GOOD);
            if (mv) {
                CS101_ASDU_addInformationObject(resp_asdu, (InformationObject)mv);
                MeasuredValueShort_destroy(mv);
            }
        }
        CS101_ASDU_setTypeID(resp_asdu, M_ME_NC_1);

        bool sent = IMasterConnection_sendASDU(connection, resp_asdu);
        fprintf(stderr, "INFO: sent measured values ASDU: %s\n", sent ? "ok" : "failed");

        CS101_ASDU_destroy(resp_asdu);
    }

    /* Create ASDU with single-point information (M_SP_NA_1) */
    CS101_ASDU sp_asdu = CS101_ASDU_create(al_params, false,
        CS101_COT_INTERROGATED_BY_STATION, 0, ca, false, false);

    if (sp_asdu) {
        for (int ioa = 101; ioa <= 105; ioa++) {
            SinglePointInformation sp = SinglePointInformation_create(
                NULL, ioa, (ioa % 2 != 0), IEC60870_QUALITY_GOOD);
            if (sp) {
                CS101_ASDU_addInformationObject(sp_asdu, (InformationObject)sp);
                SinglePointInformation_destroy(sp);
            }
        }
        CS101_ASDU_setTypeID(sp_asdu, M_SP_NA_1);

        bool sent = IMasterConnection_sendASDU(connection, sp_asdu);
        fprintf(stderr, "INFO: sent single-point ASDU: %s\n", sent ? "ok" : "failed");

        CS101_ASDU_destroy(sp_asdu);
    }

    return true;
}

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <port>\n", argv[0]);
        return 1;
    }

    int port = atoi(argv[1]);
    if (port <= 0 || port > 65535) {
        fprintf(stderr, "ERROR: invalid port %d\n", port);
        return 1;
    }

    signal(SIGINT, stop_handler);
    signal(SIGTERM, stop_handler);

    CS104_Slave slave = CS104_Slave_create(100, 10);
    if (slave == NULL) {
        fprintf(stderr, "ERROR: failed to create CS104 slave\n");
        return 1;
    }

    CS104_Slave_setLocalPort(slave, port);
    CS104_Slave_setLocalAddress(slave, "0.0.0.0");

    CS101_AppLayerParameters al_params = CS104_Slave_getAppLayerParameters(slave);
    al_params->sizeOfCA = 2;
    al_params->sizeOfIOA = 3;
    al_params->sizeOfCOT = 2;

    CS104_Slave_setInterrogationHandler(slave, interrogation_handler, NULL);

    fprintf(stderr, "INFO: starting IEC 104 server on port %d\n", port);

    CS104_Slave_start(slave);

    printf("READY\n");
    fflush(stdout);

    /* Main loop - keep running */
    while (g_running) {
        usleep(100000); /* 100ms */
    }

    CS104_Slave_stop(slave);
    CS104_Slave_destroy(slave);

    printf("DONE\n");
    fflush(stdout);

    fprintf(stderr, "INFO: server stopped\n");

    return 0;
}
