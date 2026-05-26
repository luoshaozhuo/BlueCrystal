#define _POSIX_C_SOURCE 200809L

#include <libiec61850/iec61850_server.h>
#include <libiec61850/iec61850_dynamic_model.h>
#include <libiec61850/iec61850_model.h>
#include <libiec61850/hal_thread.h>

#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

/* ── Globals ───────────────────────────────────────────────────────── */

static IedServer g_server = NULL;
static IedModel *g_model = NULL;
static volatile int g_running = 1;

/* Handles to data attributes for periodic updates */
static DataAttribute *g_ind1_stVal = NULL;
static DataAttribute *g_ind2_stVal = NULL;
static DataAttribute *g_anIn1_mag = NULL;
static DataAttribute *g_anIn2_mag = NULL;

/* Handles to writable SP (set point) attributes */
static DataAttribute *g_sp_bool = NULL;
static DataAttribute *g_sp_int32 = NULL;
static DataAttribute *g_sp_float = NULL;
static DataAttribute *g_sp_float64 = NULL;
static DataAttribute *g_sp_string = NULL;
static DataAttribute *g_sp_uint32 = NULL;
static DataAttribute *g_sp_int64 = NULL;

/* ════════════════════════════════════════════════════════════════════ */

static void sigint_handler(int signum) {
    (void)signum;
    g_running = 0;
}

/* ════════════════════════════════════════════════════════════════════ */

static IedModel *create_data_model(void) {
    IedModel *model = IedModel_create("Simulator");
    if (model == NULL) return NULL;

    /* ── Logical Device (use functional naming so MMS domain = "Simulator") ── */
    LogicalDevice *ld = LogicalDevice_createEx("Simulator", model, "Simulator");
    if (ld == NULL) goto fail;

    /* ── LLN0 (mandatory) ──────────────────────────────────────── */
    LogicalNode *lln0 = LogicalNode_create("LLN0", ld);
    if (lln0 == NULL) goto fail;

    /* ── GGIO1 ─────────────────────────────────────────────────── */
    LogicalNode *ggio1 = LogicalNode_create("GGIO1", ld);
    if (ggio1 == NULL) goto fail;

    /* Ind1: Boolean indicator */
    DataObject *ind1 = DataObject_create("Ind1", (ModelNode *)ggio1, 0);
    if (ind1 == NULL) goto fail;

    DataAttribute *ind1_stVal = DataAttribute_create(
        "stVal", (ModelNode *)ind1, IEC61850_BOOLEAN, IEC61850_FC_ST,
        TRG_OPT_DATA_CHANGED | TRG_OPT_QUALITY_CHANGED, 0, 0);
    if (ind1_stVal == NULL) goto fail;
    DataAttribute_setValue(ind1_stVal, MmsValue_newBoolean(0));

    DataAttribute *ind1_q = DataAttribute_create(
        "q", (ModelNode *)ind1, IEC61850_QUALITY, IEC61850_FC_ST, 0, 0, 0);
    if (ind1_q == NULL) goto fail;
    DataAttribute_setValue(ind1_q, MmsValue_newBitString(13));

    DataAttribute *ind1_t = DataAttribute_create(
        "t", (ModelNode *)ind1, IEC61850_TIMESTAMP, IEC61850_FC_ST, 0, 0, 0);
    if (ind1_t == NULL) goto fail;
    DataAttribute_setValue(ind1_t, MmsValue_newUtcTime(0));

    /* Ind2: Boolean indicator */
    DataObject *ind2 = DataObject_create("Ind2", (ModelNode *)ggio1, 0);
    if (ind2 == NULL) goto fail;

    DataAttribute *ind2_stVal = DataAttribute_create(
        "stVal", (ModelNode *)ind2, IEC61850_BOOLEAN, IEC61850_FC_ST,
        TRG_OPT_DATA_CHANGED | TRG_OPT_QUALITY_CHANGED, 0, 0);
    if (ind2_stVal == NULL) goto fail;
    DataAttribute_setValue(ind2_stVal, MmsValue_newBoolean(0));

    DataAttribute *ind2_q = DataAttribute_create(
        "q", (ModelNode *)ind2, IEC61850_QUALITY, IEC61850_FC_ST, 0, 0, 0);
    if (ind2_q == NULL) goto fail;
    DataAttribute_setValue(ind2_q, MmsValue_newBitString(13));

    DataAttribute *ind2_t = DataAttribute_create(
        "t", (ModelNode *)ind2, IEC61850_TIMESTAMP, IEC61850_FC_ST, 0, 0, 0);
    if (ind2_t == NULL) goto fail;
    DataAttribute_setValue(ind2_t, MmsValue_newUtcTime(0));

    /* AnIn1: 32-bit integer analog input */
    DataObject *anIn1 = DataObject_create("AnIn1", (ModelNode *)ggio1, 0);
    if (anIn1 == NULL) goto fail;

    DataAttribute *anIn1_mag = DataAttribute_create(
        "mag", (ModelNode *)anIn1, IEC61850_INT32, IEC61850_FC_MX,
        TRG_OPT_DATA_CHANGED | TRG_OPT_QUALITY_CHANGED, 0, 0);
    if (anIn1_mag == NULL) goto fail;
    DataAttribute_setValue(anIn1_mag, MmsValue_newIntegerFromInt32(0));

    DataAttribute *anIn1_q = DataAttribute_create(
        "q", (ModelNode *)anIn1, IEC61850_QUALITY, IEC61850_FC_MX, 0, 0, 0);
    if (anIn1_q == NULL) goto fail;
    DataAttribute_setValue(anIn1_q, MmsValue_newBitString(13));

    DataAttribute *anIn1_t = DataAttribute_create(
        "t", (ModelNode *)anIn1, IEC61850_TIMESTAMP, IEC61850_FC_MX, 0, 0, 0);
    if (anIn1_t == NULL) goto fail;
    DataAttribute_setValue(anIn1_t, MmsValue_newUtcTime(0));

    /* ── SP (Set Point) writable attributes ───────────────────────── */
    /* SPCtrl1: Boolean set point (writable via MMS direct write) */
    DataObject *spCtrl1 = DataObject_create("SPCtrl1", (ModelNode *)ggio1, 0);
    if (spCtrl1 == NULL) goto fail;

    g_sp_bool = DataAttribute_create(
        "setVal", (ModelNode *)spCtrl1, IEC61850_BOOLEAN, IEC61850_FC_SP,
        TRG_OPT_DATA_CHANGED, 0, 0);
    if (g_sp_bool == NULL) goto fail;
    DataAttribute_setValue(g_sp_bool, MmsValue_newBoolean(0));

    DataAttribute *spCtrl1_q = DataAttribute_create(
        "q", (ModelNode *)spCtrl1, IEC61850_QUALITY, IEC61850_FC_SP, 0, 0, 0);
    if (spCtrl1_q == NULL) goto fail;
    DataAttribute_setValue(spCtrl1_q, MmsValue_newBitString(13));

    /* SPCtrl2: INT32 set point (writable via MMS direct write) */
    DataObject *spCtrl2 = DataObject_create("SPCtrl2", (ModelNode *)ggio1, 0);
    if (spCtrl2 == NULL) goto fail;

    g_sp_int32 = DataAttribute_create(
        "setVal", (ModelNode *)spCtrl2, IEC61850_INT32, IEC61850_FC_SP,
        TRG_OPT_DATA_CHANGED, 0, 0);
    if (g_sp_int32 == NULL) goto fail;
    DataAttribute_setValue(g_sp_int32, MmsValue_newIntegerFromInt32(0));

    DataAttribute *spCtrl2_q = DataAttribute_create(
        "q", (ModelNode *)spCtrl2, IEC61850_QUALITY, IEC61850_FC_SP, 0, 0, 0);
    if (spCtrl2_q == NULL) goto fail;
    DataAttribute_setValue(spCtrl2_q, MmsValue_newBitString(13));

    /* SPCtrl3: FLOAT32 set point (writable via MMS direct write) */
    DataObject *spCtrl3 = DataObject_create("SPCtrl3", (ModelNode *)ggio1, 0);
    if (spCtrl3 == NULL) goto fail;

    g_sp_float = DataAttribute_create(
        "setVal", (ModelNode *)spCtrl3, IEC61850_FLOAT32, IEC61850_FC_SP,
        TRG_OPT_DATA_CHANGED, 0, 0);
    if (g_sp_float == NULL) goto fail;
    DataAttribute_setValue(g_sp_float, MmsValue_newFloat(0.0f));

    DataAttribute *spCtrl3_q = DataAttribute_create(
        "q", (ModelNode *)spCtrl3, IEC61850_QUALITY, IEC61850_FC_SP, 0, 0, 0);
    if (spCtrl3_q == NULL) goto fail;
    DataAttribute_setValue(spCtrl3_q, MmsValue_newBitString(13));

    /* SPCtrl4: FLOAT64 set point (writable via MMS direct write) */
    DataObject *spCtrl4 = DataObject_create("SPCtrl4", (ModelNode *)ggio1, 0);
    if (spCtrl4 == NULL) goto fail;

    g_sp_float64 = DataAttribute_create(
        "setVal", (ModelNode *)spCtrl4, IEC61850_FLOAT64, IEC61850_FC_SP,
        TRG_OPT_DATA_CHANGED, 0, 0);
    if (g_sp_float64 == NULL) goto fail;
    DataAttribute_setValue(g_sp_float64, MmsValue_newDouble(0.0));

    DataAttribute *spCtrl4_q = DataAttribute_create(
        "q", (ModelNode *)spCtrl4, IEC61850_QUALITY, IEC61850_FC_SP, 0, 0, 0);
    if (spCtrl4_q == NULL) goto fail;
    DataAttribute_setValue(spCtrl4_q, MmsValue_newBitString(13));

    /* SPCtrl5: VISIBLE_STRING set point (writable via MMS direct write) */
    DataObject *spCtrl5 = DataObject_create("SPCtrl5", (ModelNode *)ggio1, 0);
    if (spCtrl5 == NULL) goto fail;

    g_sp_string = DataAttribute_create(
        "setVal", (ModelNode *)spCtrl5, IEC61850_VISIBLE_STRING_64, IEC61850_FC_SP,
        TRG_OPT_DATA_CHANGED, 0, 0);
    if (g_sp_string == NULL) goto fail;
    DataAttribute_setValue(g_sp_string, MmsValue_newVisibleString(""));

    DataAttribute *spCtrl5_q = DataAttribute_create(
        "q", (ModelNode *)spCtrl5, IEC61850_QUALITY, IEC61850_FC_SP, 0, 0, 0);
    if (spCtrl5_q == NULL) goto fail;
    DataAttribute_setValue(spCtrl5_q, MmsValue_newBitString(13));

    /* SPCtrl6: UINT32 set point (writable via MMS direct write) */
    DataObject *spCtrl6 = DataObject_create("SPCtrl6", (ModelNode *)ggio1, 0);
    if (spCtrl6 == NULL) goto fail;

    g_sp_uint32 = DataAttribute_create(
        "setVal", (ModelNode *)spCtrl6, IEC61850_INT32U, IEC61850_FC_SP,
        TRG_OPT_DATA_CHANGED, 0, 0);
    if (g_sp_uint32 == NULL) goto fail;
    DataAttribute_setValue(g_sp_uint32, MmsValue_newIntegerFromInt32(0));

    DataAttribute *spCtrl6_q = DataAttribute_create(
        "q", (ModelNode *)spCtrl6, IEC61850_QUALITY, IEC61850_FC_SP, 0, 0, 0);
    if (spCtrl6_q == NULL) goto fail;
    DataAttribute_setValue(spCtrl6_q, MmsValue_newBitString(13));

    /* SPCtrl7: INT64 set point (writable via MMS direct write) */
    DataObject *spCtrl7 = DataObject_create("SPCtrl7", (ModelNode *)ggio1, 0);
    if (spCtrl7 == NULL) goto fail;

    g_sp_int64 = DataAttribute_create(
        "setVal", (ModelNode *)spCtrl7, IEC61850_INT64, IEC61850_FC_SP,
        TRG_OPT_DATA_CHANGED, 0, 0);
    if (g_sp_int64 == NULL) goto fail;
    DataAttribute_setValue(g_sp_int64, MmsValue_newIntegerFromInt64(0));

    DataAttribute *spCtrl7_q = DataAttribute_create(
        "q", (ModelNode *)spCtrl7, IEC61850_QUALITY, IEC61850_FC_SP, 0, 0, 0);
    if (spCtrl7_q == NULL) goto fail;
    DataAttribute_setValue(spCtrl7_q, MmsValue_newBitString(13));

    /* AnIn2: 32-bit float analog input */
    DataObject *anIn2 = DataObject_create("AnIn2", (ModelNode *)ggio1, 0);
    if (anIn2 == NULL) goto fail;

    DataAttribute *anIn2_mag = DataAttribute_create(
        "mag", (ModelNode *)anIn2, IEC61850_FLOAT32, IEC61850_FC_MX,
        TRG_OPT_DATA_CHANGED | TRG_OPT_QUALITY_CHANGED, 0, 0);
    if (anIn2_mag == NULL) goto fail;
    DataAttribute_setValue(anIn2_mag, MmsValue_newFloat(0.0f));

    DataAttribute *anIn2_q = DataAttribute_create(
        "q", (ModelNode *)anIn2, IEC61850_QUALITY, IEC61850_FC_MX, 0, 0, 0);
    if (anIn2_q == NULL) goto fail;
    DataAttribute_setValue(anIn2_q, MmsValue_newBitString(13));

    DataAttribute *anIn2_t = DataAttribute_create(
        "t", (ModelNode *)anIn2, IEC61850_TIMESTAMP, IEC61850_FC_MX, 0, 0, 0);
    if (anIn2_t == NULL) goto fail;
    DataAttribute_setValue(anIn2_t, MmsValue_newUtcTime(0));

    /* ── Data Set "Events" under LLN0 ───────────────────────────── */
    DataSet *ds = DataSet_create("Events", lln0);
    if (ds == NULL) goto fail;

    /* Add FCDA entries (MMS variable path format using $ as separator, including FC) */
    DataSetEntry *entry1 = DataSetEntry_create(ds, "GGIO1$ST$Ind1$stVal", -1, NULL);
    if (entry1 == NULL) goto fail;

    DataSetEntry *entry2 = DataSetEntry_create(ds, "GGIO1$ST$Ind2$stVal", -1, NULL);
    if (entry2 == NULL) goto fail;

    DataSetEntry *entry3 = DataSetEntry_create(ds, "GGIO1$MX$AnIn1$mag", -1, NULL);
    if (entry3 == NULL) goto fail;

    /* ── Report Control Block under LLN0 ────────────────────────── */
    /* trgOps: dchg=1, qchg=2, dupd=4, integrity=8, gi=16 */
    ReportControlBlock *rcb = ReportControlBlock_create(
        "EventsRCB01", lln0,
        "Simulator/LLN0.RP.EventsRCB01", /* rptId */
        false,                            /* isBuffered (URCB) */
        "Events",          /* dataSet name (simple, not full ref) */
        1,                                /* confRev */
        TRG_OPT_DATA_CHANGED | TRG_OPT_QUALITY_CHANGED |
            TRG_OPT_DATA_UPDATE | TRG_OPT_INTEGRITY | TRG_OPT_GI,
        RPT_OPT_SEQ_NUM | RPT_OPT_TIME_STAMP |
            RPT_OPT_REASON_FOR_INCLUSION | RPT_OPT_DATA_SET | RPT_OPT_CONF_REV,
        0,      /* bufTm */
        10000   /* intgPd = 10s */
    );
    if (rcb == NULL) goto fail;

    /* ── GOOSE Control Block under LLN0 ─────────────────────────── */
    GSEControlBlock *gcb = GSEControlBlock_create(
        "gcbEvents", lln0,
        "Simulator/LLN0.gcbEvents",
        "Events",          /* dataSet name (simple, not full ref) */
        1,
        false,
        100,    /* minTime (ms) */
        1000    /* maxTime (ms) */
    );
    if (gcb == NULL) goto fail;

    /* Set GOOSE PhyComAddress */
    {
        uint8_t dst_mac[6] = {0x01, 0x0C, 0xCD, 0x01, 0x00, 0x01};
        PhyComAddress *phy = PhyComAddress_create(4, 0, 0x0001, dst_mac);
        if (phy != NULL) {
            GSEControlBlock_addPhyComAddress(gcb, phy);
        }
    }

    /* Store handles for periodic updates (const-cast for DataAttribute_setValue) */
    g_ind1_stVal = ind1_stVal;
    g_ind2_stVal = ind2_stVal;
    g_anIn1_mag = anIn1_mag;
    g_anIn2_mag = anIn2_mag;

    return model;

fail:
    IedModel_destroy(model);
    return NULL;
}

/* ════════════════════════════════════════════════════════════════════ */

static void *periodic_update_thread(void *parameter) {
    (void)parameter;
    int counter = 0;

    while (g_running) {
        Thread_sleep(1000);

        if (g_server == NULL) continue;

        IedServer_lockDataModel(g_server);

        /* Toggle Ind1 every second */
        bool ind1_val = (counter % 2 == 0);
        IedServer_updateBooleanAttributeValue(g_server, g_ind1_stVal, ind1_val);

        /* Toggle Ind2 every 2 seconds */
        bool ind2_val = ((counter / 2) % 2 == 0);
        IedServer_updateBooleanAttributeValue(g_server, g_ind2_stVal, ind2_val);

        /* Ramp AnIn1 */
        int32_t anIn1_val = (counter % 100) * 10;
        IedServer_updateInt32AttributeValue(g_server, g_anIn1_mag, anIn1_val);

        /* Vary AnIn2 */
        float anIn2_val = 100.0f + 50.0f * (float)(counter % 360);
        IedServer_updateFloatAttributeValue(g_server, g_anIn2_mag, anIn2_val);

        IedServer_unlockDataModel(g_server);

        counter++;
    }

    return NULL;
}

/* ════════════════════════════════════════════════════════════════════ */

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <port>\n", argv[0]);
        return 2;
    }

    int port = atoi(argv[1]);
    if (port <= 0) {
        fprintf(stderr, "Invalid port\n");
        return 2;
    }

    /* Suppress library stdout diagnostics during server setup */
    fflush(stdout);
    int saved_stdout = dup(STDOUT_FILENO);
    if (saved_stdout >= 0) {
        dup2(STDERR_FILENO, STDOUT_FILENO);
    }

    /* Create data model */
    g_model = create_data_model();
    if (g_model == NULL) {
        if (saved_stdout >= 0) close(saved_stdout);
        fprintf(stderr, "Failed to create data model\n");
        return 1;
    }

    /* Create server config */
    IedServerConfig cfg = IedServerConfig_create();
    if (cfg == NULL) {
        if (saved_stdout >= 0) close(saved_stdout);
        fprintf(stderr, "Failed to create server config\n");
        IedModel_destroy(g_model);
        return 1;
    }

    IedServerConfig_setReportBufferSize(cfg, 10000);
    IedServerConfig_setMaxMmsConnections(cfg, 10);

    /* Create server */
    g_server = IedServer_createWithConfig(g_model, NULL, cfg);
    if (g_server == NULL) {
        if (saved_stdout >= 0) close(saved_stdout);
        fprintf(stderr, "Failed to create IedServer\n");
        IedServerConfig_destroy(cfg);
        IedModel_destroy(g_model);
        return 1;
    }

    /* Configure server identity */
    IedServer_setServerIdentity(g_server, "Whale", "Simulator", "1.0.0");

    /* Start server (threaded mode) */
    IedServer_start(g_server, port);

    if (!IedServer_isRunning(g_server)) {
        if (saved_stdout >= 0) close(saved_stdout);
        fprintf(stderr, "IedServer failed to start\n");
        IedServer_destroy(g_server);
        IedServerConfig_destroy(cfg);
        IedModel_destroy(g_model);
        return 1;
    }

    /* Enable GOOSE publishing */
    IedServer_enableGoosePublishing(g_server);

    /* Don't restore stdout — keep all library diagnostics going to stderr.
     * Write protocol lines (READY/DONE) directly to saved_stdout fd so
     * that library thread prints like "IED_SERVER: server thread started!"
     * never pollute the stdout protocol stream. */
    if (saved_stdout >= 0) {
        dprintf(saved_stdout, "READY\n");
        fflush(NULL);
    }

    /* Install signal handler */
    signal(SIGINT, sigint_handler);
    signal(SIGTERM, sigint_handler);

    /* Start periodic update thread */
    Thread update_thread = Thread_create(periodic_update_thread, NULL, false);
    if (update_thread != NULL) {
        Thread_start(update_thread);
    }

    /* Wait for shutdown signal */
    while (g_running) {
        Thread_sleep(100);
    }

    /* Cleanup */
    if (update_thread != NULL) {
        Thread_destroy(update_thread);
    }

    IedServer_stop(g_server);
    IedServer_destroy(g_server);
    IedServerConfig_destroy(cfg);
    IedModel_destroy(g_model);

    if (saved_stdout >= 0) {
        dprintf(saved_stdout, "DONE\n");
        fflush(NULL);
        close(saved_stdout);
    }

    return 0;
}
