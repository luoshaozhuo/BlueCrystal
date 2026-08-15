<template>
  <div class="gust-analysis">
    <a-row class="gust-analysis__grid" :gutter="8">
      <a-col :span="12" class="gust-analysis__col">
        <a-row class="gust-analysis__stack" :gutter="[0, 8]">
          <a-col :span="24" class="gust-analysis__cell">
            <section class="subpanel">
              <div class="subpanel__head">
                <div class="subpanel__title">扰动模板与样本分布</div>
                <div class="subpanel__meta">
                  <span>峰值扰动 {{ disturbancePeakText }}</span>
                  <span>持续时间 {{ disturbanceDurationText }}</span>
                </div>
              </div>
              <VChart class="subpanel__chart" :option="disturbanceTemplateOption" autoresize />
            </section>
          </a-col>

          <a-col :span="24" class="gust-analysis__cell">
            <section class="subpanel">
              <div class="subpanel__head">
                <div class="subpanel__title">功率响应对比</div>
                <div class="subpanel__meta">
                  <span>峰值提升 {{ peakGainText }}</span>
                  <span>响应提前 {{ responseLeadText }}</span>
                </div>
              </div>
              <VChart class="subpanel__chart" :option="powerResponseOption" autoresize />
            </section>
          </a-col>
        </a-row>
      </a-col>

      <a-col :span="12" class="gust-analysis__col">
        <a-row class="gust-analysis__stack" :gutter="[0, 8]">
          <a-col :span="24" class="gust-analysis__cell gust-analysis__cell--overview">
            <section class="subpanel">
              <div class="subpanel__head subpanel__head--spaced">
                <div class="subpanel__title">事件概览</div>
              </div>
              <div class="overview-grid">
                <div v-for="item in overviewItems" :key="item.label" class="overview-grid__item">
                  <div class="overview-grid__label">{{ item.label }}</div>
                  <div class="overview-grid__value">{{ item.value }}</div>
                  <div class="overview-grid__note">{{ item.note }}</div>
                </div>
              </div>
            </section>
          </a-col>

            <a-col :span="24" class="gust-analysis__cell gust-analysis__cell--timeline">
            <section class="subpanel">
              <div class="subpanel__head subpanel__head--spaced">
                <div class="subpanel__title">关键特征时间轴</div>
              </div>
              <VChart class="subpanel__chart" :option="timelineOption" autoresize />
            </section>
          </a-col>

            <a-col :span="24" class="gust-analysis__cell gust-analysis__cell--metrics">
            <section class="subpanel">
              <div class="subpanel__head subpanel__head--spaced">
                <div class="subpanel__title">指标对比</div>
              </div>
              <a-table
                class="metric-table"
                :columns="metricColumns"
                :data="metricRows"
                :bordered="false"
                :pagination="false"
                size="mini"
                row-key="name"
              >
                <template #diff="{ record }">
                  <span :class="['metric-table__diff', record.improved ? 'metric-table__diff--good' : 'metric-table__diff--warn']">
                    {{ record.diff }}
                  </span>
                </template>
              </a-table>
            </section>
          </a-col>
        </a-row>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { BarChart, CustomChart, LineChart, ScatterChart } from 'echarts/charts';
  import type { BarSeriesOption, CustomSeriesOption, LineSeriesOption, ScatterSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    MarkAreaComponent,
    MarkPointComponent,
    TooltipComponent,
    type GridComponentOption,
    type TooltipComponentOption,
  } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS, useChartTheme, useThemeTokens, withAlpha } from '@/config/chart-theme';
  import type { GustMetricComparisonRow, GustResponseCardData } from '@/types/power-analysis';

  use([
    CanvasRenderer,
    BarChart,
    CustomChart,
    LineChart,
    ScatterChart,
    GridComponent,
    MarkAreaComponent,
    MarkPointComponent,
    TooltipComponent,
  ]);

  type ECOption = ComposeOption<
    | BarSeriesOption
    | CustomSeriesOption
    | LineSeriesOption
    | ScatterSeriesOption
    | GridComponentOption
    | TooltipComponentOption
  >;

  interface MetricRowView {
    name: string;
    baseline: string;
    optimized: string;
    diff: string;
    improved: boolean;
  }

  interface MetricColumn {
    title: string;
    dataIndex: 'name' | 'baseline' | 'optimized' | 'diff';
    slotName?: 'diff';
    align?: 'left' | 'center' | 'right';
  }

  const props = defineProps<{
    data: GustResponseCardData;
  }>();

  const themeTokens = useThemeTokens();
  const chartTheme = useChartTheme();
  const ANALYSIS_BASELINE_COLOR = CHART_COMPARISON_COLORS.baseline;
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;
  const positiveDiffColor = themeTokens.success4;
  const warningDiffColor = themeTokens.warning4;
  const dividerColor = themeTokens.splitLineSoft;
  const metricLabels: Record<GustMetricComparisonRow['key'], string> = {
    responseStart: '响应起点',
    t10: '10%到时',
    peak: '峰值',
    peakTime: '峰值时刻',
    recoveryTime: '恢复时刻',
    rms: 'RMS波动',
  };

  const disturbanceDuration = computed(
    () => props.data.disturbanceTemplate.disturbanceEnd - props.data.disturbanceTemplate.disturbanceStart,
  );
  const peakGain = computed(() => {
    const baselinePeak = Math.max(...props.data.powerResponse.baseline);
    const optimizedPeak = Math.max(...props.data.powerResponse.optimized);
    return optimizedPeak - baselinePeak;
  });
  const responseLead = computed(
    () => props.data.featureTimeline.baseline.responseStart - props.data.featureTimeline.optimized.responseStart,
  );

  const disturbancePeakText = computed(() => `${props.data.disturbanceTemplate.peakValue.toFixed(2)} m/s`);
  const disturbanceDurationText = computed(() => `${disturbanceDuration.value.toFixed(1)} s`);
  const peakGainText = computed(() => `${peakGain.value.toFixed(2)} MW`);
  const responseLeadText = computed(() => `${responseLead.value.toFixed(1)} s`);

  const confidenceText = computed(() => {
    const retention = props.data.overview.sampleRetentionRate;
    const align = props.data.overview.alignSuccessRate;
    if (retention >= 80 && align >= 90) return '样本可信';
    if (retention >= 70 && align >= 85) return '样本可用';
    return '需关注';
  });

  const confidenceNote = computed(() => {
    if (confidenceText.value === '样本可信') return '样本稳定';
    if (confidenceText.value === '样本可用') return '可用于判断';
    return '建议复核';
  });

  const overviewItems = computed(() => [
    {
      label: '有效事件数',
      value: `${props.data.overview.eventCount}`,
      note: '对齐后保留',
    },
    {
      label: '覆盖机组数',
      value: `${props.data.overview.turbineCount}`,
      note: '样本来源',
    },
    {
      label: '对齐成功率',
      value: `${props.data.overview.alignSuccessRate.toFixed(1)}%`,
      note: '事件对齐质量',
    },
    {
      label: '样本保留率',
      value: `${props.data.overview.sampleRetentionRate.toFixed(1)}%`,
      note: confidenceNote.value,
    },
    {
      label: '中位持续时长',
      value: `${props.data.overview.medianDuration.toFixed(1)}s`,
      note: '典型事件长度',
    },
    {
      label: '分析时间窗',
      value: `${props.data.overview.windowSec}s`,
      note: '统一对齐窗口',
    },
  ]);

  function formatMetric(value: number, unit: string) {
    return unit === 'MW' ? `${value.toFixed(2)}${unit}` : `${value.toFixed(1)}${unit}`;
  }

  function isImproved(row: GustMetricComparisonRow) {
    if (row.key === 'peak') return row.diff > 0;
    return row.diff < 0;
  }

  const metricRows = computed<MetricRowView[]>(() =>
    props.data.metricComparison.map((row) => ({
      name: metricLabels[row.key],
      baseline: formatMetric(row.baseline, row.unit),
      optimized: formatMetric(row.optimized, row.unit),
      diff: `${row.diff > 0 ? '+' : ''}${row.diff.toFixed(row.unit === 'MW' ? 2 : 1)}${row.unit}`,
      improved: isImproved(row),
    })),
  );

  const metricColumns: MetricColumn[] = [
    { title: '指标', dataIndex: 'name', align: 'left' },
    { title: '基准', dataIndex: 'baseline', align: 'right' },
    { title: '优化后', dataIndex: 'optimized', align: 'right' },
    { title: '差值', dataIndex: 'diff', slotName: 'diff', align: 'right' },
  ];

  const disturbanceTemplateOption = computed<ECOption>(() => {
    const { time, mean, lower, upper, disturbanceStart, disturbanceEnd, peakTime, peakValue } = props.data.disturbanceTemplate;
    const allValues = [...lower, ...upper, ...mean, peakValue];
    const rawMin = Math.min(...allValues);
    const rawMax = Math.max(...allValues);
    const padding = Math.max((rawMax - rawMin) * 0.08, 0.06);
    return {
      animationDuration: 260,
      grid: { left: 48, right: 18, top: 14, bottom: 26, containLabel: true },
      tooltip: {
        trigger: 'axis',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
      },
      xAxis: {
        type: 'value',
        name: '时间(s)',
        nameLocation: 'middle',
        nameGap: 24,
        nameTextStyle: { color: themeTokens.text3, fontSize: 10 },
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '风速扰动量(m/s)',
        min: Number((rawMin - padding).toFixed(2)),
        max: Number((rawMax + padding).toFixed(2)),
        nameLocation: 'middle',
        nameGap: 34,
        nameTextStyle: { color: themeTokens.text3, fontSize: 10 },
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        splitLine: { lineStyle: { color: themeTokens.splitLineSoft } },
      },
      series: [
        {
          type: 'custom',
          name: '样本带',
          silent: true,
          data: [[0, 0]],
          renderItem(params: any, api: any) {
            const upperPoints = time.map((point, index) => api.coord([point, upper[index]]));
            const lowerPoints = time.map((point, index) => api.coord([point, lower[index]])).reverse();
            return {
              type: 'polygon',
              shape: { points: [...upperPoints, ...lowerPoints] },
              style: { fill: withAlpha(ANALYSIS_OPTIMIZED_COLOR, 0.16) },
              silent: true,
            };
          },
        },
        {
          type: 'line',
          name: '扰动模板',
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 2.2, color: ANALYSIS_OPTIMIZED_COLOR },
          data: time.map((point, index) => [point, mean[index]]),
          markArea: {
            silent: true,
            itemStyle: { color: themeTokens.markerFill },
            data: [[{ xAxis: disturbanceStart }, { xAxis: disturbanceEnd }]],
          },
          markPoint: {
            symbolSize: 8,
            itemStyle: { color: ANALYSIS_OPTIMIZED_COLOR },
            label: {
              color: themeTokens.text2,
              fontSize: 10,
              formatter(params: any) {
                const labels: Record<string, string> = { start: '起始', peak: '峰值', recover: '恢复' };
                return labels[params.data?.name] ?? '';
              },
            },
            data: [
              { name: 'start', coord: [disturbanceStart, mean[time.findIndex((item) => item === disturbanceStart)] ?? 0.12], label: { position: 'left' } },
              { name: 'peak', coord: [peakTime, peakValue], label: { position: 'top' } },
              { name: 'recover', coord: [disturbanceEnd, mean[time.findIndex((item) => item === disturbanceEnd)] ?? 0.38], label: { position: 'right' } },
            ],
          },
        },
      ],
    };
  });

  const powerResponseOption = computed<ECOption>(() => {
    const { time, baseline, optimized, baselineBandLow, baselineBandHigh, optimizedBandLow, optimizedBandHigh } = props.data.powerResponse;
    const { baseline: baselineFeature, optimized: optimizedFeature } = props.data.featureTimeline;
    const allValues = [
      ...baselineBandLow,
      ...baselineBandHigh,
      ...optimizedBandLow,
      ...optimizedBandHigh,
      ...baseline,
      ...optimized,
    ];
    const rawMin = Math.min(...allValues);
    const rawMax = Math.max(...allValues);
    const padding = Math.max((rawMax - rawMin) * 0.08, 0.12);
    return {
      animationDuration: 280,
      tooltip: {
        trigger: 'axis',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
      },
      legend: {
        top: 6,
        right: 10,
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { color: themeTokens.text3, fontSize: 10 },
        data: [
          {
            name: '基准',
            icon: 'roundRect',
            itemStyle: { color: ANALYSIS_BASELINE_COLOR },
          },
          {
            name: '优化后',
            icon: 'roundRect',
            itemStyle: { color: ANALYSIS_OPTIMIZED_COLOR },
          },
        ],
      },
      grid: { left: 52, right: 18, top: 32, bottom: 28, containLabel: true },
      xAxis: {
        type: 'value',
        name: '时间(s)',
        nameLocation: 'middle',
        nameGap: 24,
        nameTextStyle: { color: themeTokens.text3, fontSize: 10 },
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: themeTokens.splitLineSoft } },
      },
      yAxis: {
        type: 'value',
        name: '功率(MW)',
        min: Number((rawMin - padding).toFixed(2)),
        max: Number((rawMax + padding).toFixed(2)),
        nameLocation: 'middle',
        nameGap: 38,
        nameTextStyle: { color: themeTokens.text3, fontSize: 10 },
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        splitLine: { lineStyle: { color: themeTokens.splitLineSoft } },
      },
      series: [
        {
          type: 'custom',
          name: '基准波动带',
          silent: true,
          data: [[0, 0]],
          renderItem(params: any, api: any) {
            const upperPoints = time.map((point, index) => api.coord([point, baselineBandHigh[index]]));
            const lowerPoints = time.map((point, index) => api.coord([point, baselineBandLow[index]])).reverse();
            return {
              type: 'polygon',
              shape: { points: [...upperPoints, ...lowerPoints] },
              style: { fill: withAlpha(ANALYSIS_BASELINE_COLOR, 0.12) },
              silent: true,
            };
          },
        },
        {
          type: 'custom',
          name: '优化后波动带',
          silent: true,
          data: [[0, 0]],
          renderItem(params: any, api: any) {
            const upperPoints = time.map((point, index) => api.coord([point, optimizedBandHigh[index]]));
            const lowerPoints = time.map((point, index) => api.coord([point, optimizedBandLow[index]])).reverse();
            return {
              type: 'polygon',
              shape: { points: [...upperPoints, ...lowerPoints] },
              style: { fill: withAlpha(ANALYSIS_OPTIMIZED_COLOR, 0.12) },
              silent: true,
            };
          },
        },
        {
          name: '基准',
          type: 'line',
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 2, color: ANALYSIS_BASELINE_COLOR },
          data: time.map((point, index) => [point, baseline[index]]),
        },
        {
          name: '优化后',
          type: 'line',
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 2.4, color: ANALYSIS_OPTIMIZED_COLOR },
          data: time.map((point, index) => [point, optimized[index]]),
          markPoint: {
            symbolSize: 9,
            itemStyle: { color: ANALYSIS_OPTIMIZED_COLOR },
            label: {
              color: themeTokens.text2,
              fontSize: 10,
              formatter(params: any) {
                const labelMap: Record<string, string> = {
                  start: '响应起点',
                  t10: '10%时刻',
                  peak: '峰值',
                  recover: '恢复时刻',
                };
                return labelMap[params.data?.name] ?? '';
              },
            },
            data: [
              { name: 'start', coord: [optimizedFeature.responseStart, optimized[time.findIndex((item) => item === 8)] ?? optimized[4]], label: { position: 'left' } },
              { name: 't10', coord: [optimizedFeature.t10, optimized[time.findIndex((item) => item === 14)] ?? optimized[7]], label: { position: 'top' } },
              { name: 'peak', coord: [optimizedFeature.peakTime, Math.max(...optimized)], label: { position: 'top' } },
              { name: 'recover', coord: [optimizedFeature.recoveryTime, optimized[time.findIndex((item) => item === 28)] ?? optimized[14]], label: { position: 'right' } },
            ],
          },
        },
      ],
    };
  });

  const timelineOption = computed<ECOption>(() => {
    const baseline = props.data.featureTimeline.baseline;
    const optimized = props.data.featureTimeline.optimized;
    const windowSec = props.data.overview.windowSec;
    const startMarkerOffset = 0.8;
    const categories = ['基准', '优化后'];
    const points = [
      { row: 0, values: baseline, color: ANALYSIS_BASELINE_COLOR },
      { row: 1, values: optimized, color: ANALYSIS_OPTIMIZED_COLOR },
    ];
    const labels = ['开始', '响应起点', '10%到时', '峰值', '恢复时刻', '结束'];
    return {
      animationDuration: 220,
      grid: { left: 32, right: 32, top: 14, bottom: 8, containLabel: true },
      tooltip: {
        trigger: 'item',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
      },
      xAxis: {
        type: 'value',
        min: 0,
        max: windowSec,
        show: false,
        splitLine: { show: false },
      },
      yAxis: {
        type: 'category',
        data: categories,
        axisLabel: { color: themeTokens.text3, fontSize: 10, margin: 8 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        ...points.map((item) => ({
          type: 'line' as const,
          data: [
            [startMarkerOffset, item.row],
            [item.values.responseStart, item.row],
            [item.values.t10, item.row],
            [item.values.peakTime, item.row],
            [item.values.recoveryTime, item.row],
            [windowSec, item.row],
          ],
          showSymbol: true,
          symbolSize: 8,
          lineStyle: { width: 2, color: item.color },
          itemStyle: { color: item.color },
        })),
        {
          type: 'scatter',
          data: [
            [startMarkerOffset, 0, labels[0]],
            [baseline.responseStart, 0, labels[1]],
            [baseline.t10, 0, labels[2]],
            [baseline.peakTime, 0, labels[3]],
            [baseline.recoveryTime, 0, labels[4]],
            [windowSec, 0, labels[5]],
            [startMarkerOffset, 1, labels[0]],
            [optimized.responseStart, 1, labels[1]],
            [optimized.t10, 1, labels[2]],
            [optimized.peakTime, 1, labels[3]],
            [optimized.recoveryTime, 1, labels[4]],
            [windowSec, 1, labels[5]],
          ],
          symbolSize: 1,
          label: {
            show: true,
            color: themeTokens.text3,
            fontSize: 9,
            formatter(params: any) {
              return params.value?.[2] ?? '';
            },
            position: 'top',
          },
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .gust-analysis {
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  .gust-analysis__grid,
  .gust-analysis__col,
  .gust-analysis__stack,
  .gust-analysis__cell {
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  .gust-analysis__stack {
    display: flex;
    flex-direction: column;
  }

  .gust-analysis__cell {
    flex: 1 1 0;
  }

  .gust-analysis__cell--overview {
    flex: 2 1 0;
  }

  .gust-analysis__cell--timeline {
    flex: 3 1 0;
  }

  .gust-analysis__cell--metrics {
    flex: 5 1 0;
  }

  .subpanel {
    height: 100%;
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    padding: 8px 10px;
    overflow: hidden;
    box-sizing: border-box;
  }

  .subpanel__head {
    position: relative;
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    gap: 8px;
    margin-bottom: 6px;
    flex: 0 0 auto;
    min-height: 0;
  }

  .subpanel__title {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    color: v-bind('chartTheme.titleTextStyle.color');
    font-size: v-bind('`${chartTheme.titleTextStyle.fontSize}px`');
    font-weight: v-bind('chartTheme.titleTextStyle.fontWeight');
    line-height: v-bind('`${chartTheme.titleTextStyle.lineHeight}px`');
    text-align: center;
    white-space: nowrap;
  }

  .subpanel__meta {
    display: flex;
    gap: 10px;
    color: var(--color-text-3);
    font-size: 10px;
    line-height: 1.2;
    white-space: nowrap;
    flex: 0 0 auto;
  }

  .subpanel__head--spaced {
    margin-bottom: 20px;
  }

  .subpanel__chart {
    width: 100%;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }

  .overview-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 6px;
    min-height: 0;
    overflow: hidden;
  }

  .overview-grid__item {
    min-width: 0;
    padding: 6px 8px;
    border-radius: 8px;
  }

  .overview-grid__label {
    color: var(--color-text-3);
    font-size: 10px;
    line-height: 1.2;
  }

  .overview-grid__value {
    margin-top: 4px;
    color: var(--color-text-1);
    font-size: 14px;
    font-weight: 700;
    line-height: 1;
  }

  .overview-grid__note {
    margin-top: 4px;
    color: var(--color-text-4);
    font-size: 10px;
    line-height: 1.2;
  }

  .metric-table {
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }

  .metric-table__diff {
    font-weight: 600;
  }

  .metric-table__diff--good {
    color: v-bind(positiveDiffColor);
  }

  .metric-table__diff--warn {
    color: v-bind(warningDiffColor);
  }

  .metric-table :deep(.arco-table-container) {
    height: 100%;
    background: transparent;
  }

  .metric-table :deep(.arco-table-content),
  .metric-table :deep(.arco-table-body) {
    height: 100%;
    background: transparent;
  }

  .metric-table :deep(.arco-table-th),
  .metric-table :deep(.arco-table-td) {
    padding: 4px 8px;
    background: transparent;
    border-bottom-color: v-bind(dividerColor);
    color: var(--color-text-2);
    font-size: 11px;
  }

  .metric-table :deep(.arco-table-th) {
    color: var(--color-text-3);
    font-size: 10px;
    font-weight: 600;
  }
</style>
