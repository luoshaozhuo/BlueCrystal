<template>
  <div class="lidar-page">
    <a-row class="section-top" :gutter="8">
      <a-col :span="2" class="full-height">
      <OverviewTurbineSelectCard
        v-model="selectedLidarTurbine"
        :options="lidarTurbineOptions"
        :loading="loading.turbineOptions"
        label="选择机组"
        placeholder="选择机组"
      />
      </a-col>

      <a-col :span="2" class="full-height">
        <DeviceInfoCard :data="lidarDeviceInfo" :loading="loading.deviceInfo" />
      </a-col>

      <a-col v-for="item in displayTopMetrics" :key="item.key" :span="2" class="full-height">
        <TopMetricCard
          :label="item.label"
          :value="item.value"
          :unit="item.unit"
          :status="item.status"
          :trend="item.trend"
          :precision="item.precision"
          :loading="loading.topMetrics"
          reverse-trend-color
        />
      </a-col>

      <a-col :span="6" class="full-height">
        <a-card class="analysis-panel top-wave-panel" :bordered="false" :loading="loading.topWave">
          <template #title>
            <div class="card-head">
              <div class="card-title">风速（最近60秒）</div>
            </div>
          </template>
          <div class="top-wave-panel__content">
            <TopRealtimeWindWave :data="topRealtimeWindWave" />
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row class="section-measure" :gutter="8">
      <a-col :span="8" class="full-height">
        <a-card class="analysis-panel" :bordered="false" :loading="loading.volume">
          <template #title>
            <div class="card-head">
              <div class="card-title">3D Lidar 锥体视图（实时）</div>
              <div class="card-subtitle">原始波束采样</div>
            </div>
          </template>
          <LidarVolumeView :data="lidarVolumeData" />
        </a-card>
      </a-col>

      <a-col :span="8" class="full-height">
        <a-card class="analysis-panel" :bordered="false" :loading="loading.multiRange">
          <template #title>
            <div class="card-head">
              <div class="card-title">前向来流剖面（实时）</div>
              <div class="card-subtitle">10个探测距离上的合成来流参数分布</div>
            </div>
          </template>
          <LidarInflowProfilePanel :data="inflowProfilePanelData" />
        </a-card>
      </a-col>

      <a-col :span="8" class="full-height">
        <a-card class="analysis-panel" :bordered="false" :loading="loading.windRose">
          <template #title>
            <div class="card-head">
              <div class="card-title">风向与湍流度</div>
              <div class="card-subtitle">从最近一年数据统计得到</div>
            </div>
          </template>
          <WindRoseTiStats :data="windRoseTiStats" />
        </a-card>
      </a-col>
    </a-row>

    <a-row class="section-model" :gutter="8">
      <a-col :span="12" class="full-height">
        <a-card class="analysis-panel" :bordered="false" :loading="loading.transfer">
          <template #title>
            <div class="card-head">
              <div class="card-title">雷达与风速仪传递函数</div>
              <div class="card-subtitle">对数频轴下的增益衰减与相位滞后特征</div>
            </div>
          </template>
          <TransferFunctionChart :data="transferFunctionData" />
        </a-card>
      </a-col>

      <a-col :span="6" class="full-height">
        <a-card class="analysis-panel" :bordered="false" :loading="loading.consistency">
          <template #title>
            <div class="card-head">
              <div class="card-title">雷达与风速仪一致性</div>
              <div class="card-subtitle">Lidar 与机舱风速散点及回归偏差</div>
            </div>
          </template>
          <ConsistencyAlignmentChart :data="consistencyAlignmentData" />
        </a-card>
      </a-col>

      <a-col :span="6" class="full-height">
        <a-card class="analysis-panel" :bordered="false" :loading="loading.quality">
          <template #title>
            <div class="card-head">
              <div class="card-title">数据质量总览</div>
              <div class="card-subtitle">可用率、延迟、丢包与信号同步摘要</div>
            </div>
          </template>
          <DataQualityPanel :data="dataQualitySummary" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts" setup>
  import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
  import type {
    ConsistencyAlignmentData,
    DataQualitySummary,
    LidarDeviceInfo,
    LidarForwardComposite3DResponse,
    LidarInflowProfilePanelData,
    LidarTopMetricItem,
    LidarTurbineOption,
    RealtimeWindWaveResponse,
    TransferFunctionData,
    WindRoseTiStats as WindRoseTiStatsData,
  } from '@/types/lidar';
  import {
    getConsistencyAlignmentData,
    getDataQualitySummary,
    getLidarDeviceInfo,
    getLidarInflowProfilePanelData,
    getLidarForwardComposite3DData,
    getLidarTopMetrics,
    getLidarTurbineOptions,
    getTopRealtimeWindWave,
    getTransferFunctionData,
    getWindRoseTiStats,
    setActiveLidarTurbine,
  } from '@/api/lidar-page';
  import { useChartTheme } from '@/config/chart-theme';
  import OverviewTurbineSelectCard from '@/components/overview-turbine-select-card/index.vue';
  import ConsistencyAlignmentChart from './components/ConsistencyAlignmentChart.vue';
  import DataQualityPanel from './components/DataQualityPanel.vue';
  import DeviceInfoCard from './components/DeviceInfoCard.vue';
  import LidarInflowProfilePanel from './components/LidarInflowProfilePanel.vue';
  import LidarVolumeView from './components/LidarVolumeView.vue';
  import TopMetricCard from '@/components/top-metric-card/index.vue';
  import TopRealtimeWindWave from './components/TopRealtimeWindWave.vue';
  import TransferFunctionChart from './components/TransferFunctionChart.vue';
  import WindRoseTiStats from './components/WindRoseTiStats.vue';

  const topMetricLabels = {
    deviceStatus: '设备状态',
    hubSpeed: '轮毂高度实时风速',
    hubDirection: '轮毂高度实时风向',
    ti1m: '最近1分钟湍流度',
    gustFactor: '阵风因子',
    verticalShear: '竖向风切变',
    horizontalShear: '横向风切变',
  } as const;
  const deviceStatusValueLabels = {
    normal: '在线',
    warning: '告警',
    offline: '离线',
  } as const;
  const initialTopMetrics: LidarTopMetricItem[] = [
    { key: 'deviceStatus', value: 'normal', status: 'normal' },
    { key: 'hubSpeed', value: 0, unit: 'm/s', precision: 2, status: 'normal' },
    { key: 'hubDirection', value: 0, unit: 'deg', precision: 0, status: 'normal' },
    { key: 'ti1m', value: 0, unit: '%', precision: 1, status: 'normal' },
    { key: 'gustFactor', value: 0, unit: '-', precision: 2, status: 'normal' },
    { key: 'verticalShear', value: 0, unit: '-', precision: 2, status: 'normal' },
    { key: 'horizontalShear', value: 0, unit: '-', precision: 2, status: 'normal' },
  ];

  const lidarTurbineOptions = ref<LidarTurbineOption[]>([]);
  const selectedLidarTurbine = ref('');
  const lidarDeviceInfo = ref<LidarDeviceInfo | null>(null);
  const topMetrics = ref<LidarTopMetricItem[]>(initialTopMetrics);
  const displayTopMetrics = computed(() =>
    topMetrics.value.map((item) => ({
      ...item,
      label: topMetricLabels[item.key as keyof typeof topMetricLabels] ?? item.key,
      value:
        item.key === 'deviceStatus'
          ? deviceStatusValueLabels[item.value as 'normal' | 'warning' | 'offline'] ?? item.value
          : item.value,
    })),
  );
  const topRealtimeWindWave = ref<RealtimeWindWaveResponse>({
    points: [],
    current: 0,
    mean60s: 0,
    min60s: 0,
    max60s: 0,
  });

  const lidarVolumeData = ref<LidarForwardComposite3DResponse>({
    turbineId: 'WT-07',
    hubWindSpeed: 0,
    hubWindDirection: 0,
    distances: [],
    rawPoints: [],
    synthPoints: [],
  });
  const inflowProfilePanelData = ref<LidarInflowProfilePanelData>({
    activeDistance: 150,
    distances: [],
    profiles: [],
  });
  const windRoseTiStats = ref<WindRoseTiStatsData>({ sectors: [] });
  const transferFunctionData = ref<TransferFunctionData>({
    points: [],
    markerFrequencies: [0.1, 0.3],
  });
  const consistencyAlignmentData = ref<ConsistencyAlignmentData>({
    points: [],
    regression: { slope: 1, intercept: 0 },
    stats: { bias: 0, rmse: 0, corr: 0 },
  });
  const dataQualitySummary = ref<DataQualitySummary>({
    qualityOverview: {
      topMetrics: [],
      bottomMetrics: [],
    },
  });
  const loading = reactive({
    turbineOptions: true,
    deviceInfo: true,
    topMetrics: true,
    topWave: true,
    volume: true,
    multiRange: true,
    windRose: true,
    transfer: true,
    consistency: true,
    quality: true,
  });

  const chartTheme = useChartTheme();
  const dividerColor = chartTheme.value.splitLineSoft;

  let topWaveTimer: ReturnType<typeof window.setInterval> | null = null;
  let topMetricsTimer: ReturnType<typeof window.setInterval> | null = null;
  let forwardFieldTimer: ReturnType<typeof window.setInterval> | null = null;
  let inflowProfileTimer: ReturnType<typeof window.setInterval> | null = null;

  async function loadTopCards() {
    loading.turbineOptions = true;
    const options = await getLidarTurbineOptions();
    lidarTurbineOptions.value = options;
    if (!selectedLidarTurbine.value) {
      selectedLidarTurbine.value = options[0]?.value ?? '';
      setActiveLidarTurbine(selectedLidarTurbine.value);
    }
    loading.turbineOptions = false;
  }

  async function loadFirstRowData() {
    loading.deviceInfo = true;
    loading.topMetrics = true;
    loading.topWave = true;
    const [deviceInfo, metrics, wave] = await Promise.all([
      getLidarDeviceInfo(),
      getLidarTopMetrics(),
      getTopRealtimeWindWave(),
    ]);
    lidarDeviceInfo.value = deviceInfo;
    topMetrics.value = metrics;
    topRealtimeWindWave.value = wave;
    loading.deviceInfo = false;
    loading.topMetrics = false;
    loading.topWave = false;
  }

  async function refreshTopMetrics() {
    topMetrics.value = await getLidarTopMetrics();
  }

  async function refreshTopWave() {
    topRealtimeWindWave.value = await getTopRealtimeWindWave();
  }

  async function refreshForwardField(showLoading = false) {
    if (showLoading) {
      loading.volume = true;
    }
    lidarVolumeData.value = await getLidarForwardComposite3DData();
    if (showLoading) {
      loading.volume = false;
    }
  }

  async function refreshInflowProfile(showLoading = false) {
    if (showLoading) {
      loading.multiRange = true;
    }
    inflowProfilePanelData.value = await getLidarInflowProfilePanelData();
    if (showLoading) {
      loading.multiRange = false;
    }
  }

  async function loadLowerCards() {
    const tasks: Array<Promise<void>> = [
      getLidarForwardComposite3DData()
        .then((data) => {
          lidarVolumeData.value = data;
        })
        .finally(() => {
          loading.volume = false;
        }),
      getLidarInflowProfilePanelData()
        .then((data) => {
          inflowProfilePanelData.value = data;
        })
        .finally(() => {
          loading.multiRange = false;
        }),
      getWindRoseTiStats()
        .then((data) => {
          windRoseTiStats.value = data;
        })
        .finally(() => {
          loading.windRose = false;
        }),
      getTransferFunctionData()
        .then((data) => {
          transferFunctionData.value = data;
        })
        .finally(() => {
          loading.transfer = false;
        }),
      getConsistencyAlignmentData()
        .then((data) => {
          consistencyAlignmentData.value = data;
        })
        .finally(() => {
          loading.consistency = false;
        }),
      getDataQualitySummary()
        .then((data) => {
          dataQualitySummary.value = data;
        })
        .finally(() => {
          loading.quality = false;
        }),
    ];

    await Promise.allSettled(tasks);
  }

  watch(
    selectedLidarTurbine,
    async (value) => {
      if (!value) return;
      setActiveLidarTurbine(value);
      await loadFirstRowData();
      await Promise.all([refreshForwardField(true), refreshInflowProfile(true)]);
    },
    { immediate: true },
  );

  onMounted(async () => {
    await loadTopCards();
    await loadLowerCards();
    topWaveTimer = window.setInterval(() => {
      refreshTopWave();
    }, 1000);
    topMetricsTimer = window.setInterval(() => {
      refreshTopMetrics();
    }, 5000);
    forwardFieldTimer = window.setInterval(() => {
      refreshForwardField();
    }, 3000);
    inflowProfileTimer = window.setInterval(() => {
      refreshInflowProfile();
    }, 3000);
  });

  onBeforeUnmount(() => {
    if (topWaveTimer) {
      window.clearInterval(topWaveTimer);
      topWaveTimer = null;
    }
    if (topMetricsTimer) {
      window.clearInterval(topMetricsTimer);
      topMetricsTimer = null;
    }
    if (forwardFieldTimer) {
      window.clearInterval(forwardFieldTimer);
      forwardFieldTimer = null;
    }
    if (inflowProfileTimer) {
      window.clearInterval(inflowProfileTimer);
      inflowProfileTimer = null;
    }
  });
</script>

<style scoped lang="less">
  .lidar-page {
    --page-content-height: calc(100vh - 64px - 16px);
    --top-row-height: calc(var(--page-content-height) * 0.14);
    height: calc(100vh - 64px);
    max-height: calc(100vh - 64px);
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 8px;
    overflow: hidden;
    min-height: 0;
    box-sizing: border-box;
  }

  .section-top {
    flex: 0 0 var(--top-row-height);
    height: var(--top-row-height);
  }

  .section-measure {
    flex: 0 0 38%;
  }

  .section-model {
    flex: 1 1 auto;
    min-height: 0;
  }

  .full-height {
    height: 100%;
    min-height: 0;
  }

  .analysis-panel {
    height: 100%;
    min-height: 0;
    border-radius: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .analysis-panel :deep(.arco-card-header) {
    flex: 0 0 auto;
    padding: 8px 10px 6px;
    border-bottom: 1px solid v-bind(dividerColor);
  }

  .analysis-panel :deep(.arco-card-body) {
    flex: 1 1 auto;
    padding: 6px;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }

  .analysis-panel :deep(.arco-card-body > *) {
    flex: 1 1 auto;
    min-height: 0;
  }

  .card-head {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .card-title {
    font-size: 12px;
    line-height: 1.25;
    color: var(--color-text-2);
  }

  .card-subtitle {
    font-size: 11px;
    line-height: 1.3;
    color: var(--color-text-3);
  }

  .top-wave-panel :deep(.arco-card-header) {
    padding: 6px 10px 2px;
    border-bottom: none;
  }

  .top-wave-panel :deep(.arco-card-body) {
    padding: 0 8px 6px;
  }

  .top-wave-panel__content {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }
</style>
