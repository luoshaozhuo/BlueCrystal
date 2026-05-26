#define _POSIX_C_SOURCE 199309L

#include <libiec61850/iec61850_client.h>
#include <libiec61850/iec61850_common.h>

#include <errno.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_LINE_LEN 8192
#define MAX_VALUE_TEXT_LEN 512
#define MAX_STATUS_TEXT_LEN 64

static int64_t monotonic_now_us(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return ((int64_t)ts.tv_sec * 1000000LL) + ((int64_t)ts.tv_nsec / 1000LL);
}

static double monotonic_now_s(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0.0;
    }
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void millisleep(uint32_t ms) {
    struct timespec req;
    req.tv_sec = ms / 1000;
    req.tv_nsec = (long)(ms % 1000) * 1000000L;
    struct timespec rem;
    while (nanosleep(&req, &rem) != 0 && errno == EINTR) {
        req = rem;
    }
}

static void sanitize_field(const char *input, char *output, size_t output_size) {
    if (output_size == 0) return;
    if (input == NULL || input[0] == '\0') {
        snprintf(output, output_size, "-");
        return;
    }
    size_t i, j = 0;
    for (i = 0; input[i] != '\0' && j + 1 < output_size; i++) {
        char ch = input[i];
        if (ch == '\t' || ch == '\n' || ch == '\r')
            ch = ' ';
        output[j++] = ch;
    }
    output[j] = '\0';
}

static void strip_newline(char *line) {
    size_t len = strlen(line);
    while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r')) {
        line[len - 1] = '\0';
        len--;
    }
}

static int split_fields(char *line, char **fields, int max_fields) {
    int count = 0;
    char *cursor = line;
    while (cursor != NULL && count < max_fields) {
        fields[count++] = cursor;
        char *tab = strchr(cursor, '\t');
        if (tab == NULL) {
            break;
        }
        *tab = '\0';
        cursor = tab + 1;
    }
    return count;
}

static void format_mms_value(MmsValue *value, char *buf, size_t buf_size) {
    if (value == NULL) {
        snprintf(buf, buf_size, "-");
        return;
    }
    MmsType t = MmsValue_getType(value);
    switch (t) {
    case MMS_BOOLEAN:
        snprintf(buf, buf_size, "%s", MmsValue_getBoolean(value) ? "true" : "false");
        break;
    case MMS_INTEGER:
    case MMS_UNSIGNED:
        snprintf(buf, buf_size, "%lld", (long long)MmsValue_toInt64(value));
        break;
    case MMS_FLOAT:
        snprintf(buf, buf_size, "%.9g", MmsValue_toDouble(value));
        break;
    case MMS_VISIBLE_STRING:
    case MMS_STRING: {
        const char *s = MmsValue_toString(value);
        if (s == NULL)
            snprintf(buf, buf_size, "-");
        else
            snprintf(buf, buf_size, "%s", s);
        break;
    }
    case MMS_UTC_TIME:
        snprintf(buf, buf_size, "%llu", (unsigned long long)MmsValue_getUtcTimeInMs(value));
        break;
    case MMS_BIT_STRING:
        snprintf(buf, buf_size, "0x%x", MmsValue_getBitStringAsInteger(value));
        break;
    case MMS_OCTET_STRING:
        snprintf(buf, buf_size, "octets(%d)", MmsValue_getOctetStringSize(value));
        break;
    case MMS_ARRAY:
    case MMS_STRUCTURE:
        snprintf(buf, buf_size, "complex(%d)", (int)MmsValue_getArraySize(value));
        break;
    case MMS_DATA_ACCESS_ERROR:
        snprintf(buf, buf_size, "access_error-%d", (int)MmsValue_getDataAccessError(value));
        break;
    default: {
        char tmp[64];
        MmsValue_printToBuffer((MmsValue *)value, tmp, sizeof(tmp));
        sanitize_field(tmp, buf, buf_size);
        break;
    }
    }
}

/* ── Value type helpers for WRITE ───────────────────────────────────── */


static const char *mms_type_name(MmsType t) {
    switch (t) {
    case MMS_BOOLEAN: return "BOOLEAN";
    case MMS_INTEGER: return "INTEGER";
    case MMS_UNSIGNED: return "UNSIGNED";
    case MMS_FLOAT: return "FLOAT";
    case MMS_VISIBLE_STRING: return "VISIBLE_STRING";
    case MMS_STRING: return "STRING";
    case MMS_UTC_TIME: return "UTC_TIME";
    case MMS_BIT_STRING: return "BIT_STRING";
    default: return "UNKNOWN";
    }
}


/* ═══════════════════════════════════════════════════════════════════════
 * Interactive mode (stdin/stdout protocol)
 * ═══════════════════════════════════════════════════════════════════════ */

/* Forward declarations */
static void handle_read_command(char *line);
static void handle_write_command(char *line);

static IedConnection create_and_connect(
    const char *host, int port,
    uint32_t connect_timeout_ms, uint32_t request_timeout_ms,
    IedClientError *error
) {
    IedConnection con = IedConnection_create();
    if (con == NULL) return NULL;

    IedConnection_setConnectTimeout(con, connect_timeout_ms);
    IedConnection_setRequestTimeout(con, request_timeout_ms);

    IedConnection_connect(con, error, host, port);
    if (*error != IED_ERROR_OK) {
        IedConnection_destroy(con);
        return NULL;
    }
    return con;
}

/* Handle one READ command:
 *   READ\t<request_id>\t<host>\t<port>\t<obj_ref>\t<fc>
 * stdout: READ_RESULT\t<request_id>\t<obj_ref>\tok=1\tOK\t<value_type>\t<value>
 *      or: READ_RESULT\t<request_id>\t<obj_ref>\tok=0\t<error>\t<value_type>\t<value>
 */
static void handle_read_command(char *line) {
    char *fields[7] = {0};
    int field_count = split_fields(line, fields, 7);
    if (field_count < 6 || strcmp(fields[0], "READ") != 0) {
        fprintf(stderr, "READ protocol_error: field_count=%d\n", field_count);
        printf("READ_RESULT\t-\t-\tok=0\tprotocol_error\tinvalid_read_command\t-\n");
        fflush(stdout);
        return;
    }

    char request_id[MAX_VALUE_TEXT_LEN];
    char host[MAX_VALUE_TEXT_LEN];
    int port = atoi(fields[3]);
    char obj_ref[MAX_LINE_LEN];
    char fc_str[MAX_LINE_LEN];

    sanitize_field(fields[1], request_id, sizeof(request_id));
    sanitize_field(fields[2], host, sizeof(host));
    sanitize_field(fields[4], obj_ref, sizeof(obj_ref));
    sanitize_field(fields[5], fc_str, sizeof(fc_str));

    if (port <= 0) {
        fprintf(stderr, "READ invalid port: %s\n", fields[3]);
        printf("READ_RESULT\t%s\t%s\tok=0\tinvalid_param\tinvalid_port\t-\n",
               request_id, obj_ref);
        fflush(stdout);
        return;
    }

    FunctionalConstraint fc = IEC61850_FC_NONE;
    if (strcmp(fc_str, "NONE") != 0 && strcmp(fc_str, "-") != 0) {
        fc = FunctionalConstraint_fromString(fc_str);
        if (fc == IEC61850_FC_NONE) {
            fprintf(stderr, "READ unknown FC: %s\n", fc_str);
            printf("READ_RESULT\t%s\t%s\tok=0\tinvalid_param\tunknown_fc\t-\n",
                   request_id, obj_ref);
            fflush(stdout);
            return;
        }
    }

    IedClientError error = IED_ERROR_OK;
    IedConnection con = create_and_connect(host, port, 5000, 5000, &error);
    if (con == NULL) {
        fprintf(stderr, "READ connect_failed: %s\n", IedClientError_toString(error));
        printf("READ_RESULT\t%s\t%s\tok=0\tconnect_failed\t%s\t-\n",
               request_id, obj_ref, IedClientError_toString(error));
        fflush(stdout);
        return;
    }

    MmsValue *val = IedConnection_readObject(con, &error, obj_ref, fc);
    if (error != IED_ERROR_OK || val == NULL) {
        fprintf(stderr, "READ readObject failed: %s\n", IedClientError_toString(error));
        printf("READ_RESULT\t%s\t%s\tok=0\tread_failed\t%s\t-\n",
               request_id, obj_ref, IedClientError_toString(error));
        fflush(stdout);
        IedConnection_close(con);
        IedConnection_destroy(con);
        return;
    }

    char value_buf[MAX_VALUE_TEXT_LEN] = "-";
    format_mms_value(val, value_buf, sizeof(value_buf));
    MmsType val_type = MmsValue_getType(val);
    const char *type_name = mms_type_name(val_type);

    printf("READ_RESULT\t%s\t%s\tok=1\tOK\t%s\t%s\n",
           request_id, obj_ref, type_name, value_buf);
    fflush(stdout);

    MmsValue_delete(val);
    IedConnection_close(con);
    IedConnection_destroy(con);
}

/* Handle one WRITE command:
 *   WRITE\t<request_id>\t<host>\t<port>\t<obj_ref>\t<fc>\t<value_type>\t<value>
 * stdout: WRITE_RESULT\t<request_id>\t<obj_ref>\tok=1\tOK\t<value_type>
 *      or: WRITE_RESULT\t<request_id>\t<obj_ref>\tok=0\t<error>\t<value_type>
 */
static void handle_write_command(char *line) {
    char *fields[9] = {0};
    int field_count = split_fields(line, fields, 9);
    if (field_count < 8 || strcmp(fields[0], "WRITE") != 0) {
        fprintf(stderr, "WRITE protocol_error: field_count=%d\n", field_count);
        printf("WRITE_RESULT\t-\t-\tok=0\tprotocol_error\tinvalid_write_command_format\n");
        fflush(stdout);
        return;
    }

    char request_id[MAX_VALUE_TEXT_LEN];
    char host[MAX_VALUE_TEXT_LEN];
    int port = atoi(fields[3]);
    char obj_ref[MAX_LINE_LEN];
    char fc_str[MAX_LINE_LEN];
    char value_type_str[MAX_LINE_LEN];
    char value_text[MAX_LINE_LEN];

    sanitize_field(fields[1], request_id, sizeof(request_id));
    sanitize_field(fields[2], host, sizeof(host));
    sanitize_field(fields[4], obj_ref, sizeof(obj_ref));
    sanitize_field(fields[5], fc_str, sizeof(fc_str));
    sanitize_field(fields[6], value_type_str, sizeof(value_type_str));
    sanitize_field(fields[7], value_text, sizeof(value_text));

    if (port <= 0) {
        fprintf(stderr, "WRITE invalid port: %s\n", fields[3]);
        printf("WRITE_RESULT\t%s\t%s\tok=0\tinvalid_param\tinvalid_port\n",
               request_id, obj_ref);
        fflush(stdout);
        return;
    }

    FunctionalConstraint fc = IEC61850_FC_NONE;
    if (strcmp(fc_str, "NONE") != 0 && strcmp(fc_str, "-") != 0) {
        fc = FunctionalConstraint_fromString(fc_str);
        if (fc == IEC61850_FC_NONE) {
            fprintf(stderr, "WRITE unknown FC: %s\n", fc_str);
            printf("WRITE_RESULT\t%s\t%s\tok=0\tinvalid_param\tunknown_fc\n",
                   request_id, obj_ref);
            fflush(stdout);
            return;
        }
    }

    /* Create MmsValue based on value_type */
    MmsValue *write_val = NULL;
    if (strcmp(value_type_str, "BOOLEAN") == 0 || strcmp(value_type_str, "bool") == 0) {
        bool v = (strcmp(value_text, "true") == 0 || strcmp(value_text, "1") == 0);
        write_val = MmsValue_newBoolean(v);
    } else if (strcmp(value_type_str, "INT32") == 0 || strcmp(value_type_str, "int32") == 0) {
        int32_t v = (int32_t)strtol(value_text, NULL, 10);
        write_val = MmsValue_newIntegerFromInt32(v);
    } else if (strcmp(value_type_str, "UINT32") == 0 || strcmp(value_type_str, "uint32") == 0) {
        uint32_t v = (uint32_t)strtoul(value_text, NULL, 10);
        write_val = MmsValue_newUnsignedFromUint32(v);
    } else if (strcmp(value_type_str, "INT64") == 0 || strcmp(value_type_str, "int64") == 0) {
        int64_t v = (int64_t)strtoll(value_text, NULL, 10);
        write_val = MmsValue_newIntegerFromInt64(v);
    } else if (strcmp(value_type_str, "FLOAT32") == 0 || strcmp(value_type_str, "float32") == 0 ||
               strcmp(value_type_str, "float") == 0) {
        float v = (float)strtod(value_text, NULL);
        write_val = MmsValue_newFloat(v);
    } else if (strcmp(value_type_str, "FLOAT64") == 0 || strcmp(value_type_str, "float64") == 0 ||
               strcmp(value_type_str, "double") == 0) {
        double v = strtod(value_text, NULL);
        write_val = MmsValue_newDouble(v);
    } else if (strcmp(value_type_str, "VISIBLE_STRING") == 0 || strcmp(value_type_str, "string") == 0) {
        write_val = MmsValue_newVisibleString(value_text);
    } else {
        fprintf(stderr, "WRITE unsupported value_type: %s\n", value_type_str);
        printf("WRITE_RESULT\t%s\t%s\tok=0\tunsupported_type\t%s\n",
               request_id, obj_ref, value_type_str);
        fflush(stdout);
        return;
    }

    if (write_val == NULL) {
        fprintf(stderr, "WRITE failed to create MmsValue\n");
        printf("WRITE_RESULT\t%s\t%s\tok=0\tinternal_error\tcreate_value_failed\n",
               request_id, obj_ref);
        fflush(stdout);
        return;
    }

    IedClientError error = IED_ERROR_OK;
    IedConnection con = create_and_connect(host, port, 5000, 5000, &error);
    if (con == NULL) {
        fprintf(stderr, "WRITE connect_failed: %s\n", IedClientError_toString(error));
        printf("WRITE_RESULT\t%s\t%s\tok=0\tconnect_failed\t%s\n",
               request_id, obj_ref, IedClientError_toString(error));
        fflush(stdout);
        MmsValue_delete(write_val);
        return;
    }

    IedConnection_writeObject(con, &error, obj_ref, fc, write_val);
    MmsValue_delete(write_val);

    char status_buf[MAX_STATUS_TEXT_LEN];
    if (error == IED_ERROR_OK) {
        sanitize_field("OK", status_buf, sizeof(status_buf));
    } else {
        sanitize_field(IedClientError_toString(error), status_buf, sizeof(status_buf));
    }

    fprintf(stderr, "WRITE done: ref=%s fc=%s type=%s value=%s status=%s\n",
            obj_ref, fc_str, value_type_str, value_text,
            error == IED_ERROR_OK ? "OK" : IedClientError_toString(error));

    printf("WRITE_RESULT\t%s\t%s\tok=%d\t%s\t%s\n",
           request_id, obj_ref,
           error == IED_ERROR_OK ? 1 : 0,
           status_buf,
           value_type_str);
    fflush(stdout);

    IedConnection_close(con);
    IedConnection_destroy(con);
}

static int run_interactive_mode(void) {
    printf("READY\n");
    fflush(stdout);

    char line[MAX_LINE_LEN];
    while (fgets(line, sizeof(line), stdin) != NULL) {
        strip_newline(line);
        if (line[0] == '\0') continue;

        if (strcmp(line, "QUIT") == 0) {
            return 0;
        }

        if (strncmp(line, "WRITE\t", 6) == 0) {
            handle_write_command(line);
            continue;
        }

        if (strncmp(line, "READ\t", 5) == 0) {
            handle_read_command(line);
            continue;
        }

        fprintf(stderr, "Unknown command: %s\n", line);
        printf("WRITE_RESULT\t-\t-\tok=0\tunknown_command\t%s\n", line);
        fflush(stdout);
    }
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════
 * CLI polling mode (existing behavior, preserved for capacity tests)
 * ═══════════════════════════════════════════════════════════════════════ */

static int run_cli_polling_mode(
    const char *host, int port,
    const char *ied_name,
    const char *ld_name, const char *ln_class,
    const char *do_name, const char *da_name,
    const char *fc_str,
    int interval_ms, int count
) {
    /* Parse functional constraint */
    FunctionalConstraint fc = IEC61850_FC_NONE;
    if (strcmp(fc_str, "NONE") != 0) {
        fc = FunctionalConstraint_fromString(fc_str);
        if (fc == IEC61850_FC_NONE) {
            fprintf(stderr, "Unknown functional constraint: %s\n", fc_str);
            return 2;
        }
    }

    /* Build the object reference */
    char obj_ref[512];
    int ref_len;
    if (da_name != NULL && strlen(da_name) > 0)
        ref_len = snprintf(obj_ref, sizeof(obj_ref), "%s/%s.%s.%s", ld_name, ln_class, do_name, da_name);
    else
        ref_len = snprintf(obj_ref, sizeof(obj_ref), "%s/%s.%s", ld_name, ln_class, do_name);

    if (ref_len < 0 || (size_t)ref_len >= sizeof(obj_ref)) {
        fprintf(stderr, "Object reference too long\n");
        return 2;
    }

    IedClientError error = IED_ERROR_OK;
    IedConnection con = IedConnection_create();
    if (con == NULL) {
        fprintf(stderr, "Failed to create IedConnection\n");
        return 1;
    }

    IedConnection_setConnectTimeout(con, 5000);
    IedConnection_setRequestTimeout(con, 5000);

    IedConnection_connect(con, &error, host, port);
    if (error != IED_ERROR_OK) {
        fprintf(stderr, "Connect failed: %s\n", IedClientError_toString(error));
        IedConnection_destroy(con);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    int64_t start_us = monotonic_now_us();
    int ok_count = 0;
    int err_count = 0;

    for (int i = 0; i < count; i++) {
        int64_t tick_start_us = monotonic_now_us();

        error = IED_ERROR_OK;
        MmsValue *val = IedConnection_readObject(con, &error, obj_ref, fc);
        int64_t tick_end_us = monotonic_now_us();

        if (error != IED_ERROR_OK || val == NULL) {
            err_count++;
            printf("SAMPLE\terror\t%s\n", IedClientError_toString(error));
            fflush(stdout);
        } else {
            ok_count++;
            char value_buf[1024] = "-";
            format_mms_value(val, value_buf, sizeof(value_buf));

            printf("SAMPLE\t%s\t%s\t%lld\t%lld\n",
                   obj_ref, value_buf,
                   (long long)(tick_start_us - start_us),
                   (long long)(tick_end_us - tick_start_us));
            fflush(stdout);

            MmsValue_delete(val);
        }

        if (i + 1 < count) {
            millisleep((uint32_t)interval_ms);
        }
    }

    int64_t end_us = monotonic_now_us();
    int64_t elapsed_us = end_us - start_us;
    double value_ratio = (count > 0) ? ((double)ok_count / (double)count) : 0.0;

    printf("BATCH\t%d\t%d\t%d\n", count, ok_count, err_count);
    fflush(stdout);

    printf("SUMMARY\t%lld\t%.6f\n", (long long)elapsed_us, value_ratio);
    fflush(stdout);

    printf("DONE\n");
    fflush(stdout);

    IedConnection_close(con);
    IedConnection_destroy(con);
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════
 * Multi-point CLI polling mode
 * ═══════════════════════════════════════════════════════════════════════
 *
 * Per-tick output: SAMPLE\t<point_count>\t<ref1>=<val1>\t<ref2>=<val2>\t<offset_us>\t<duration_us>
 * SUMMARY includes total_values in 3rd field.
 *
 * Called from main() when argc >= 12 and (argc - 8) % 4 == 0.
 * CLI format: <host> <port> <ied_name> <ld_name> <interval_ms> <count> <point_count> [<ln> <do> <da> <fc>]...
 * ═══════════════════════════════════════════════════════════════════════ */

#define MAX_MMS_POINTS 16

static int run_cli_polling_mode_multi(
    const char *host, int port,
    const char *ied_name, const char *ld_name,
    const char * const *ln_classes, const char * const *do_names,
    const char * const *da_names, const char * const *fc_strs,
    int point_count,
    int interval_ms, int count
) {
    (void)ied_name; /* not used for reads */

    if (point_count < 1 || point_count > MAX_MMS_POINTS) {
        fprintf(stderr, "Invalid point_count: %d (max %d)\n",
                point_count, MAX_MMS_POINTS);
        return 2;
    }

    /* Build object references and parse FCs */
    char obj_refs[MAX_MMS_POINTS][512];
    FunctionalConstraint fcs[MAX_MMS_POINTS];

    for (int i = 0; i < point_count; i++) {
        FunctionalConstraint fc = IEC61850_FC_NONE;
        if (fc_strs[i] != NULL && strcmp(fc_strs[i], "NONE") != 0) {
            fc = FunctionalConstraint_fromString(fc_strs[i]);
        }
        fcs[i] = fc;

        if (da_names[i] != NULL && strlen(da_names[i]) > 0) {
            snprintf(obj_refs[i], sizeof(obj_refs[i]), "%s/%s.%s.%s",
                     ld_name, ln_classes[i], do_names[i], da_names[i]);
        } else {
            snprintf(obj_refs[i], sizeof(obj_refs[i]), "%s/%s.%s",
                     ld_name, ln_classes[i], do_names[i]);
        }
    }

    IedClientError error = IED_ERROR_OK;
    IedConnection con = IedConnection_create();
    if (con == NULL) {
        fprintf(stderr, "Failed to create IedConnection\n");
        return 1;
    }

    IedConnection_setConnectTimeout(con, 5000);
    IedConnection_setRequestTimeout(con, 5000);

    IedConnection_connect(con, &error, host, port);
    if (error != IED_ERROR_OK) {
        fprintf(stderr, "Connect failed: %s\n", IedClientError_toString(error));
        IedConnection_destroy(con);
        return 1;
    }

    printf("READY\n");
    fflush(stdout);

    int64_t start_us = monotonic_now_us();
    int ok_count = 0;
    int err_count = 0;
    int total_values = 0;

    for (int i = 0; i < count; i++) {
        int64_t tick_start_us = monotonic_now_us();
        bool tick_ok = true;
        int points_ok = 0;

        printf("SAMPLE\t%d", point_count);

        for (int p = 0; p < point_count; p++) {
            error = IED_ERROR_OK;
            MmsValue *val = IedConnection_readObject(con, &error, obj_refs[p], fcs[p]);

            if (error != IED_ERROR_OK || val == NULL) {
                printf("\t%s=error_%s",
                       obj_refs[p], IedClientError_toString(error));
                if (tick_ok) {
                    tick_ok = false;
                }
            } else {
                char value_buf[1024] = "-";
                format_mms_value(val, value_buf, sizeof(value_buf));
                printf("\t%s=%s", obj_refs[p], value_buf);
                total_values++;
                points_ok++;
                MmsValue_delete(val);
            }
        }

        int64_t tick_end_us = monotonic_now_us();
        printf("\t%lld\t%lld\n",
               (long long)(tick_start_us - start_us),
               (long long)(tick_end_us - tick_start_us));
        fflush(stdout);

        if (tick_ok) ok_count++;
        if (!tick_ok) err_count++;

        if (i + 1 < count) {
            millisleep((uint32_t)interval_ms);
        }
    }

    int64_t end_us = monotonic_now_us();
    int64_t elapsed_us = end_us - start_us;
    double value_ratio = (count > 0) ? ((double)ok_count / (double)count) : 0.0;

    printf("BATCH\t%d\t%d\t%d\n", count, ok_count, err_count);
    fflush(stdout);

    printf("SUMMARY\t%lld\t%.6f\t%d\n",
           (long long)elapsed_us, value_ratio, total_values);
    fflush(stdout);

    printf("DONE\n");
    fflush(stdout);

    IedConnection_close(con);
    IedConnection_destroy(con);
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════
 * Entry point
 * ═══════════════════════════════════════════════════════════════════════ */

static void print_version(void) {
    printf("iec61850_mms_client_runner 1.2.0\n");
    printf("protocol: stdin/stdout interactive + CLI polling\n");
    printf("stdin commands: READ, WRITE, QUIT\n");
    printf("stdout prefixes: READY, READ_RESULT, WRITE_RESULT\n");
}

int main(int argc, char **argv) {
    if (argc == 2 && (strcmp(argv[1], "--version") == 0 || strcmp(argv[1], "-v") == 0)) {
        print_version();
        return 0;
    }

    /* Interactive mode: no arguments */
    if (argc == 1) {
        return run_interactive_mode();
    }

    /* Legacy CLI polling mode: <host> <port> <ied_name> <ld_name> <ln_class> <do_name> <da_name> <fc> <interval_ms> <count> */
    if (argc == 11) {
        return run_cli_polling_mode(
            argv[1], atoi(argv[2]),
            argv[3], argv[4], argv[5],
            argv[6], argv[7], argv[8],
            atoi(argv[9]), atoi(argv[10])
        );
    }

    /* Multi-point CLI polling:
     * <host> <port> <ied_name> <ld_name> <interval_ms> <count> <point_count> [<ln> <do> <da> <fc>]...
     * argc = 8 + point_count * 4
     */
    if (argc >= 12 && ((argc - 8) % 4) == 0) {
        int point_count = (argc - 8) / 4;
        int argv_count = atoi(argv[7]);

        if (argv_count != point_count) {
            fprintf(stderr, "Point count mismatch: cli=%d, arg_count=%d\n",
                    argv_count, point_count);
            return 2;
        }

        if (point_count > MAX_MMS_POINTS) {
            fprintf(stderr, "Too many points: %d (max %d)\n",
                    point_count, MAX_MMS_POINTS);
            return 2;
        }

        const char *ln_classes[MAX_MMS_POINTS];
        const char *do_names[MAX_MMS_POINTS];
        const char *da_names[MAX_MMS_POINTS];
        const char *fc_strs[MAX_MMS_POINTS];

        for (int i = 0; i < point_count; i++) {
            ln_classes[i] = argv[8 + i * 4];
            do_names[i] = argv[8 + i * 4 + 1];
            da_names[i] = argv[8 + i * 4 + 2];
            fc_strs[i] = argv[8 + i * 4 + 3];
        }

        return run_cli_polling_mode_multi(
            argv[1], atoi(argv[2]),
            argv[3], argv[4],
            ln_classes, do_names, da_names, fc_strs,
            point_count,
            atoi(argv[5]), atoi(argv[6])
        );
    }

    fprintf(stderr,
            "Usage: %s [--version|-v]\n"
            "   or: %s <host> <port> <ied_name> <ld_name> <ln_class> <do_name> <da_name> <fc> <interval_ms> <count>\n"
            "   or: %s <host> <port> <ied_name> <ld_name> <interval_ms> <count> <point_count> [<ln> <do> <da> <fc>]...\n",
            argv[0], argv[0], argv[0]);
    return 2;
}
