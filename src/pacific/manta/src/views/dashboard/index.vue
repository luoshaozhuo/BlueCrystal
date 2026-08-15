<template>
  <div class="dashboard-screen">
    <div class="viewer-layer">
      <GeoSceneViewer />
    </div>

    <div class="overlay overlay-right">
      <a-card :bordered="false" class="floating-card monitor-card" :loading="loading.utilization">
        <div class="monitor-card-content gauge-card-content">
          <div class="monitor-card-title">当前风能利用率</div>
          <Chart :options="utilizationGaugeOptions" height="100%" />
          <div class="gauge-card-stats">
            <div class="gauge-stat">
              <span class="gauge-stat-label">实际发电功率</span>
              <span class="gauge-stat-value">{{ currentActualPower }} MW</span>
            </div>
            <div class="gauge-stat">
              <span class="gauge-stat-label">总可用功率</span>
              <span class="gauge-stat-value"
                >{{ currentAvailablePower }} MW</span
              >
            </div>
          </div>
        </div>
      </a-card>

      <a-card :bordered="false" class="floating-card monitor-card" :loading="loading.aep">
        <div class="monitor-card-content value-card-content">
          <div class="monitor-card-title">累计 AEP 提升量</div>
          <div class="metric-value-group">
            <div class="metric-value-primary">{{ cumulativeAepGain }}</div>
            <div class="metric-value-unit">MWh</div>
          </div>
          <div class="metric-footnote">截至当前时刻累计增发电量</div>
          <div class="metric-detail-grid">
            <div class="metric-detail-item">
              <span class="metric-detail-label">今日增益占比</span>
              <span class="metric-detail-value">{{ aepGainRatio }}%</span>
            </div>
            <div class="metric-detail-item">
              <span class="metric-detail-label">折算收益</span>
              <span class="metric-detail-value">{{ aepRevenue }} kCNY</span>
            </div>
          </div>
        </div>
      </a-card>

      <a-card :bordered="false" class="floating-card monitor-card" :loading="loading.fatigue">
        <div class="monitor-card-content value-card-content">
          <div class="monitor-card-title">累计等效疲劳载荷降低小时数</div>
          <div class="metric-value-group">
            <div class="metric-value-primary">{{ reducedFatigueHours }}</div>
            <div class="metric-value-unit">h</div>
          </div>
          <div class="metric-footnote">折算机组寿命缓释累计小时数</div>
          <div class="metric-detail-grid">
            <div class="metric-detail-item">
              <span class="metric-detail-label">塔架载荷下降</span>
              <span class="metric-detail-value">{{ towerLoadReduction }}%</span>
            </div>
            <div class="metric-detail-item">
              <span class="metric-detail-label">叶根 DEL 改善</span>
              <span class="metric-detail-value">{{ bladeDelReduction }}%</span>
            </div>
          </div>
        </div>
      </a-card>

      <a-card :bordered="false" class="floating-card monitor-card" :loading="loading.fluctuation">
        <div class="monitor-card-content fluctuation-card-content">
          <div class="monitor-card-title">功率波动率变化趋势</div>
          <div class="fluctuation-summary">
            <div class="fluctuation-summary-item">
              <span class="metric-detail-label">当前波动率</span>
              <span class="metric-detail-value"
                >{{ currentFluctuationRate }}%</span
              >
            </div>
            <div class="fluctuation-summary-item">
              <span class="metric-detail-label">相较基准下降（30天）</span>
              <span class="metric-detail-value"
                >{{ fluctuationImprovement }}%</span
              >
            </div>
          </div>
          <Chart :options="fluctuationTrendOptions" height="100%" />
        </div>
      </a-card>
    </div>

    <div class="overlay overlay-left-bottom">
      <a-card
        :bordered="false"
        class="floating-card floating-card-large trend-panel-card"
        :loading="loading.trend"
      >
        <div class="trend-panel">
          <div class="trend-chart-grid">
            <section class="trend-chart-box">
              <div class="trend-chart-meta">
                <div class="trend-chart-title">全场实时有功功率</div>
                <div class="trend-chart-value">{{ latestActivePower }} MW</div>
              </div>
              <Chart :options="activePowerOptions" height="100%" />
            </section>

            <section class="trend-chart-box">
              <div class="trend-chart-meta">
                <div class="trend-chart-title">全场无功功率</div>
                <div class="trend-chart-value">
                  {{ latestReactivePower }} MVar
                </div>
              </div>
              <Chart :options="reactivePowerOptions" height="100%" />
            </section>

            <section class="trend-chart-box">
              <div class="trend-chart-meta">
                <div class="trend-chart-title">全场平均风速</div>
                <div class="trend-chart-value">
                  {{ latestAverageWindSpeed }} m/s
                </div>
              </div>
              <Chart :options="averageWindSpeedOptions" height="100%" />
            </section>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
  import GeoSceneViewer from './components/GeoSceneViewer.vue';
  import { useChartTheme } from '@/config/chart-theme';
  import useAppStore from '@/store/modules/app';

  type RealtimePoint = {
    time: string;
    activePower: number;
    reactivePower: number;
    averageWindSpeed: number;
  };

  const trendPointCount = 60;
  const trendTickMs = 1000;
  const baseTimestamp = Date.now();
  const loading = ref({
    utilization: true,
    aep: true,
    fatigue: true,
    fluctuation: true,
    trend: true,
  });
  const chartTextColor = ref('#1d2129');
  const appStore = useAppStore();
  const appChartTheme = useChartTheme();
  const baseAvailablePower = 124;
  const fluctuationSeries = Array.from({ length: 30 }, (_, index) => {
    const day = `${index + 1}`.padStart(2, '0');
    const value =
      13.2 -
      index * 0.14 +
      Math.sin(index / 2.8) * 1.1 +
      Math.cos(index / 4.3) * 0.35;
    return {
      label: `${day}d`,
      value: Number(value.toFixed(2)),
    };
  });

  function resolveThemeColor(variableName: string, fallback: string) {
    if (typeof window === 'undefined') return fallback;
    const value = window
      .getComputedStyle(document.documentElement)
      .getPropertyValue(variableName)
      .trim();
    return value || fallback;
  }

  function resolveRenderedTextColor(selector: string, fallback: string) {
    if (typeof window === 'undefined') return fallback;
    const element = document.querySelector<HTMLElement>(selector);
    if (!element) return fallback;
    const value = window.getComputedStyle(element).color.trim();
    return value || fallback;
  }

  function syncChartTextColor() {
    const fallback = resolveThemeColor('--color-text-1', '#1d2129');
    chartTextColor.value = resolveRenderedTextColor(
      '.trend-chart-value',
      fallback,
    );
  }

  function formatTimeLabel(timestamp: number) {
    const date = new Date(timestamp);
    const minutes = `${date.getMinutes()}`.padStart(2, '0');
    const seconds = `${date.getSeconds()}`.padStart(2, '0');
    return `${minutes}:${seconds}`;
  }

  function createTrendPoint(index: number): RealtimePoint {
    const timestamp =
      baseTimestamp - (trendPointCount - 1 - index) * trendTickMs;
    const wave = index / 4.2;
    const pulse = Math.sin(index / 13) > 0.78 ? 1 : 0;
    const activePower =
      92 +
      Math.sin(wave) * 16 +
      Math.cos(wave / 2.4) * 7 +
      pulse * 8 +
      Math.sin(index * 1.7) * 2.4;
    const reactivePower =
      24 +
      Math.cos(wave * 0.92) * 8 +
      Math.sin(wave / 2.8) * 3.8 +
      Math.cos(index * 1.35) * 1.8;
    const averageWindSpeed =
      8.2 +
      Math.sin(wave * 0.88) * 1.9 +
      Math.cos(wave / 3.1) * 0.9 +
      Math.sin(index * 1.15) * 0.45;

    return {
      time: formatTimeLabel(timestamp),
      activePower: Number(activePower.toFixed(2)),
      reactivePower: Number(reactivePower.toFixed(2)),
      averageWindSpeed: Number(averageWindSpeed.toFixed(2)),
    };
  }

  const trendSeries = ref(
    Array.from({ length: trendPointCount }, (_, index) =>
      createTrendPoint(index),
    ),
  );

  const trendCursor = ref(trendPointCount);
  let trendTimer: ReturnType<typeof window.setInterval> | undefined =
    window.setInterval(() => {
      const nextPoint = createTrendPoint(trendCursor.value);
      trendSeries.value = [...trendSeries.value.slice(1), nextPoint];
      trendCursor.value += 1;
    }, trendTickMs);

  const latestActivePower = computed(
    () =>
      trendSeries.value[trendSeries.value.length - 1]?.activePower.toFixed(2) ??
      '--',
  );
  const latestReactivePower = computed(
    () =>
      trendSeries.value[trendSeries.value.length - 1]?.reactivePower.toFixed(
        2,
      ) ?? '--',
  );
  const latestAverageWindSpeed = computed(
    () =>
      trendSeries.value[trendSeries.value.length - 1]?.averageWindSpeed.toFixed(
        2,
      ) ?? '--',
  );
  const latestActivePowerNumber = computed(
    () => trendSeries.value[trendSeries.value.length - 1]?.activePower ?? 0,
  );
  const currentAvailablePowerNumber = computed(
    () =>
      baseAvailablePower +
      Math.sin(trendCursor.value / 6) * 4 +
      Math.cos(trendCursor.value / 10) * 2.2,
  );
  const utilizationRatio = computed(() => {
    const denominator = currentAvailablePowerNumber.value;
    if (denominator <= 0) return 0;
    return Math.min(100, (latestActivePowerNumber.value / denominator) * 100);
  });
  const currentActualPower = computed(() =>
    latestActivePowerNumber.value.toFixed(2),
  );
  const currentAvailablePower = computed(() =>
    currentAvailablePowerNumber.value.toFixed(2),
  );
  const cumulativeAepGain = computed(() =>
    (368.4 + trendCursor.value * 0.92).toFixed(1),
  );
  const aepGainRatio = computed(() =>
    (4.6 + Math.sin(trendCursor.value / 8) * 0.4).toFixed(2),
  );
  const aepRevenue = computed(() =>
    (Number(cumulativeAepGain.value) * 0.46).toFixed(1),
  );
  const reducedFatigueHours = computed(() =>
    (126.8 + trendCursor.value * 0.31).toFixed(1),
  );
  const towerLoadReduction = computed(() =>
    (8.4 + Math.sin(trendCursor.value / 7) * 0.8).toFixed(2),
  );
  const bladeDelReduction = computed(() =>
    (11.2 + Math.cos(trendCursor.value / 9) * 0.9).toFixed(2),
  );
  const currentFluctuationRate = computed(
    () =>
      fluctuationSeries[fluctuationSeries.length - 1]?.value.toFixed(2) ?? '--',
  );
  const fluctuationImprovement = computed(() => {
    const first = fluctuationSeries[0]?.value ?? 0;
    const last = fluctuationSeries[fluctuationSeries.length - 1]?.value ?? 0;
    return (first - last).toFixed(2);
  });

  function buildTrendOptions(config: {
    name: string;
    unit: string;
    color: string;
    fillColor: string;
    values: number[];
  }) {
    const minValue = Math.min(...config.values);
    const maxValue = Math.max(...config.values);
    const axisMin = Number(minValue.toFixed(2));
    const axisMax = Number(maxValue.toFixed(2));

    return {
      animation: false,
      grid: {
        top: 12,
        right: 14,
        bottom: 18,
        left: 8,
        containLabel: true,
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: appChartTheme.value.tooltipBg,
        borderColor: appChartTheme.value.tooltipBorder,
        textStyle: appChartTheme.value.tooltipTextStyle,
        valueFormatter: (value: number) => `${value.toFixed(2)} ${config.unit}`,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: trendSeries.value.map((item) => item.time),
        axisLabel: {
          color: appChartTheme.value.textMuted,
          fontSize: 10,
          interval: 19,
        },
        axisLine: {
          lineStyle: {
            color: appChartTheme.value.axisLine,
          },
        },
        axisTick: {
          show: false,
        },
      },
      yAxis: {
        type: 'value',
        min: axisMin,
        max: axisMax,
        axisLabel: {
          color: appChartTheme.value.textMuted,
          fontSize: 10,
          formatter: (value: number) => {
            const epsilon = 0.02;
            if (Math.abs(value - axisMin) < epsilon)
              return `${axisMin} ${config.unit}`;
            if (Math.abs(value - axisMax) < epsilon)
              return `${axisMax} ${config.unit}`;
            return '';
          },
        },
        splitLine: {
          lineStyle: {
            color: appChartTheme.value.splitLineSoft,
            type: 'dashed',
          },
        },
      },
      series: [
        {
          name: config.name,
          type: 'line',
          smooth: true,
          showSymbol: false,
          symbol: 'circle',
          lineStyle: {
            width: 2.5,
            color: config.color,
            shadowBlur: 16,
            shadowColor: config.color,
          },
          areaStyle: {
            color: config.fillColor,
          },
          data: config.values,
        },
      ],
    };
  }

  const activePowerOptions = computed(() =>
    buildTrendOptions({
      name: '全场实时有功功率',
      unit: 'MW',
      color: '#4cc9ff',
      fillColor: 'rgba(76, 201, 255, 0.14)',
      values: trendSeries.value.map((item) => item.activePower),
    }),
  );

  const reactivePowerOptions = computed(() =>
    buildTrendOptions({
      name: '全场无功功率',
      unit: 'MVar',
      color: '#32f0ff',
      fillColor: 'rgba(50, 240, 255, 0.12)',
      values: trendSeries.value.map((item) => item.reactivePower),
    }),
  );

  const averageWindSpeedOptions = computed(() =>
    buildTrendOptions({
      name: '全场平均风速',
      unit: 'm/s',
      color: '#61ffb2',
      fillColor: 'rgba(97, 255, 178, 0.12)',
      values: trendSeries.value.map((item) => item.averageWindSpeed),
    }),
  );

  const utilizationGaugeOptions = computed(() => ({
    animation: false,
    series: [
      {
        type: 'gauge',
        center: ['50%', '56%'],
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        radius: '100%',
        splitNumber: 5,
        progress: {
          show: true,
          width: 14,
          itemStyle: {
            color: '#2f88ff',
          },
        },
        pointer: {
          show: false,
        },
        axisLine: {
          lineStyle: {
            width: 14,
            color: [[1, 'rgba(47, 136, 255, 0.18)']],
          },
        },
        axisTick: {
          distance: -18,
          splitNumber: 4,
          lineStyle: {
            width: 2,
            color: 'rgba(47, 136, 255, 0.42)',
          },
        },
        splitLine: {
          distance: -18,
          length: 12,
          lineStyle: {
            width: 3,
            color: 'rgba(47, 136, 255, 0.58)',
          },
        },
        axisLabel: {
          distance: 6,
          color: chartTextColor.value,
          fontSize: 11,
        },
        anchor: {
          show: false,
        },
        title: {
          show: false,
          offsetCenter: [0, '34%'],
          color: chartTextColor.value,
          fontSize: 11,
        },
        detail: {
          valueAnimation: false,
          offsetCenter: [0, '8%'],
          formatter: (value: number) => `${value.toFixed(1)}%`,
          color: chartTextColor.value,
          fontSize: 26,
          fontWeight: 700,
        },
        data: [
          {
            value: Number(utilizationRatio.value.toFixed(1)),
            name: '风能利用率',
          },
        ],
      },
    ],
  }));

  const fluctuationTrendOptions = computed(() => {
    const values = fluctuationSeries.map((item) => item.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    return {
      animation: false,
      grid: {
        top: 12,
        right: 8,
        bottom: 18,
        left: 4,
        containLabel: true,
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: appChartTheme.value.tooltipBg,
        borderColor: appChartTheme.value.tooltipBorder,
        textStyle: appChartTheme.value.tooltipTextStyle,
        valueFormatter: (value: number) => `${value.toFixed(2)}%`,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: fluctuationSeries.map((item) => item.label),
        axisLabel: {
          color: appChartTheme.value.textMuted,
          fontSize: 10,
          interval: 4,
        },
        axisLine: {
          lineStyle: {
            color: appChartTheme.value.axisLine,
          },
        },
        axisTick: {
          show: false,
        },
      },
      yAxis: {
        type: 'value',
        min: Number(minValue.toFixed(2)),
        max: Number(maxValue.toFixed(2)),
        axisLabel: {
          color: appChartTheme.value.textMuted,
          fontSize: 10,
          formatter: (value: number) => {
            const epsilon = 0.02;
            if (Math.abs(value - minValue) < epsilon)
              return `${minValue.toFixed(2)}%`;
            if (Math.abs(value - maxValue) < epsilon)
              return `${maxValue.toFixed(2)}%`;
            return '';
          },
        },
        splitLine: {
          lineStyle: {
            color: appChartTheme.value.splitLineSoft,
            type: 'dashed',
          },
        },
      },
      series: [
        {
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 2.5,
            color: '#2f88ff',
          },
          areaStyle: {
            color: 'rgba(47, 136, 255, 0.12)',
          },
          data: values,
        },
      ],
    };
  });

  onMounted(async () => {
    syncChartTextColor();
    await nextTick();
    loading.value = {
      utilization: false,
      aep: false,
      fatigue: false,
      fluctuation: false,
      trend: false,
    };
  });

  watch(
    () => appStore.theme,
    () => {
      window.requestAnimationFrame(() => {
        syncChartTextColor();
      });
    },
  );

  onBeforeUnmount(() => {
    if (trendTimer) {
      window.clearInterval(trendTimer);
      trendTimer = undefined;
    }
  });
</script>

<script lang="ts">
  export default {
    name: 'Dashboard',
  };
</script>

<style scoped lang="less">
  .dashboard-screen {
    position: relative;
    height: calc(100vh - 64px);
    min-height: 720px;
    overflow: hidden;
    background: #06111f;
  }

  .viewer-layer {
    position: absolute;
    inset: 0;
  }

  .overlay {
    position: absolute;
    z-index: 2;
    pointer-events: none;
  }

  .overlay-right {
    top: 20px;
    right: 20px;
    bottom: 20px;
    width: min(360px, 28vw);
    display: grid;
    grid-template-rows: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }

  .overlay-left-bottom {
    left: 20px;
    bottom: 20px;
    width: min(360px, 28vw);
  }

  .trend-panel-card {
    position: relative;
    height: 100%;
    pointer-events: auto;
    overflow: hidden;
  }

  .trend-panel-card::before {
    content: none;
  }

  .floating-card {
    height: 100%;
    pointer-events: auto;
  }

  .floating-card-large {
    height: 380px;
  }

  :deep(.floating-card.arco-card) {
    display: flex;
    flex-direction: column;
    background-color: color-mix(in srgb, var(--color-bg-2) 50%, transparent);
    border-color: color-mix(in srgb, var(--color-border-2) 58%, transparent);
    backdrop-filter: blur(12px);
    box-shadow: 0 18px 48px rgb(0 0 0 / 18%);
  }

  :deep(.floating-card .arco-card-header) {
    flex: 0 0 auto;
    background-color: color-mix(in srgb, var(--color-fill-2) 36%, transparent);
    border-bottom-color: color-mix(
      in srgb,
      var(--color-border-2) 52%,
      transparent
    );
  }

  :deep(.floating-card .arco-card-title) {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.01em;
  }

  :deep(.floating-card .arco-card-body) {
    flex: 1 1 auto;
    min-height: 0;
    padding: 14px 16px 12px;
  }

  .card-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 10px;
    line-height: 1.6;
  }

  .card-content p {
    margin: 0;
    font-size: 14px;
  }

  .monitor-card-content {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
  }

  .monitor-card-title {
    margin-bottom: 6px;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.35;
    color: var(--color-text-1);
    letter-spacing: 0.01em;
  }

  .gauge-card-content {
    gap: 4px;
  }

  .gauge-card-content :deep(.echarts) {
    flex: 1 1 auto;
    min-height: 0;
  }

  .gauge-card-stats {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .gauge-stat,
  .metric-detail-item,
  .fluctuation-summary-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid color-mix(in srgb, var(--color-border-2) 48%, transparent);
    background: transparent;
  }

  .gauge-stat-label,
  .metric-detail-label {
    font-size: 12px;
    line-height: 1.4;
    color: var(--color-text-3);
  }

  .gauge-stat-value,
  .metric-detail-value {
    font-size: 16px;
    line-height: 1.3;
    font-weight: 700;
    color: var(--color-text-1);
  }

  .value-card-content {
    justify-content: space-between;
  }

  .metric-value-group {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin: 2px 0 8px;
  }

  .metric-value-primary {
    font-size: 42px;
    line-height: 0.95;
    font-weight: 700;
    color: var(--color-text-1);
    letter-spacing: -0.03em;
  }

  .metric-value-unit {
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text-2);
  }

  .metric-footnote {
    margin-bottom: 12px;
    font-size: 12px;
    line-height: 1.6;
    color: var(--color-text-3);
  }

  .metric-detail-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .fluctuation-card-content {
    gap: 8px;
  }

  .fluctuation-summary {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .fluctuation-card-content :deep(.echarts) {
    flex: 1 1 auto;
    min-height: 0;
  }

  .monitor-card :deep(.arco-card-header) {
    display: none;
  }

  .monitor-card :deep(.arco-card-body) {
    padding-top: 12px;
  }

  .trend-panel {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .trend-chart-grid {
    flex: 1 1 auto;
    min-height: 0;
    display: grid;
    grid-template-rows: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .trend-chart-box {
    display: flex;
    flex-direction: column;
    min-height: 0;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
    overflow: hidden;
  }

  .trend-chart-meta {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 4px;
  }

  .trend-chart-title {
    font-size: 13px;
    font-weight: 700;
    line-height: 1.35;
    color: var(--color-text-1);
    letter-spacing: 0.02em;
  }

  .trend-chart-value {
    font-size: 17px;
    line-height: 1.2;
    font-weight: 700;
    color: var(--color-text-1);
    white-space: nowrap;
  }

  .trend-chart-box :deep(.echarts) {
    flex: 1 1 auto;
    min-height: 0;
  }

  .trend-panel-card :deep(.arco-card-header) {
    display: none;
  }

  .trend-panel-card :deep(.arco-card) {
    background-color: color-mix(in srgb, var(--color-bg-2) 50%, transparent);
    border-color: color-mix(in srgb, var(--color-border-2) 58%, transparent);
    backdrop-filter: blur(12px);
    box-shadow: 0 18px 48px rgb(0 0 0 / 18%);
  }

  .trend-panel-card :deep(.arco-card-body) {
    position: relative;
    z-index: 1;
    height: 100%;
    padding: 12px 14px;
  }

  @media (max-width: 1280px) {
    .dashboard-screen {
      min-height: 640px;
    }

    .overlay-right {
      width: min(320px, 32vw);
      gap: 12px;
    }

    .overlay-left-bottom {
      width: min(320px, 32vw);
    }

    .trend-panel-card {
      height: 350px;
    }
  }

  @media (max-width: 960px) {
    .overlay-right {
      top: auto;
      right: 12px;
      bottom: 12px;
      width: calc(50% - 18px);
      height: 420px;
    }

    .overlay-left-bottom {
      left: 12px;
      bottom: 12px;
      width: calc(50% - 18px);
    }

    .floating-card-large {
      height: 360px;
    }

    .trend-panel-card {
      height: 330px;
    }
  }

  @media (max-width: 768px) {
    .dashboard-screen {
      min-height: auto;
    }

    .overlay-right,
    .overlay-left-bottom {
      left: 12px;
      right: 12px;
      width: auto;
    }

    .overlay-right {
      top: 12px;
      bottom: auto;
      height: auto;
      grid-template-rows: repeat(4, minmax(110px, auto));
    }

    .overlay-left-bottom {
      bottom: 12px;
    }

    .floating-card-large {
      height: 340px;
    }

    .trend-panel-card {
      height: 310px;
    }
  }
</style>
