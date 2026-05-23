/*
 * iec104_event_runner.c
 *
 * IEC 104 event/subscription runner. Connects as CS104 client, enables
 * spontaneous data transfer, and prints NOTIFY lines for each received
 * event ASDU.
 *
 * CLI: <host> <port> <common_addr> <duration_s>
 *
 * Stdout: READY, NOTIFY (per ASDU/event), STREAM_SUMMARY, DONE.
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

        /* Print debug info to stderr */
        fprintf(stderr, "INFO: NOTIFY type=%d ca=%d cot=%d ioa=%d elem=%d/%d\n",
                (int)type, ca, cot, ioa, i + 1, num_elems);

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
        g_running = false;
        break;
    }
}

int main(int argc, char *argv[])
{
    if (argc < 5) {
        fprintf(stderr, "Usage: %s <host> <port> <common_addr> <duration_s>\n",
                argv[0]);
        return 1;
    }

    const char *host = argv[1];
    int tcp_port = atoi(argv[2]);
    int common_addr = atoi(argv[3]);
    int duration_s = atoi(argv[4]);

    if (duration_s <= 0) {
        fprintf(stderr, "ERROR: duration_s must be positive\n");
        return 1;
    }

    signal(SIGINT, stop_handler);
    signal(SIGTERM, stop_handler);

    CS104_Connection connection = CS104_Connection_create(host, tcp_port);
    if (connection == NULL) {
        fprintf(stderr, "ERROR: failed to create CS104 connection\n");
        return 1;
    }

    CS104_Connection_setASDUReceivedHandler(connection, asdu_received_handler, NULL);
    CS104_Connection_setConnectionHandler(connection, connection_handler, NULL);

    CS104_APCIParameters apci_params = CS104_Connection_getAPCIParameters(connection);
    apci_params->t0 = 10000;
    apci_params->t1 = 15000;
    apci_params->t2 = 10000;
    apci_params->t3 = 20000;

    fprintf(stderr, "INFO: connecting to %s:%d\n", host, tcp_port);

    if (!CS104_Connection_connect(connection)) {
        fprintf(stderr, "ERROR: connection failed\n");
        CS104_Connection_destroy(connection);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    /* Wait for events for the specified duration */
    fprintf(stderr, "INFO: listening for events for %d seconds\n", duration_s);

    int elapsed_ms = 0;
    int total_ms = duration_s * 1000;
    while (g_running && elapsed_ms < total_ms) {
        usleep(100000); /* 100ms sleep */
        elapsed_ms += 100;
    }

    printf("STREAM_SUMMARY\t%ld\t%ld\n", g_event_count, g_value_count);
    printf("DONE\n");
    fflush(stdout);

    CS104_Connection_sendStopDT(connection);
    CS104_Connection_close(connection);
    CS104_Connection_destroy(connection);

    fprintf(stderr, "INFO: done, received %ld events, %ld values\n",
            g_event_count, g_value_count);

    return 0;
}
