/*
 * modbus_simulator_server.c
 *
 * Simple Modbus TCP simulator server. Binds to a port, creates a modbus
 * mapping with some example values, and runs an infinite server loop.
 *
 * CLI: <port>
 *
 * Stdout protocol: READY on start, ERROR on failure.
 * All diagnostics go to stderr.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <modbus/modbus.h>

static volatile int running = 1;

static void stop_handler(int sig)
{
    (void)sig;
    running = 0;
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

    /* Create a Modbus TCP server context */
    modbus_mapping_t *mapping = modbus_mapping_new(
        MODBUS_MAX_READ_BITS,      /* nb_bits */
        0,                         /* nb_input_bits */
        MODBUS_MAX_READ_REGISTERS, /* nb_registers */
        0                          /* nb_input_registers */
    );
    if (mapping == NULL) {
        fprintf(stderr, "ERROR: modbus_mapping_new failed\n");
        return 1;
    }

    /* Initialize holding registers with some example values */
    for (int i = 0; i < MODBUS_MAX_READ_REGISTERS; i++)
        mapping->tab_registers[i] = (uint16_t)(i * 10);

    /* Initialize discrete outputs */
    for (int i = 0; i < MODBUS_MAX_READ_BITS; i++)
        mapping->tab_bits[i] = (i % 2 != 0) ? 1 : 0;

    /* Listen on all interfaces */
    modbus_t *ctx = modbus_new_tcp("0.0.0.0", port);
    if (ctx == NULL) {
        fprintf(stderr, "ERROR: modbus_new_tcp failed\n");
        modbus_mapping_free(mapping);
        return 1;
    }

    int server_socket = modbus_tcp_listen(ctx, 1);
    if (server_socket == -1) {
        fprintf(stderr, "ERROR: modbus_tcp_listen: %s\n", modbus_strerror(errno));
        modbus_free(ctx);
        modbus_mapping_free(mapping);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    while (running) {
        int client_socket = modbus_tcp_accept(ctx, &server_socket);
        if (client_socket == -1) {
            if (running)
                fprintf(stderr, "ERROR: modbus_tcp_accept: %s\n", modbus_strerror(errno));
            continue;
        }

        fprintf(stderr, "INFO: client connected\n");

        uint8_t query[MODBUS_TCP_MAX_ADU_LENGTH];
        while (running) {
            int rc = modbus_receive(ctx, query);
            if (rc == -1) {
                /* Connection closed or error */
                break;
            }

            rc = modbus_reply(ctx, query, rc, mapping);
            if (rc == -1) {
                fprintf(stderr, "ERROR: modbus_reply: %s\n", modbus_strerror(errno));
                break;
            }
        }

        modbus_close(ctx);
        fprintf(stderr, "INFO: client disconnected\n");
    }

    modbus_mapping_free(mapping);
    modbus_free(ctx);

    printf("DONE\n");
    fflush(stdout);

    return 0;
}
