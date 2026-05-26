#define _POSIX_C_SOURCE 199309L

#include <arpa/inet.h>
#include <errno.h>
#include <limits.h>
#include <linux/if_packet.h>
#include <net/ethernet.h>
#include <net/if.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static const uint16_t SV_ETHERTYPE = 0x88ba;
static const uint16_t VLAN_ETHERTYPE = 0x8100;
static const uint16_t VLAN_ETHERTYPE_PROVIDER = 0x88a8;

static volatile int g_msg_count = 0;
static volatile int g_msg_errors = 0;

static int64_t monotonic_now_ms(void);
static bool parse_u16_arg(const char *raw, uint16_t *value);
static bool parse_positive_int_arg(const char *raw, int *value);
static bool interface_exists(const char *interface_id);
static int open_capture_socket(const char *interface_id);
static bool parse_frame_app_id(const uint8_t *frame, ssize_t size, uint16_t expected_ethertype, uint16_t *app_id);

static int64_t monotonic_now_ms(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return ((int64_t)ts.tv_sec * 1000LL) + ((int64_t)ts.tv_nsec / 1000000LL);
}

static bool parse_u16_arg(const char *raw, uint16_t *value) {
    char *end = NULL;
    long parsed;

    if (raw == NULL || *raw == '\0' || value == NULL) return false;

    errno = 0;
    parsed = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' || parsed <= 0 || parsed > 0xffffL) {
        return false;
    }

    *value = (uint16_t)parsed;
    return true;
}

static bool parse_positive_int_arg(const char *raw, int *value) {
    char *end = NULL;
    long parsed;

    if (raw == NULL || *raw == '\0' || value == NULL) return false;

    errno = 0;
    parsed = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' || parsed <= 0 || parsed > INT_MAX) {
        return false;
    }

    *value = (int)parsed;
    return true;
}

static bool interface_exists(const char *interface_id) {
    if (interface_id == NULL || *interface_id == '\0') return false;
    return if_nametoindex(interface_id) != 0;
}

static int open_capture_socket(const char *interface_id) {
    int fd = -1;
    int ifindex = 0;
    struct sockaddr_ll bind_addr;
    struct packet_mreq membership;

    ifindex = (int)if_nametoindex(interface_id);
    if (ifindex <= 0) return -1;

    fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (fd < 0) return -1;

    memset(&bind_addr, 0, sizeof(bind_addr));
    bind_addr.sll_family = AF_PACKET;
    bind_addr.sll_ifindex = ifindex;
    bind_addr.sll_protocol = htons(ETH_P_ALL);
    if (bind(fd, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) != 0) {
        close(fd);
        return -1;
    }

    memset(&membership, 0, sizeof(membership));
    membership.mr_ifindex = ifindex;
    membership.mr_type = PACKET_MR_ALLMULTI;
    if (setsockopt(fd, SOL_PACKET, PACKET_ADD_MEMBERSHIP, &membership, sizeof(membership)) != 0) {
        /* Continue without ALLMULTI if unsupported. */
    }

    return fd;
}

static bool parse_frame_app_id(const uint8_t *frame, ssize_t size, uint16_t expected_ethertype, uint16_t *app_id) {
    size_t offset = 12;
    uint16_t ether_type = 0;
    uint16_t network_value = 0;

    if (frame == NULL || app_id == NULL || size < 18) return false;

    memcpy(&network_value, frame + offset, sizeof(network_value));
    ether_type = ntohs(network_value);
    offset += 2;

    if (ether_type == VLAN_ETHERTYPE || ether_type == VLAN_ETHERTYPE_PROVIDER) {
        if (size < 22) return false;
        memcpy(&network_value, frame + 16, sizeof(network_value));
        ether_type = ntohs(network_value);
        offset = 18;
    }

    if (ether_type != expected_ethertype || size < (ssize_t)(offset + 2)) {
        return false;
    }

    memcpy(&network_value, frame + offset, sizeof(network_value));
    *app_id = ntohs(network_value);
    return true;
}

int main(int argc, char **argv) {
    const char *interface_id = NULL;
    uint16_t app_id = 0;
    int duration_s = 0;
    int fd = -1;
    int exit_code = 1;
    int64_t end_ms = 0;
    struct pollfd pollfd = {0};

    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        printf("iec61850_sv_subscriber_runner\tversion=2\n");
        return 0;
    }

    if (argc != 4) {
        fprintf(stderr, "Usage: %s <interface> <app_id> <duration_s>\n", argv[0]);
        return 2;
    }

    interface_id = argv[1];
    if (!interface_exists(interface_id)) {
        fprintf(stderr, "ERROR\tinvalid interface: %s\n", interface_id);
        return 2;
    }

    if (!parse_u16_arg(argv[2], &app_id)) {
        fprintf(stderr, "ERROR\tinvalid app_id: %s\n", argv[2]);
        return 2;
    }

    if (!parse_positive_int_arg(argv[3], &duration_s)) {
        fprintf(stderr, "ERROR\tinvalid duration: %s\n", argv[3]);
        return 2;
    }

    fd = open_capture_socket(interface_id);
    if (fd < 0) {
        fprintf(stderr, "ERROR\tfailed to open raw socket on interface=%s errno=%d\n", interface_id, errno);
        goto cleanup;
    }

    printf("READY\n");
    fflush(stdout);

    pollfd.fd = fd;
    pollfd.events = POLLIN;
    end_ms = monotonic_now_ms() + (int64_t)duration_s * 1000LL;

    while (monotonic_now_ms() < end_ms) {
        uint8_t frame[2048];
        uint16_t observed_app_id = 0;
        int remaining_ms = (int)(end_ms - monotonic_now_ms());
        int wait_ms = remaining_ms > 100 ? 100 : remaining_ms;
        int ready = poll(&pollfd, 1, wait_ms > 0 ? wait_ms : 0);

        if (ready < 0) {
            if (errno == EINTR) continue;
            fprintf(stderr, "ERROR\tpoll failed errno=%d\n", errno);
            goto cleanup;
        }
        if (ready == 0 || (pollfd.revents & POLLIN) == 0) continue;

        ssize_t received = recv(fd, frame, sizeof(frame), 0);
        if (received < 0) {
            if (errno == EINTR || errno == EAGAIN) continue;
            fprintf(stderr, "ERROR\trecv failed errno=%d\n", errno);
            goto cleanup;
        }

        if (!parse_frame_app_id(frame, received, SV_ETHERTYPE, &observed_app_id)) {
            continue;
        }
        if (observed_app_id != app_id) {
            continue;
        }

        g_msg_count++;
        printf("NOTIFY\t%d\t-\t-\t1\t4\t1\t%lld\t1\t1\n",
               g_msg_count,
               (long long)monotonic_now_ms());
        fflush(stdout);
    }

    printf("STREAM_SUMMARY\t%d\t%d\n", g_msg_count, g_msg_errors);
    fflush(stdout);
    printf("DONE\n");
    fflush(stdout);
    exit_code = 0;

cleanup:
    if (fd >= 0) close(fd);
    return exit_code;
}
