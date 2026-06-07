/*
 * iec101_simulator_slave.c
 *
 * Simple IEC 101 slave simulator. Listens on a serial device and responds
 * to interrogation commands with test ASDUs.
 *
 * CLI: <serial_device> <baudrate> <parity> <data_bits> <stop_bits>
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

#include <lib60870/cs101_slave.h>
#include <lib60870/iec60870_common.h>
#include <lib60870/cs101_information_objects.h>
#include <lib60870/hal_serial.h>
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
        for (int ioa = 1; ioa <= 5; ioa++) {
            MeasuredValueShort mv = MeasuredValueShort_create(
                NULL, ioa, (float)(ioa * 100), IEC60870_QUALITY_GOOD);
            if (mv) {
                CS101_ASDU_addInformationObject(resp_asdu, (InformationObject)mv);
                MeasuredValueShort_destroy(mv);
            }
        }

        CS101_ASDU_setTypeID(resp_asdu, M_ME_NC_1);

        bool sent = IMasterConnection_sendASDU(connection, resp_asdu);
        fprintf(stderr, "INFO: sent measured values ASDU: %s\n",
                sent ? "ok" : "failed");

        CS101_ASDU_destroy(resp_asdu);
    }

    /* Create ASDU with single-point information (M_SP_NA_1) */
    CS101_ASDU sp_asdu = CS101_ASDU_create(al_params, false,
        CS101_COT_INTERROGATED_BY_STATION, 0, ca, false, false);

    if (sp_asdu) {
        for (int ioa = 101; ioa <= 103; ioa++) {
            SinglePointInformation sp = SinglePointInformation_create(
                NULL, ioa, (ioa % 2 != 0), IEC60870_QUALITY_GOOD);
            if (sp) {
                CS101_ASDU_addInformationObject(sp_asdu, (InformationObject)sp);
                SinglePointInformation_destroy(sp);
            }
        }

        CS101_ASDU_setTypeID(sp_asdu, M_SP_NA_1);

        bool sent = IMasterConnection_sendASDU(connection, sp_asdu);
        fprintf(stderr, "INFO: sent single-point ASDU: %s\n",
                sent ? "ok" : "failed");

        CS101_ASDU_destroy(sp_asdu);
    }

    return true;
}

int main(int argc, char *argv[])
{
    if (argc < 6) {
        fprintf(stderr, "Usage: %s <serial_device> <baudrate> <parity> "
                        "<data_bits> <stop_bits>\n",
                argv[0]);
        return 1;
    }

    const char *device = argv[1];
    int baudrate = atoi(argv[2]);
    char parity = argv[3][0];
    int data_bits = atoi(argv[4]);
    int stop_bits = atoi(argv[5]);

    if (parity != 'N' && parity != 'E' && parity != 'O') {
        fprintf(stderr, "ERROR: parity must be N, E, or O\n");
        return 1;
    }

    signal(SIGINT, stop_handler);
    signal(SIGTERM, stop_handler);

    /* Create and open serial port */
    SerialPort serial_port = SerialPort_create(device, baudrate,
                                               (uint8_t)data_bits,
                                               parity,
                                               (uint8_t)stop_bits);
    if (serial_port == NULL) {
        fprintf(stderr, "ERROR: failed to create serial port\n");
        return 1;
    }

    if (!SerialPort_open(serial_port)) {
        fprintf(stderr, "ERROR: failed to open serial port %s\n", device);
        SerialPort_destroy(serial_port);
        return 1;
    }

    SerialPort_setTimeout(serial_port, 1000);

    /* Set up link layer parameters */
    struct sLinkLayerParameters ll_params;
    ll_params.addressLength = 1;
    ll_params.timeoutForAck = 500;
    ll_params.timeoutRepeat = 500;
    ll_params.useSingleCharACK = true;
    ll_params.timeoutLinkState = 500;

    /* Set up application layer parameters */
    struct sCS101_AppLayerParameters al_params;
    al_params.sizeOfTypeId = 1;
    al_params.sizeOfVSQ = 1;
    al_params.sizeOfCOT = 2;
    al_params.originatorAddress = 0;
    al_params.sizeOfCA = 2;
    al_params.sizeOfIOA = 3;
    al_params.maxSizeOfASDU = 249;

    /* Create slave in unbalanced mode */
    CS101_Slave slave = CS101_Slave_create(
        serial_port, &ll_params, &al_params, IEC60870_LINK_LAYER_UNBALANCED);

    if (slave == NULL) {
        fprintf(stderr, "ERROR: failed to create CS101 slave\n");
        SerialPort_close(serial_port);
        SerialPort_destroy(serial_port);
        return 1;
    }

    CS101_Slave_setLinkLayerAddress(slave, 1);
    CS101_Slave_setInterrogationHandler(slave, interrogation_handler, NULL);
    CS101_Slave_start(slave);

    fprintf(stderr, "INFO: CS101 slave started on %s\n", device);

    printf("READY\n");
    fflush(stdout);

    /* Main loop */
    while (g_running) {
        usleep(100000); /* 100ms */
    }

    CS101_Slave_stop(slave);
    CS101_Slave_destroy(slave);
    SerialPort_close(serial_port);
    SerialPort_destroy(serial_port);

    printf("DONE\n");
    fflush(stdout);

    fprintf(stderr, "INFO: slave stopped\n");

    return 0;
}
