/*
 * iec104_client_runner.c
 *
 * IEC 104 polling runner. Connects as CS104 client, sends interrogation
 * (total interrogation / station call) at each interval, and prints
 * SAMPLE lines from received ASDUs.
 *
 * CLI: <host> <port> <common_addr> <interval_ms> <count>
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

#include <lib60870/cs104_connection.h>
#include <lib60870/iec60870_common.h>
#include <lib60870/cs101_information_objects.h>
#include <lib60870/hal_time.h>

static volatile int g_interrogation_count = 0;
static int g_total_interrogations = 0;
static int g_ok_count = 0;
static int g_err_count = 0;
static int g_total_sample_count = 0;

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
        case M_BO_NA_1:
        {
            BitString32 bs = (BitString32)io;
            printf("\tBITS\t%u", (unsigned)BitString32_getValue(bs));
            break;
        }
        case M_IT_NA_1:
        {
            IntegratedTotals it = (IntegratedTotals)io;
            BinaryCounterReading bcr = IntegratedTotals_getBCR(it);
            printf("\tTOTAL\t%ld", (long)BinaryCounterReading_getValue(bcr));
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

static void connection_handler(void *parameter, CS104_Connection connection,
                               CS104_ConnectionEvent event)
{
    (void)parameter;

    switch (event) {
    case CS104_CONNECTION_OPENED:
        fprintf(stderr, "INFO: connection opened\n");
        CS104_Connection_sendStartDT(connection);
        break;
    case CS104_CONNECTION_CLOSED:
        fprintf(stderr, "INFO: connection closed\n");
        break;
    case CS104_CONNECTION_STARTDT_CON_RECEIVED:
        fprintf(stderr, "INFO: STARTDT received\n");
        break;
    case CS104_CONNECTION_STOPDT_CON_RECEIVED:
        fprintf(stderr, "INFO: STOPDT received\n");
        break;
    case CS104_CONNECTION_FAILED:
        fprintf(stderr, "ERROR: connection failed\n");
        break;
    }
}

int main(int argc, char *argv[])
{
    if (argc < 6) {
        fprintf(stderr, "Usage: %s <host> <port> <common_addr> <interval_ms> <count>\n",
                argv[0]);
        return 1;
    }

    const char *host = argv[1];
    int tcp_port = atoi(argv[2]);
    int common_addr = atoi(argv[3]);
    int interval_ms = atoi(argv[4]);
    g_total_interrogations = atoi(argv[5]);

    if (g_total_interrogations <= 0) {
        fprintf(stderr, "ERROR: count must be positive\n");
        return 1;
    }

    CS104_Connection connection = CS104_Connection_create(host, tcp_port);
    if (connection == NULL) {
        fprintf(stderr, "ERROR: failed to create CS104 connection\n");
        return 1;
    }

    CS104_Connection_setASDUReceivedHandler(connection, asdu_received_handler, NULL);
    CS104_Connection_setConnectionHandler(connection, connection_handler, NULL);

    /* Use default APCI parameters */
    CS104_APCIParameters apci_params = CS104_Connection_getAPCIParameters(connection);
    apci_params->t0 = 10000;  /* 10s connect timeout */
    apci_params->t1 = 15000;  /* 15s send/receive timeout */
    apci_params->t2 = 10000;  /* 10s ack timeout */
    apci_params->t3 = 20000;  /* 20s test frame timeout */

    fprintf(stderr, "INFO: connecting to %s:%d\n", host, tcp_port);

    if (!CS104_Connection_connect(connection)) {
        fprintf(stderr, "ERROR: connection failed\n");
        CS104_Connection_destroy(connection);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    /* Main polling loop */
    for (int i = 0; i < g_total_interrogations; i++) {
        g_interrogation_count = i + 1;

        /* Small delay before sending interrogation to let STARTDT complete */
        if (i == 0)
            usleep(500000); /* 500ms initial wait */

        bool sent = CS104_Connection_sendInterrogationCommand(
            connection, CS101_COT_ACTIVATION, common_addr, IEC60870_QOI_STATION);

        if (!sent) {
            fprintf(stderr, "ERROR: failed to send interrogation at iteration %d\n", i);
            g_err_count++;
        } else {
            g_ok_count++;
            fprintf(stderr, "INFO: sent interrogation %d\n", i + 1);
        }

        /* Wait for responses */
        if (i < g_total_interrogations - 1)
            usleep(interval_ms * 1000);
        else
            usleep(500000); /* extra time for final responses */
    }

    printf("BATCH\t%d\t%d\t%d\n",
           g_ok_count + g_err_count, g_ok_count, g_err_count);
    printf("SUMMARY\t%d\t%d\n",
           g_total_sample_count,
           (g_total_sample_count > 0) ? 100 : 0);
    printf("DONE\n");
    fflush(stdout);

    CS104_Connection_sendStopDT(connection);
    CS104_Connection_close(connection);
    CS104_Connection_destroy(connection);

    return 0;
}
