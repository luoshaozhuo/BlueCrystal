<template>
  <div class="power-analysis-page">
    <div class="row row-summary">
      <OverviewTurbineSelectCard
        v-model="selectedTurbine"
        :options="turbineOptions"
        :loading="loading.summary"
      />
      <OverviewTurbineInfoCard :items="turbineInfoItems" :loading="loading.summary" />
      <StatSummaryCard
        v-for="item in displaySummaryMetrics"
        :key="item.key"
        :title="item.title"
        :value="item.value"
        :unit="item.unit"
        :subtitle="item.subtitle"
        :trend="item.trend"
        :compact-value="item.compactValue"
        :loading="loading.summary"
      />
    </div>

    <div class="row row-benefit">
      <a-card class="analysis-panel" :bordered="false" :loading="loading.benefit">
        <template #title>
          <div class="section-head">
            <div>
              <div class="section-title">功率曲线与收益分布</div>
              <div class="section-subtitle">条件化功率曲线 + 各风速段净收益</div>
            </div>
          </div>
        </template>
        <PowerCurveComparisonChart
          :data="powerCurveSeries"
          :rayleigh-parameters="windFrequencyRayleighParameters"
        />
      </a-card>
    </div>

    <div class="volatility-column">
      <a-card class="analysis-panel" :bordered="false" :loading="loading.volatility">
        <template #title>
          <div class="section-head">
            <div>
              <div class="section-title">波动性收益摘要</div>
              <div class="section-subtitle">分布迁移、尾部收缩与统计稳健性共同支撑波动性改善</div>
            </div>
          </div>
        </template>
        <VolatilitySummary :data="volatilityEvidence" />
      </a-card>
    </div>

    <div class="response-grid">
      <div class="response-grid__main">
        <a-card class="analysis-panel" :bordered="false" :loading="loading.response">
          <template #title>
            <div class="section-head">
              <div>
                <div class="section-title">短期扰动事件分析</div>
                <div class="section-subtitle">扰动模板、响应对比、关键时序与指标改善联合评估</div>
              </div>
            </div>
          </template>
          <GustResponse :data="gustResponseCardData" />
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, nextTick, onMounted, reactive, ref } from 'vue';
  import OverviewTurbineInfoCard from '@/components/overview-turbine-info-card/index.vue';
  import OverviewTurbineSelectCard from '@/components/overview-turbine-select-card/index.vue';
  import GustResponse from './components/GustResponse.vue';
  import PowerCurveComparisonChart from './components/PowerCurveComparisonChart.vue';
  import StatSummaryCard from './components/StatSummaryCard.vue';
  import VolatilitySummary from './components/VolatilitySummary.vue';
  import {
    gustResponseCardData,
    powerCurveSeries,
    summaryMetrics as overviewSummaryMetrics,
    turbineOptions,
    turbineProfiles,
    volatilityEvidence,
    windFrequencyRayleighParameters,
  } from '@/mock/power-analysis';

  const summaryMetricCopy: Record<
    string,
    { title: string; subtitle: string }
  > = {
    netAepGain: { title: '净发电增益', subtitle: '等效化 AEP' },
    avgPowerGain: { title: '平均功率提升', subtitle: '中高风速段' },
    rmsReduction: { title: 'RMS 改善', subtitle: '10s~600s 窗口' },
    tailRiskReduction: { title: '尾部风险改善', subtitle: 'Peak / P95 / P99' },
    validEventCount: { title: '有效事件数', subtitle: '阵风识别样本' },
    retentionRate: { title: '样本保留率', subtitle: '对齐清洗后保留' },
    alignmentSuccessRate: { title: '对齐成功率', subtitle: '阵风起点对齐成功' },
    mainContributionBand: { title: '主贡献风速段', subtitle: '净收益累计最高' },
    positiveGainBinRate: { title: '正收益风速箱占比', subtitle: '全风速分箱统计' },
  };

  const selectedTurbine = ref(turbineProfiles[0]?.turbineId ?? '');
  const loading = reactive({
    summary: true,
    benefit: true,
    volatility: true,
    response: true,
  });
  const currentProfile = computed(
    () =>
      turbineProfiles.find((item) => item.turbineId === selectedTurbine.value) ??
      turbineProfiles[0],
  );

  const turbineInfoItems = computed(() => [
    { label: '风机型号', value: currentProfile.value.model },
    { label: '投运日期', value: currentProfile.value.commissionDate },
    { label: '优化节点', value: currentProfile.value.optimizationDate },
    { label: '分析窗口', value: `近 ${currentProfile.value.analysisWindowDays} 天` },
  ]);

  const displaySummaryMetrics = computed(() =>
    overviewSummaryMetrics.map((item) => ({
      ...item,
      title: summaryMetricCopy[item.key]?.title ?? item.key,
      subtitle: summaryMetricCopy[item.key]?.subtitle ?? '',
    })),
  );

  onMounted(async () => {
    await nextTick();
    loading.summary = false;
    loading.benefit = false;
    loading.volatility = false;
    loading.response = false;
  });

</script>

<style scoped lang="less">
  .power-analysis-page {
    --page-content-height: calc(100vh - 64px - 16px);
    --top-row-height: calc(var(--page-content-height) * 0.14);
    height: calc(100vh - 64px);
    max-height: calc(100vh - 64px);
    display: grid;
    grid-template-columns: minmax(0, 16fr) minmax(0, 8fr);
    grid-template-rows:
      minmax(0, var(--top-row-height))
      minmax(0, calc((100% - 24px) * 0.29))
      minmax(0, calc((100% - 24px) * 0.21))
      minmax(0, calc((100% - 24px) * 0.36));
    gap: 8px;
    padding: 8px;
    overflow: hidden;
    min-height: 0;
    box-sizing: border-box;
  }

  .row {
    height: 100%;
    min-height: 0;
  }

  .row-summary {
    grid-column: 1 / span 2;
    grid-row: 1;
    height: var(--top-row-height);
    display: grid;
    grid-template-columns: repeat(24, minmax(0, 1fr));
    gap: 8px;
    align-items: stretch;
  }

  .row-summary > * {
    grid-column: span 2;
  }

  .row-benefit {
    grid-column: 1;
    grid-row: 2;
    display: grid;
    grid-template-columns: 1fr;
  }

  .row-summary > *,
  .row-benefit > *,
  .response-grid > * {
    min-height: 0;
    height: 100%;
  }

  .analysis-panel {
    height: 100%;
    min-height: 0;
    overflow: hidden;
    border-radius: 0;
    display: flex;
    flex-direction: column;
  }

  .analysis-panel :deep(.arco-card-body) {
    height: 100%;
    min-height: 0;
    padding: 5px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .section-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    min-height: 0;
  }

  .section-title {
    font-size: 12px;
    line-height: 1.25;
    color: var(--color-text-2);
  }

  .section-subtitle {
    margin-top: 1px;
    font-size: 11px;
    line-height: 1.3;
    color: var(--color-text-3);
  }

  .volatility-column {
    grid-column: 2;
    grid-row: 2 / span 3;
    min-height: 0;
    height: 100%;
  }

  .response-grid {
    grid-column: 1;
    grid-row: 3 / span 2;
    min-height: 0;
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: 1fr;
  }

  .response-grid__main {
    min-height: 0;
    grid-row: 1;
    grid-column: 1;
  }

  @media (max-width: 1600px) {
    .row-summary {
      grid-template-columns: repeat(24, minmax(0, 1fr));
    }

    .power-analysis-page {
      grid-template-columns: 1fr;
    }

    .row-summary,
    .row-benefit,
    .volatility-column,
    .response-grid {
      grid-column: 1;
    }

    .row-benefit {
      grid-row: 2;
    }

    .volatility-column {
      grid-row: 3;
    }

    .response-grid {
      grid-row: 4;
    }
  }

  @media (max-width: 1200px) {
    .power-analysis-page {
      height: auto;
      overflow: visible;
    }

    .row-summary {
      grid-template-columns: repeat(24, minmax(0, 1fr));
    }

    .row-summary > * {
      grid-column: span 24;
    }
  }
</style>
