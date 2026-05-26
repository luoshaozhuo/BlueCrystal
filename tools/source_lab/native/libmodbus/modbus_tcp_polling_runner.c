/*
 * modbus_tcp_polling_runner.c
 *
 * Two modes:
 *   1. Polling mode (CLI args):
 *        <host> <port> <unit_id> <reg_addr> <reg_count> <interval_ms> <count>
 *   2. Interactive mode (stdin/stdout, no CLI args):
 *        WRITE commands, QUIT
 *
 * Interactive stdin commands:
 *   WRITE\trequest_id\thost\tport\tunit_id\treg_addr\tvalue_type\tvalue
 *   READ\trequest_id\thost\tport\tunit_id\treg_addr\tcount
 *
 * Interactive stdout prefixes:
 *   READY, WRITE_RESULT, READ_RESULT, ERROR
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#include <unistd.h>
#include <modbus/modbus.h>

#define MAX_LINE_LEN 8192
#define MAX_FIELD_LEN 512

static void strip_newline(char *line)
{
    size_t len = strlen(line);
    while(len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r')) {
        line[len - 1] = '\0';
        len--;
    }
}

static int split_fields(char *line, char **fields, int max_fields)
{
    int count = 0;
    char *cursor = line;
    while(cursor != NULL && count < max_fields) {
        fields[count++] = cursor;
        char *tab = strchr(cursor, '\t');
        if(tab == NULL) break;
        *tab = '\0';
        cursor = tab + 1;
    }
    return count;
}

static void sanitize_field(const char *src, char *dst, size_t dst_size)
{
    if(src == NULL) {
        dst[0] = '\0';
        return;
    }
    strncpy(dst, src, dst_size - 1);
    dst[dst_size - 1] = '\0';
}

/* ── WRITE command handler (FC06 write single register) ──────────────── */

static void handle_write_command(char *line)
{
    /* WRITE\trequest_id\thost\tport\tunit_id\treg_addr\tvalue_type\tvalue */
    char *fields[10] = {0};
    int field_count = split_fields(line, fields, 10);
    if(field_count < 8 || strcmp(fields[0], "WRITE") != 0) {
        fprintf(stderr, "WRITE protocol_error: field_count=%d\n", field_count);
        printf("WRITE_RESULT\t-\tok=0\tprotocol_error\tinvalid_write_command_format\n");
        fflush(stdout);
        return;
    }

    char request_id[MAX_FIELD_LEN];
    char host[MAX_FIELD_LEN];
    char value_type[MAX_FIELD_LEN];
    char value_text[MAX_FIELD_LEN];

    sanitize_field(fields[1], request_id, sizeof(request_id));
    sanitize_field(fields[2], host, sizeof(host));
    int port = atoi(fields[3]);
    int unit_id = atoi(fields[4]);
    int reg_addr = atoi(fields[5]);
    sanitize_field(fields[6], value_type, sizeof(value_type));
    sanitize_field(fields[7], value_text, sizeof(value_text));

    if(port <= 0 || port > 65535) {
        fprintf(stderr, "WRITE invalid_port: %d\n", port);
        printf("WRITE_RESULT\t%s\tok=0\tinvalid_port\tport=%d\n", request_id, port);
        fflush(stdout);
        return;
    }

    /* Parse value based on type */
    uint16_t reg_value = 0;
    if(strcmp(value_type, "uint16") == 0 || strcmp(value_type, "int16") == 0) {
        long v = strtol(value_text, NULL, 10);
        reg_value = (uint16_t)(v & 0xFFFF);
    } else if(strcmp(value_type, "bool") == 0) {
        reg_value = (strcmp(value_text, "true") == 0 || strcmp(value_text, "1") == 0) ? 1 : 0;
    } else {
        /* Default: try parsing as integer */
        long v = strtol(value_text, NULL, 10);
        reg_value = (uint16_t)(v & 0xFFFF);
    }

    modbus_t *ctx = modbus_new_tcp(host, port);
    if(ctx == NULL) {
        fprintf(stderr, "WRITE modbus_new_tcp_failed\n");
        printf("WRITE_RESULT\t%s\tok=0\tinternal_error\tmodbus_new_tcp_failed\n", request_id);
        fflush(stdout);
        return;
    }

    modbus_set_slave(ctx, unit_id);

    if(modbus_connect(ctx) == -1) {
        fprintf(stderr, "WRITE connect_failed: %s\n", modbus_strerror(errno));
        printf("WRITE_RESULT\t%s\tok=0\tconnect_failed\t%s\n",
               request_id, modbus_strerror(errno));
        fflush(stdout);
        modbus_free(ctx);
        return;
    }

    int rc = modbus_write_register(ctx, (int)reg_addr, reg_value);
    if(rc == -1) {
        fprintf(stderr, "WRITE write_failed: %s\n", modbus_strerror(errno));
        printf("WRITE_RESULT\t%s\tok=0\twrite_failed\t%s\n",
               request_id, modbus_strerror(errno));
    } else {
        fprintf(stderr, "WRITE done: host=%s port=%d unit=%d addr=%d value=%u type=%s\n",
                host, port, unit_id, reg_addr, (unsigned)reg_value, value_type);
        printf("WRITE_RESULT\t%s\tok=1\tOK\treg_addr=%d\tvalue=%u\tvalue_type=%s\n",
               request_id, reg_addr, (unsigned)reg_value, value_type);
    }
    fflush(stdout);

    modbus_close(ctx);
    modbus_free(ctx);
}

/* ── READ command handler (FC03 read holding registers) ───────────────── */

static void handle_read_command(char *line)
{
    /* READ\trequest_id\thost\tport\tunit_id\treg_addr\tcount */
    char *fields[10] = {0};
    int field_count = split_fields(line, fields, 10);
    if(field_count < 6 || strcmp(fields[0], "READ") != 0) {
        fprintf(stderr, "READ protocol_error: field_count=%d\n", field_count);
        printf("READ_RESULT\t-\tok=0\tprotocol_error\tinvalid_read_command_format\n");
        fflush(stdout);
        return;
    }

    char request_id[MAX_FIELD_LEN];
    char host[MAX_FIELD_LEN];

    sanitize_field(fields[1], request_id, sizeof(request_id));
    sanitize_field(fields[2], host, sizeof(host));
    int port = atoi(fields[3]);
    int unit_id = atoi(fields[4]);
    int reg_addr = atoi(fields[5]);
    int count = (field_count >= 7) ? atoi(fields[6]) : 1;

    if(port <= 0 || port > 65535) {
        fprintf(stderr, "READ invalid_port: %d\n", port);
        printf("READ_RESULT\t%s\tok=0\tinvalid_port\tport=%d\n", request_id, port);
        fflush(stdout);
        return;
    }
    if(count <= 0 || count > 125) {
        fprintf(stderr, "READ invalid_count: %d\n", count);
        printf("READ_RESULT\t%s\tok=0\tinvalid_count\tcount=%d\n", request_id, count);
        fflush(stdout);
        return;
    }

    modbus_t *ctx = modbus_new_tcp(host, port);
    if(ctx == NULL) {
        fprintf(stderr, "READ modbus_new_tcp_failed\n");
        printf("READ_RESULT\t%s\tok=0\tinternal_error\tmodbus_new_tcp_failed\n", request_id);
        fflush(stdout);
        return;
    }

    modbus_set_slave(ctx, unit_id);

    if(modbus_connect(ctx) == -1) {
        fprintf(stderr, "READ connect_failed: %s\n", modbus_strerror(errno));
        printf("READ_RESULT\t%s\tok=0\tconnect_failed\t%s\n",
               request_id, modbus_strerror(errno));
        fflush(stdout);
        modbus_free(ctx);
        return;
    }

    uint16_t *tab = (uint16_t *)malloc(count * sizeof(uint16_t));
    if(tab == NULL) {
        fprintf(stderr, "READ malloc_failed\n");
        printf("READ_RESULT\t%s\tok=0\tinternal_error\tmalloc_failed\n", request_id);
        fflush(stdout);
        modbus_close(ctx);
        modbus_free(ctx);
        return;
    }

    int rc = modbus_read_registers(ctx, reg_addr, count, tab);
    if(rc == -1) {
        fprintf(stderr, "READ read_failed: %s\n", modbus_strerror(errno));
        printf("READ_RESULT\t%s\tok=0\tread_failed\t%s\n",
               request_id, modbus_strerror(errno));
    } else {
        fprintf(stderr, "READ done: host=%s port=%d unit=%d addr=%d count=%d ok=%d\n",
                host, port, unit_id, reg_addr, count, rc);
        printf("READ_RESULT\t%s\tok=1\tOK", request_id);
        for(int j = 0; j < rc; j++)
            printf("\t%u", (unsigned)tab[j]);
        printf("\n");
    }
    fflush(stdout);

    free(tab);
    modbus_close(ctx);
    modbus_free(ctx);
}

/* ── Interactive mode (stdin/stdout) ─────────────────────────────────── */

static int run_interactive(void)
{
    printf("READY\n");
    fflush(stdout);

    char line[MAX_LINE_LEN];
    while(fgets(line, sizeof(line), stdin) != NULL) {
        strip_newline(line);
        if(line[0] == '\0') continue;
        if(strcmp(line, "QUIT") == 0) return 0;
        if(strncmp(line, "WRITE\t", 6) == 0) {
            handle_write_command(line);
            continue;
        }
        if(strncmp(line, "READ\t", 5) == 0) {
            handle_read_command(line);
            continue;
        }
        printf("ERROR\tunknown_command\n");
        fflush(stdout);
    }
    return 0;
}

/* ── Polling mode (CLI args) ────────────────────────────────────────── */

static int run_polling(int argc, char **argv)
{
    const char *host = argv[1];
    int port = atoi(argv[2]);
    int unit_id = atoi(argv[3]);
    int reg_addr = atoi(argv[4]);
    int reg_count = atoi(argv[5]);
    int interval_ms = atoi(argv[6]);
    int total_count = atoi(argv[7]);

    if(reg_count <= 0 || total_count <= 0) {
        fprintf(stderr, "ERROR: reg_count and count must be positive\n");
        return 1;
    }

    modbus_t *ctx = modbus_new_tcp(host, port);
    if(ctx == NULL) {
        fprintf(stderr, "ERROR: modbus_new_tcp failed\n");
        return 1;
    }

    modbus_set_slave(ctx, unit_id);

    if(modbus_connect(ctx) == -1) {
        fprintf(stderr, "ERROR: connect: %s\n", modbus_strerror(errno));
        modbus_free(ctx);
        return 1;
    }

    uint16_t *tab = (uint16_t *)malloc(reg_count * sizeof(uint16_t));
    if(tab == NULL) {
        fprintf(stderr, "ERROR: malloc failed\n");
        modbus_close(ctx);
        modbus_free(ctx);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    int ok = 0, err = 0;
    for(int i = 0; i < total_count; i++) {
        int rc = modbus_read_registers(ctx, reg_addr, reg_count, tab);
        if(rc == -1) {
            fprintf(stderr, "ERROR: read at %d: %s\n", i, modbus_strerror(errno));
            err++;
        } else {
            printf("SAMPLE");
            for(int j = 0; j < rc; j++)
                printf("\t%d", tab[j]);
            printf("\n");
            ok++;
        }
        fflush(stdout);
        if(i < total_count - 1)
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

static void print_version(void)
{
    printf("modbus_tcp_polling_runner 1.2.0\n");
    printf("protocol: stdin/stdout polling + write + read (FC03/FC06)\n");
    printf("stdin commands: WRITE, READ, QUIT\n");
    printf("stdout prefixes: READY, WRITE_RESULT, READ_RESULT, ERROR, SAMPLE, BATCH, SUMMARY, DONE\n");
}

/* ── Entry point ────────────────────────────────────────────────────── */

int main(int argc, char **argv)
{
    if(argc == 2 && (strcmp(argv[1], "--version") == 0 || strcmp(argv[1], "-v") == 0)) {
        print_version();
        return 0;
    }
    if(argc == 1) {
        return run_interactive();
    }
    if(argc != 8) {
        fprintf(stderr, "Usage: %s <host> <port> <unit_id> <reg_addr> <reg_count> <interval_ms> <count>\n",
                argv[0]);
        fprintf(stderr, "   or: %s [--version|-v]\n", argv[0]);
        return 1;
    }
    return run_polling(argc, argv);
}
