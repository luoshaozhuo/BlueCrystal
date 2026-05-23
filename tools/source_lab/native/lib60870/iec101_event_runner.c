/*
 * iec101_event_runner.c
 *
 * IEC 101 event reception runner. Connects as CS101 master, continuously
 * polls the slave for class 2 data, and prints NOTIFY for each received
 * event ASDU.
 *
 * CLI: <serial_device> <baudrate> <parity> <data_bits> <stop_bits>
 *      <common_addr> <duration_s>
 *
 * Stdout: READY, NOTIFY (per event), STREAM_SUMMARY, DONE.
 * All diagnostics go to stderr.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <signal.h>

#include <lib60870/cs101_master.h>
#include <lib60870/iec60870_common.h>
#include <lib60870/cs101_information_objects.h>
#include <lib60870/hal_serial.h>
#include <lib60870/hal_time.h>

static volatile bool g_running = true;
static long g_event_count = 0;
static long g_value_count = 0;

static void stop_handler(int sig)
{
    (void)sig;
    g_running = false;
}

static void print_notify_from_asdu(CS101_ASDU asdu)
{
    TypeID type = CS101_ASDU_getTypeID(asdu);
    int num_elems = CS101_ASDU_getNumberOfElements(asdu);
    int ca = CS101_ASDU_getCA(asdu);
    int cot = (int)CS101_ASDU_getCOT(asdu);

    for (int i = 0; i < num_elems; i++) {
        InformationObject io = CS101_ASDU_getElement(asdu, i);
        if (io == NULL)
            continue;

        int ioa = InformationObject_getObjectAddress(io);
        TypeID io_type = InformationObject_getType(io);

        g_event_count++;
        g_value_count++;

        printf("NOTIFY\t%ld\t%d\t%d\t%d",
               g_event_count, ioa, (int)io_type, cot);

        switch (io_type) {
        case M_SP_NA_1:
        {
            SinglePointInformation spi = (SinglePointInformation)io;
            printf("\tSP\t%s", SinglePointInformation_getValue(spi) ? "1" : "0");
            break;
        }
        case M_DP_NA_1:
        {
            DoublePointInformation dpi = (DoublePointInformation)io;
            printf("\tDP\t%d", (int)DoublePointInformation_getValue(dpi));
            break;
        }
        case M_ME_NC_1:
        {
            MeasuredValueShort mvs = (MeasuredValueShort)io;
            printf("\tSHORT\t%.6f", (double)MeasuredValueShort_getValue(mvs));
            break;
        }
        case M_ME_NB_1:
        {
            MeasuredValueScaled mvs = (MeasuredValueScaled)io;
            printf("\tSCALED\t%d", MeasuredValueScaled_getValue(mvs));
            break;
        }
        case M_ME_NA_1:
        {
            MeasuredValueNormalized mvn = (MeasuredValueNormalized)io;
            printf("\tNORM\t%.6f", (double)MeasuredValueNormalized_getValue(mvn));
            break;
        }
        default:
            printf("\tTYPE%d\t-", (int)io_type);
            break;
        }

        printf("\n");
        fflush(stdout);
    }
}

static bool asdu_received_handler(void *parameter, int address, CS101_ASDU asdu)
{
    (void)parameter;
    (void)address;

    print_notify_from_asdu(asdu);
    return true;
}

int main(int argc, char *argv[])
{
    if (argc < 8) {
        fprintf(stderr, "Usage: %s <serial_device> <baudrate> <parity> "
                        "<data_bits> <stop_bits> <common_addr> <duration_s>\n",
                argv[0]);
        return 1;
    }

    const char *device = argv[1];
    int baudrate = atoi(argv[2]);
    char parity = argv[3][0];
    int data_bits = atoi(argv[4]);
    int stop_bits = atoi(argv[5]);
    int common_addr = atoi(argv[6]);
    int duration_s = atoi(argv[7]);

    if (duration_s <= 0) {
        fprintf(stderr, "ERROR: duration_s must be positive\n");
        return 1;
    }

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

    /* Create master in unbalanced mode */
    CS101_Master master = CS101_Master_create(
        serial_port, &ll_params, &al_params, IEC60870_LINK_LAYER_UNBALANCED);

    if (master == NULL) {
        fprintf(stderr, "ERROR: failed to create CS101 master\n");
        SerialPort_close(serial_port);
        SerialPort_destroy(serial_port);
        return 1;
    }

    CS101_Master_setASDUReceivedHandler(master, asdu_received_handler, NULL);
    CS101_Master_addSlave(master, common_addr);
    CS101_Master_start(master);

    fprintf(stderr, "INFO: CS101 event master started on %s\n", device);

    printf("READY\n");
    fflush(stdout);

    /* Wait for link up */
    usleep(500000);

    /* Event loop - poll continuously for the specified duration */
    int elapsed_ms = 0;
    int total_ms = duration_s * 1000;

    while (g_running && elapsed_ms < total_ms) {
        CS101_Master_pollSingleSlave(master, common_addr);
        usleep(50000); /* 50ms between polls */
        elapsed_ms += 50;
    }

    printf("STREAM_SUMMARY\t%ld\t%ld\n", g_event_count, g_value_count);
    printf("DONE\n");
    fflush(stdout);

    CS101_Master_stop(master);
    CS101_Master_destroy(master);
    SerialPort_close(serial_port);
    SerialPort_destroy(serial_port);

    fprintf(stderr, "INFO: done, received %ld events, %ld values\n",
            g_event_count, g_value_count);

    return 0;
}
