#define _POSIX_C_SOURCE 199309L

#include <libiec61850/iec61850_client.h>
#include <libiec61850/iec61850_common.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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
    size_t i, j = 0;
    for (i = 0; input[i] != '\0' && j + 1 < output_size; i++) {
        char ch = input[i];
        if (ch == '\t' || ch == '\n' || ch == '\r')
            ch = ' ';
        output[j++] = ch;
    }
    output[j] = '\0';
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

int main(int argc, char **argv) {
    if (argc != 11) {
        fprintf(stderr,
                "Usage: %s <host> <port> <ied_name> <ld_name> <ln_class> <do_name> <da_name> <fc> <interval_ms> <count>\n"
                "  fc: ST MX SP SV CF DC SG SE SR OR BL EX CO US MS RP BR LG GO (or NONE)\n",
                argv[0]);
        return 2;
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    const char *ied_name = argv[3];
    const char *ld_name = argv[4];
    const char *ln_class = argv[5];
    const char *do_name = argv[6];
    const char *da_name = argv[7];
    const char *fc_str = argv[8];
    int interval_ms = atoi(argv[9]);
    int count = atoi(argv[10]);

    if (port <= 0 || interval_ms <= 0 || count <= 0) {
        fprintf(stderr, "Invalid numeric arguments\n");
        return 2;
    }

    /* Parse functional constraint */
    FunctionalConstraint fc = IEC61850_FC_NONE;
    if (strcmp(fc_str, "NONE") != 0) {
        fc = FunctionalConstraint_fromString(fc_str);
        if (fc == IEC61850_FC_NONE) {
            fprintf(stderr, "Unknown functional constraint: %s\n", fc_str);
            return 2;
        }
    }

    /* Build the object reference:
     * e.g. "simpleIOGenericIO/GGIO1.SPVAl1.stVal" */
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

    /* Emit READY */
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
