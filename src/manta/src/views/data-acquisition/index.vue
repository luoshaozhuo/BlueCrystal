<template>
  <div class="collect-page">
    <a-row class="section-overview" :gutter="8">
      <a-col v-for="item in overviewList" :key="item.key" :span="2" class="full-height">
        <TopMetricCard
          :label="item.label"
          :value="item.value"
          :unit="item.unit"
          :status="item.status"
          :trend="item.trend"
          :precision="item.precision"
          :loading="pageLoading"
          value-use-theme-color
          reverse-trend-color
        />
      </a-col>
    </a-row>

    <!-- ② 采集层 -->
    <div class="section-collection">
      <!-- 左：设备通信实况 -->
      <a-card class="comm-card analysis-panel" :bordered="false" :loading="pageLoading">
        <template #title>
          <div class="card-head">
            <div class="card-title" :style="cardTitleStyle">设备通信实况</div>
            <div class="card-subtitle" :style="cardSubtitleStyle">{{ commCardSubtitle }}</div>
          </div>
        </template>
        <DeviceCommStatusCard :data="pageData.deviceCommStatus" />
      </a-card>

      <!-- 右：数据质量 -->
      <a-card class="quality-card analysis-panel" :bordered="false" :loading="pageLoading">
        <template #title>
          <div class="card-head">
            <div class="card-title" :style="cardTitleStyle">数据质量</div>
            <div class="card-subtitle" :style="cardSubtitleStyle">完整率、同步误差、异常占比与延迟分布</div>
          </div>
        </template>
        <DataQualityAnalysisCard :data="pageData.dataQualityAnalysis" />
      </a-card>
    </div>

    <!-- ③ 资源层能力 -->
    <div class="section-resource">
      <a-card class="resource-card analysis-panel" :bordered="false" :loading="pageLoading">
        <template #title>
          <div class="card-head">
            <div class="card-title" :style="cardTitleStyle">信道资源</div>
            <div class="card-subtitle" :style="cardSubtitleStyle">带宽、流量与丢包状态概览</div>
          </div>
        </template>
        <ChannelResourceCard :data="pageData.channelResource" />
      </a-card>

      <a-card class="resource-card analysis-panel" :bordered="false" :loading="pageLoading">
        <template #title>
          <div class="card-head">
            <div class="card-title" :style="cardTitleStyle">存储资源</div>
            <div class="card-subtitle" :style="cardSubtitleStyle">容量增长、利用率与剩余空间</div>
          </div>
        </template>
        <StorageResourceCard :data="pageData.storageResource" />
      </a-card>

      <a-card class="resource-card analysis-panel" :bordered="false" :loading="pageLoading">
        <template #title>
          <div class="card-head">
            <div class="card-title" :style="cardTitleStyle">计算资源</div>
            <div class="card-subtitle" :style="cardSubtitleStyle">CPU、内存与处理性能状态</div>
          </div>
        </template>
        <ComputeResourceCard :data="pageData.computeResource" />
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
  import { useChartTheme } from '@/config/chart-theme';
  import TopMetricCard from '@/components/top-metric-card/index.vue';
  import ChannelResourceCard from './components/ChannelResourceCard.vue';
  import ComputeResourceCard from './components/ComputeResourceCard.vue';
  import DataQualityAnalysisCard from './components/DataQualityAnalysisCard.vue';
  import DeviceCommStatusCard from './components/DeviceCommStatusCard.vue';
  import StorageResourceCard from './components/StorageResourceCard.vue';
  import { getDataCollectionMock } from '@/mock/data-acquisition';
  import type { DataAcquisitionTopMetricKey } from '@/mock/data-acquisition';

  const pageLoading = ref(true);
  const pageData = ref(getDataCollectionMock(0));
  const topMetricLabels: Record<DataAcquisitionTopMetricKey, string> = {
    writeRate: '实时写入速率',
    avgDelay: '平均延迟',
    p95Delay: 'P95 延迟',
    onlineDevices: '在线设备',
    activeAlerts: '活跃告警',
    syncError: '时间同步误差',
    integrityRate: '完整率',
    abnormalRate: '异常比例',
    todayIncrement: '今日新增',
    qualityLevel: '数据质量等级',
    availableData: '可分析数据量',
    totalData: '累计数据量',
  };
  const qualityLevelValueLabels = {
    A: 'A级',
    B: 'B级',
  } as const;
  const overviewList = computed(() =>
    pageData.value.topMetrics.map((item) => ({
      ...item,
      label: topMetricLabels[item.key],
      value: item.key === 'qualityLevel' ? qualityLevelValueLabels[item.value as 'A' | 'B'] ?? item.value : item.value,
    })),
  );
  const chartTheme = useChartTheme();
  const dividerColor = chartTheme.value.splitLineSoft;
  const cardTitleStyle = computed(() => ({
    color: chartTheme.value.textMain,
    fontSize: '12px',
    fontWeight: 500,
    lineHeight: '1.25',
  }));
  const cardSubtitleStyle = computed(() => ({
    color: chartTheme.value.textMuted,
    fontSize: '11px',
    fontWeight: 400,
    lineHeight: '1.3',
  }));
  const commCardSubtitle = computed(() => {
    const devices = pageData.value.deviceCommStatus.devices;
    const turbineCount = devices.filter((item) => item.type === 'turbine').length;
    const lidarCount = devices.filter((item) => item.type === 'lidar').length;
    return `${turbineCount}台风机，${lidarCount}台激光雷达`;
  });

  let metricStep = 0;
  let overviewTimer: ReturnType<typeof window.setInterval> | null = null;

  function refreshOverview() {
    pageData.value = getDataCollectionMock(metricStep);
    metricStep += 1;
  }

  onMounted(async () => {
    refreshOverview();
    await nextTick();
    pageLoading.value = false;
    overviewTimer = window.setInterval(() => {
      refreshOverview();
    }, 1800);
  });

  onBeforeUnmount(() => {
    if (overviewTimer) {
      window.clearInterval(overviewTimer);
      overviewTimer = null;
    }
  });
</script>

<style scoped lang="less">
  .collect-page {
    --page-content-height: calc(100vh - 64px - 16px);
    --top-row-height: calc(var(--page-content-height) * 0.14);
    height: calc(100vh - 64px);
    display: grid;
    grid-template-rows: var(--top-row-height) minmax(0, 1.2fr) minmax(0, 1fr);
    gap: 8px;
    padding: 8px;
    overflow: hidden;
    min-height: 0;
    box-sizing: border-box;
  }

  .section-overview {
    height: var(--top-row-height);
    min-height: 0;
  }

  .full-height {
    height: 100%;
    min-height: 0;
  }

  .section-collection {
    display: grid;
    grid-template-columns: 60% 40%;
    gap: 8px;
    min-height: 0;
  }

  .comm-card,
  .quality-card {
    height: 100%;
  }

  .analysis-panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .analysis-panel :deep(.arco-card-header) {
    flex: 0 0 auto;
    padding: 8px 10px 6px;
    border-bottom: 1px solid v-bind(dividerColor);
  }

  .analysis-panel :deep(.arco-card-body) {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    padding: 6px;
    min-height: 0;
    overflow: hidden;
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
  }

  .card-subtitle {
    font-size: 11px;
    line-height: 1.3;
  }

  .section-resource {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    min-height: 0;
  }

  .resource-card {
    height: 100%;
  }

  .resource-layout {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
    color: var(--color-text-2);
  }

  .value {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-primary-6);
  }
</style>
