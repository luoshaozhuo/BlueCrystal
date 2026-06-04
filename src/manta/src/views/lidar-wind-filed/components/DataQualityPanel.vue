<template>
  <div class="quality-panel">
    <div v-for="(row, rowIndex) in rows" :key="rowIndex" class="quality-row">
      <div
        v-for="metric in row"
        :key="metric.key"
        class="metric-block"
        :class="{ 'metric-block--highlight': metric.highlight }"
      >
        <div class="metric-label" :title="metricLabels[metric.key] ?? metric.key">{{ metricLabels[metric.key] ?? metric.key }}</div>
        <div class="metric-value" :class="{ 'metric-value--highlight': metric.highlight }">
          <template v-if="typeof metric.value === 'number'">
            <span>{{ formatMetricValue(metric) }}</span>
            <small v-if="metric.unit">{{ metric.unit }}</small>
          </template>
          <template v-else>
            <span>{{ formatMetricValue(metric) }}</span>
          </template>
        </div>
        <div class="metric-footer">
          <span class="metric-status">{{ statusLabels[metric.status] }}</span>
          <div class="metric-progress">
            <div class="metric-progress__fill" :style="{ width: `${metric.progress * 100}%` }" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import type { DataQualityMetricItem, DataQualitySummary } from '@/types/lidar';
  import { useChartTheme } from '@/config/chart-theme';

  const props = defineProps<{
    data: DataQualitySummary;
  }>();

  const chartTheme = useChartTheme();
  const metricLabels: Record<string, string> = {
    availability: '可用率',
    latency: '时延',
    packetLoss: '丢包率',
    timeSync: '时间同步',
    snr: '平均 SNR',
    validBeam: '有效波束',
    freshness: '数据新鲜度',
    qualityScore: '综合评分',
  };
  const statusLabels = {
    excellent: '优秀',
    good: '良好',
    normal: '正常',
    warning: '告警',
  } as const;

  const rows = computed<DataQualityMetricItem[][]>(() => {
    const overview = props.data.qualityOverview;
    return [overview?.topMetrics ?? [], overview?.bottomMetrics ?? []];
  });

  function formatNumber(value: number, precision?: number) {
    if (typeof precision === 'number') {
      return value.toFixed(precision);
    }
    if (Number.isInteger(value)) {
      return value.toFixed(0);
    }
    return value.toString();
  }

  function formatMetricValue(metric: DataQualityMetricItem) {
    if (metric.key === 'qualityScore' && metric.grade) {
      return `${metric.grade} / ${metric.value}`;
    }
    if (typeof metric.value === 'number') {
      return `${metric.prefix ?? ''}${formatNumber(metric.value, metric.precision)}`;
    }
    return `${metric.prefix ?? ''}${metric.value}`;
  }
</script>

<style scoped lang="less">
  .quality-panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .quality-row {
    flex: 1 1 0;
    min-height: 0;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-template-rows: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .metric-block {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 0;
    padding: 10px 10px 8px;
    border: 1px solid v-bind('chartTheme.borderSoft');
    border-radius: 10px;
    background: v-bind('chartTheme.bgPanel');
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  }

  .metric-block:hover {
    border-color: v-bind('chartTheme.axisLine');
    transform: translateY(-1px);
  }

  .metric-block--highlight {
    border-color: v-bind('chartTheme.primary');
    background: linear-gradient(180deg, v-bind('chartTheme.fillSoft'), v-bind('chartTheme.bgPanel'));
    box-shadow:
      inset 0 0 0 1px v-bind('chartTheme.primary'),
      0 0 18px v-bind('chartTheme.fillMuted');
  }

  .metric-label {
    overflow: hidden;
    color: v-bind('chartTheme.textMuted');
    font-size: 11px;
    line-height: 1.2;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .metric-value {
    display: flex;
    align-items: baseline;
    gap: 4px;
    margin: 6px 0;
    color: v-bind('chartTheme.textMain');
    font-size: 22px;
    font-weight: 600;
    line-height: 1;
    white-space: nowrap;
  }

  .metric-value small {
    color: v-bind('chartTheme.textMuted');
    font-size: 11px;
    font-weight: 400;
  }

  .metric-value--highlight {
    font-size: 24px;
    letter-spacing: 0.02em;
  }

  .metric-footer {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .metric-status {
    color: v-bind('chartTheme.textFaint');
    font-size: 10px;
    line-height: 1;
  }

  .metric-progress {
    width: 100%;
    height: 3px;
    overflow: hidden;
    border-radius: 999px;
    background: v-bind('chartTheme.fillMuted');
  }

  .metric-progress__fill {
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, v-bind('chartTheme.info'), v-bind('chartTheme.primary'));
  }

  .metric-block--highlight .metric-progress__fill {
    background: linear-gradient(90deg, v-bind('chartTheme.primary'), v-bind('chartTheme.warning'));
  }
</style>
