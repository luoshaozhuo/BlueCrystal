/*
 * modbus_tcp_polling_runner.c
 *
 * Polls Modbus TCP holding registers at a fixed interval and outputs
 * SAMPLE / BATCH / SUMMARY / DONE lines on stdout (no other stdout noise).
 *
 * CLI: <host> <port> <unit_id> <reg_addr> <reg_count> <interval_ms> <count>
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#include <unistd.h>
#include <modbus/modbus.h>

int main(int argc, char *argv[])
{
    if (argc < 8) {
        fprintf(stderr, "Usage: %s <host> <port> <unit_id> <reg_addr> <reg_count> <interval_ms> <count>\n",
                argv[0]);
        return 1;
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    int unit_id = atoi(argv[3]);
    int reg_addr = atoi(argv[4]);
    int reg_count = atoi(argv[5]);
    int interval_ms = atoi(argv[6]);
    int total_count = atoi(argv[7]);

    if (reg_count <= 0 || total_count <= 0) {
        fprintf(stderr, "ERROR: reg_count and count must be positive\n");
        return 1;
    }

    modbus_t *ctx = modbus_new_tcp(host, port);
    if (ctx == NULL) {
        fprintf(stderr, "ERROR: modbus_new_tcp failed\n");
        return 1;
    }

    modbus_set_slave(ctx, unit_id);

    if (modbus_connect(ctx) == -1) {
        fprintf(stderr, "ERROR: connect: %s\n", modbus_strerror(errno));
        modbus_free(ctx);
        return 1;
    }

    uint16_t *tab = (uint16_t *)malloc(reg_count * sizeof(uint16_t));
    if (tab == NULL) {
        fprintf(stderr, "ERROR: malloc failed\n");
        modbus_close(ctx);
        modbus_free(ctx);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    int ok = 0, err = 0;
    for (int i = 0; i < total_count; i++) {
        int rc = modbus_read_registers(ctx, reg_addr, reg_count, tab);
        if (rc == -1) {
            fprintf(stderr, "ERROR: read at %d: %s\n", i, modbus_strerror(errno));
            err++;
        } else {
            printf("SAMPLE");
            for (int j = 0; j < rc; j++)
                printf("\t%d", tab[j]);
            printf("\n");
            ok++;
        }
        fflush(stdout);

        if (i < total_count - 1)
            usleep(interval_ms * 1000);
    }

    printf("BATCH\t%d\t%d\t%d\n", ok + err, ok, err);
    printf("SUMMARY\t%d\t%d\n", ok, err);
    printf("DONE\n");
    fflush(stdout);

    free(tab);
    modbus_close(ctx);
    modbus_free(ctx);
    return 0;
}
