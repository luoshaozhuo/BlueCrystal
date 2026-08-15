<template>
  <div class="single-load-page">
    <div class="section-top">
      <OverviewTurbineSelectCard
        v-model="selectedTurbine"
        :options="turbineOptions"
        :loading="loading.summary"
      />
      <OverviewTurbineInfoCard :items="turbineInfoItems" :loading="loading.summary" />
      <OverviewMetricCard
        v-for="item in kpiList"
        :key="item.title"
        :title="item.title"
        :value="item.value"
        :footnote="item.footnote"
        :trend-symbol="item.trend"
        tone="negative"
        :loading="loading.summary"
      />
    </div>

    <div class="section-fatigue">
      <div class="analysis-section-shell">
        <a-tabs
          v-model:active-key="localMetric"
          class="analysis-section-tabs"
          size="mini"
          type="text"
          :hide-content="true"
        >
          <a-tab-pane
            v-for="item in metricTabs"
            :key="item.value"
            :title="item.label"
          />
        </a-tabs>

        <div class="analysis-section-content">
          <div class="load-cycle-structure-row">
            <a-card class="analysis-panel analysis-panel-shell" :bordered="false" :loading="loading.structure">
              <AmplitudeStructureComparison
                :data="currentMetricConfig.structureData"
              />
            </a-card>

            <a-card class="analysis-panel analysis-panel-shell" :bordered="false" :loading="loading.structure">
              <LoadCycleMigrationHeatmap
                :data="currentMetricConfig.migrationData"
              />
            </a-card>

            <a-card class="analysis-panel analysis-panel-shell" :bordered="false" :loading="loading.structure">
              <HighAmplitudeRiskComparison
                :data="currentMetricConfig.riskData"
                :high-amplitude-bins="highAmplitudeBins"
              />
            </a-card>
          </div>

          <div class="shock-analysis-row">
            <a-card class="analysis-panel shock-analysis-panel" :bordered="false" :loading="loading.evidence">
              <RmsImprovementOverview
                :data="currentEvidence.rmsSeries"
                :unit="currentEvidence.unit"
              />
            </a-card>

            <a-card class="analysis-panel shock-analysis-panel" :bordered="false" :loading="loading.evidence">
              <PeakQuantileEvidence
                :data="currentEvidence.peakQqEvidence"
                :unit="currentEvidence.unit"
              />
            </a-card>

            <a-card class="analysis-panel shock-analysis-panel" :bordered="false" :loading="loading.evidence">
              <ImprovementStabilityStats :data="currentEvidence.stabilitySeries" />
            </a-card>

            <a-card class="analysis-panel shock-analysis-panel" :bordered="false" :loading="loading.evidence">
              <EnergySpectrumComparison :data="currentEvidence.energySpectrum" />
            </a-card>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
  import OverviewMetricCard from '@/components/overview-metric-card/index.vue';
  import OverviewTurbineInfoCard from '@/components/overview-turbine-info-card/index.vue';
  import OverviewTurbineSelectCard from '@/components/overview-turbine-select-card/index.vue';
  import {
    createLoadMitigationMetricConfigMap,
    loadMitigationHighAmplitudeBins,
    loadMitigationKpiList,
    loadMitigationTurbineMeta,
    loadMitigationTurbineOptions,
    type LoadMetricKey,
    type LoadMitigationMetricConfig,
  } from '@/api/local-data/load-mitigation';
  import AmplitudeStructureComparison from './components/AmplitudeStructureComparison.vue';
  import EnergySpectrumComparison from './components/EnergySpectrumComparison.vue';
  import HighAmplitudeRiskComparison from './components/HighAmplitudeRiskComparison.vue';
  import ImprovementStabilityStats from './components/ImprovementStabilityStats.vue';
  import LoadCycleMigrationHeatmap from './components/LoadCycleMigrationHeatmap.vue';
  import PeakQuantileEvidence from './components/PeakQuantileEvidence.vue';
  import RmsImprovementOverview from './components/RmsImprovementOverview.vue';

  const loadMitigationMetricCopy: Record<LoadMetricKey, string> = {
    bladeRootMoment: '叶根弯矩',
    nacelleAcceleration: '机舱振动',
    generatorTorque: '发电机扭矩',
  };

  const loadMitigationKpiCopy: Record<
    string,
    { title: string; footnote: string }
  > = {
    blade_root_fatigue: { title: '叶根疲劳改善', footnote: '基于叶根弯矩' },
    drive_train_fatigue: { title: '传动链疲劳改善', footnote: '基于发电机扭矩' },
    nacelle_fatigue: { title: '机舱疲劳改善', footnote: '基于双向加速度' },
    nacelle_vibration_rms: { title: '机舱振动 RMS', footnote: '机舱合成加速度均方根' },
    nacelle_vibration_peak: { title: '机舱振动峰值', footnote: '机舱合成加速度95分位数' },
    blade_root_moment_rms: { title: '叶根弯矩 RMS', footnote: '叶根弯矩均方根' },
    blade_root_moment_peak: { title: '叶根弯矩峰值', footnote: '叶根弯矩5分位数' },
    generator_torque_rms: { title: '发电机扭矩 RMS', footnote: '发电机扭矩均方根' },
    generator_torque_peak: { title: '发电机扭矩峰值', footnote: '发电机扭矩5分位数' },
  };

  const selectedTurbine = ref(loadMitigationTurbineOptions[0]?.value ?? 'WT-07');
  const loading = reactive({
    summary: true,
    structure: true,
    evidence: true,
  });
  const turbineOptions = loadMitigationTurbineOptions;
  const turbineMeta = reactive({ ...loadMitigationTurbineMeta });
  const kpiList = reactive(
    loadMitigationKpiList.map((item) => ({
      ...item,
      title: loadMitigationKpiCopy[item.key]?.title ?? item.key,
      footnote: loadMitigationKpiCopy[item.key]?.footnote ?? '',
    })),
  );
  const highAmplitudeBins = loadMitigationHighAmplitudeBins;

  const turbineInfoItems = computed(() => [
    { label: '风机型号', value: turbineMeta.model },
    { label: '投运日期', value: turbineMeta.commissionedAt },
    { label: '优化节点', value: turbineMeta.optimizedAt },
    { label: '分析窗口', value: `近 ${turbineMeta.windowDays} 天` },
  ]);

  const emptyMetricConfig: LoadMitigationMetricConfig = {
    migrationData: {
      meanBins: [],
      amplitudeBins: [],
      baseline: [],
      optimized: [],
    },
    structureData: {
      meanBins: [],
      amplitudeBins: [],
      baseline: [],
      optimized: [],
    },
    riskData: {
      meanBins: [],
      amplitudeBins: [],
      baseline: [],
      optimized: [],
    },
    evidence: {
      unit: '',
      rmsSeries: [],
      peakQqEvidence: {
        beforePeaks: [],
        afterPeaks: [],
      },
      stabilitySeries: [],
      energySpectrum: [],
    },
  };

  const activeLoadMetric = ref<LoadMetricKey>('bladeRootMoment');
  const metricConfigMap = computed<Record<LoadMetricKey, LoadMitigationMetricConfig>>(
    () => createLoadMitigationMetricConfigMap(),
  );
  const metricTabs = computed(() =>
    Object.entries(metricConfigMap.value).map(([value]) => ({
      value,
      label: loadMitigationMetricCopy[value as LoadMetricKey] ?? value,
    })),
  );

  const localMetric = ref(activeLoadMetric.value);

  watch(activeLoadMetric, (value) => {
    localMetric.value = value;
  });

  watch(localMetric, (value, previousValue) => {
    if (value === previousValue) return;
    activeLoadMetric.value = value as LoadMetricKey;
    restartRotation();
  });

  const currentMetricConfig = computed(() => {
    const fallbackKey = metricTabs.value[0]?.value as LoadMetricKey | undefined;
    const activeKey =
      localMetric.value in metricConfigMap.value
        ? (localMetric.value as LoadMetricKey)
        : fallbackKey;
    return activeKey ? metricConfigMap.value[activeKey] : emptyMetricConfig;
  });

  const currentEvidence = computed(() => currentMetricConfig.value.evidence);

  let rotationTimer: ReturnType<typeof setInterval> | null = null;

  function rotateMetric() {
    const tabs = metricTabs.value;
    if (tabs.length <= 1) return;
    const currentIndex = tabs.findIndex((item) => item.value === localMetric.value);
    const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % tabs.length;
    localMetric.value = tabs[nextIndex].value as LoadMetricKey;
  }

  function restartRotation() {
    if (rotationTimer) clearInterval(rotationTimer);
    rotationTimer = setInterval(() => {
      rotateMetric();
    }, 5000);
  }

  onMounted(async () => {
    restartRotation();
    await nextTick();
    loading.summary = false;
    loading.structure = false;
    loading.evidence = false;
  });

  onBeforeUnmount(() => {
    if (rotationTimer) clearInterval(rotationTimer);
  });
</script>

<style scoped lang="less">
  .single-load-page {
    --page-content-height: calc(100vh - 64px - 16px);
    --top-row-height: calc(var(--page-content-height) * 0.14);
    height: calc(100vh - 64px);
    max-height: calc(100vh - 64px);
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 8px;
    overflow: hidden;
    box-sizing: border-box;
  }

  .section-top {
    flex: 0 0 var(--top-row-height);
    height: var(--top-row-height);
    display: grid;
    grid-template-columns: repeat(24, minmax(0, 1fr));
    gap: 8px;
    min-height: 0;
  }

  .section-top > * {
    grid-column: span 2;
  }

  .section-fatigue {
    flex: 1;
    min-height: 0;
  }

  .analysis-section-shell {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  .analysis-section-tabs {
    flex: 0 0 auto;
  }

  .analysis-section-tabs :deep(.arco-tabs-content) {
    display: none !important;
    overflow: hidden !important;
  }

  .analysis-section-content {
    flex: 1;
    min-width: 0;
    min-height: 0;
    display: grid;
    grid-template-rows: minmax(0, 1fr) minmax(0, 0.92fr);
    gap: 12px;
    box-sizing: border-box;
  }

  .load-cycle-structure-row {
    min-width: 0;
    min-height: 0;
    display: grid;
    grid-template-columns: 7fr 10fr 7fr;
    gap: 12px;
  }

  .analysis-panel {
    min-width: 0;
    min-height: 0;
  }

  .analysis-panel-shell {
    border-radius: 0;
    overflow: hidden;
  }

  .shock-analysis-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    min-height: 0;
  }

  .shock-analysis-panel {
    border-radius: 0;
    overflow: hidden;
  }

  .analysis-panel-shell :deep(.arco-card-body),
  .shock-analysis-panel :deep(.arco-card-body) {
    height: 100%;
    padding: 6px;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  @media (max-width: 1600px) {
    .analysis-section-content {
      grid-template-rows: auto auto;
    }

    .load-cycle-structure-row {
      grid-template-columns: 1fr;
    }

    .shock-analysis-row {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 1024px) {
    .section-top {
      grid-template-columns: repeat(24, minmax(0, 1fr));
    }

    .section-top > * {
      grid-column: span 24;
    }

    .shock-analysis-row {
      grid-template-columns: 1fr;
    }
  }
</style>
