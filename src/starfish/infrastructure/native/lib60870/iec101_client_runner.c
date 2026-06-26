/*
 * iec101_client_runner.c
 *
 * IEC 101 polling runner (serial). Connects as CS101 master, sends
 * interrogation at each interval, and prints SAMPLE lines from received
 * ASDUs.
 *
 * CLI: <serial_device> <baudrate> <parity> <data_bits> <stop_bits>
 *      <common_addr> <interval_ms> <count>
 *
 * Stdout: READY, SAMPLE (per received IOA/value), BATCH, SUMMARY, DONE.
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
static int g_interrogation_count = 0;
static int g_ok_count = 0;
static int g_err_count = 0;
static int g_total_sample_count = 0;

static void stop_handler(int sig)
{
    (void)sig;
    g_running = false;
}

static void print_sample_from_asdu(CS101_ASDU asdu)
{
    TypeID type = CS101_ASDU_getTypeID(asdu);
    int num_elems = CS101_ASDU_getNumberOfElements(asdu);

    for (int i = 0; i < num_elems; i++) {
        InformationObject io = CS101_ASDU_getElement(asdu, i);
        if (io == NULL)
            continue;

        int ioa = InformationObject_getObjectAddress(io);
        TypeID io_type = InformationObject_getType(io);

        printf("SAMPLE\t%d\t%d", g_interrogation_count, ioa);

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
        case M_ME_NA_1:
        {
            MeasuredValueNormalized mvn = (MeasuredValueNormalized)io;
            printf("\tNORM\t%.6f", (double)MeasuredValueNormalized_getValue(mvn));
            break;
        }
        case M_ME_NB_1:
        {
            MeasuredValueScaled mvs = (MeasuredValueScaled)io;
            printf("\tSCALED\t%d", MeasuredValueScaled_getValue(mvs));
            break;
        }
        case M_ME_NC_1:
        {
            MeasuredValueShort mvs = (MeasuredValueShort)io;
            printf("\tSHORT\t%.6f", (double)MeasuredValueShort_getValue(mvs));
            break;
        }
        case M_ST_NA_1:
        {
            StepPositionInformation spi = (StepPositionInformation)io;
            printf("\tSTEP\t%d", StepPositionInformation_getValue(spi));
            break;
        }
        default:
            printf("\tTYPE%d\t-", (int)io_type);
            break;
        }

        printf("\n");
        g_total_sample_count++;
        fflush(stdout);
    }
}

static bool asdu_received_handler(void *parameter, int address, CS101_ASDU asdu)
{
    (void)parameter;
    (void)address;

    print_sample_from_asdu(asdu);
    return true;
}

int main(int argc, char *argv[])
{
    if (argc < 9) {
        fprintf(stderr, "Usage: %s <serial_device> <baudrate> <parity> "
                        "<data_bits> <stop_bits> <common_addr> <interval_ms> <count>\n",
                argv[0]);
        return 1;
    }

    const char *device = argv[1];
    int baudrate = atoi(argv[2]);
    char parity = argv[3][0];
    int data_bits = atoi(argv[4]);
    int stop_bits = atoi(argv[5]);
    int common_addr = atoi(argv[6]);
    int interval_ms = atoi(argv[7]);
    int total_count = atoi(argv[8]);

    if (total_count <= 0) {
        fprintf(stderr, "ERROR: count must be positive\n");
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

    fprintf(stderr, "INFO: CS101 master started on %s\n", device);

    printf("READY\n");
    fflush(stdout);

    /* Wait for link to come up */
    usleep(1000000); /* 1s initial wait */

    /* Main polling loop */
    for (int i = 0; i < total_count && g_running; i++) {
        g_interrogation_count = i + 1;

        /* Poll slave to receive data */
        CS101_Master_pollSingleSlave(master, common_addr);

        /* Send interrogation */
        CS101_Master_sendInterrogationCommand(
            master, CS101_COT_ACTIVATION, common_addr, IEC60870_QOI_STATION);

        fprintf(stderr, "INFO: sent interrogation %d\n", i + 1);
        g_ok_count++;

        /* Poll a few more times to receive response */
        for (int p = 0; p < 5; p++) {
            CS101_Master_pollSingleSlave(master, common_addr);
            usleep(100000); /* 100ms between polls */
        }

        if (i < total_count - 1)
            usleep((interval_ms - 500) * 1000);
    }

    printf("BATCH\t%d\t%d\t%d\n",
           g_ok_count + g_err_count, g_ok_count, g_err_count);
    printf("SUMMARY\t%d\t%d\n",
           g_total_sample_count, (g_total_sample_count > 0) ? 100 : 0);
    printf("DONE\n");
    fflush(stdout);

    CS101_Master_stop(master);
    CS101_Master_destroy(master);
    SerialPort_close(serial_port);
    SerialPort_destroy(serial_port);

    return 0;
}
