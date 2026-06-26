/*
 * modbus_rtu_polling_runner.c
 *
 * Polls Modbus RTU holding registers at a fixed interval and outputs
 * SAMPLE / BATCH / SUMMARY / DONE lines on stdout.
 *
 * CLI: <serial_device> <baudrate> <parity> <data_bits> <stop_bits>
 *      <unit_id> <reg_addr> <reg_count> <interval_ms> <count>
 *
 * parity: 'N' (none), 'E' (even), 'O' (odd)
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
    if (argc < 11) {
        fprintf(stderr, "Usage: %s <serial_device> <baudrate> <parity> <data_bits> <stop_bits> "
                        "<unit_id> <reg_addr> <reg_count> <interval_ms> <count>\n",
                argv[0]);
        return 1;
    }

    const char *device = argv[1];
    int baudrate = atoi(argv[2]);
    const char *parity_str = argv[3];
    int data_bits = atoi(argv[4]);
    int stop_bits = atoi(argv[5]);
    int unit_id = atoi(argv[6]);
    int reg_addr = atoi(argv[7]);
    int reg_count = atoi(argv[8]);
    int interval_ms = atoi(argv[9]);
    int total_count = atoi(argv[10]);

    if (reg_count <= 0 || total_count <= 0) {
        fprintf(stderr, "ERROR: reg_count and count must be positive\n");
        return 1;
    }

    char parity = parity_str[0];
    if (parity != 'N' && parity != 'E' && parity != 'O') {
        fprintf(stderr, "ERROR: parity must be N, E, or O\n");
        return 1;
    }

    modbus_t *ctx = modbus_new_rtu(device, baudrate, parity, data_bits, stop_bits);
    if (ctx == NULL) {
        fprintf(stderr, "ERROR: modbus_new_rtu failed\n");
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
