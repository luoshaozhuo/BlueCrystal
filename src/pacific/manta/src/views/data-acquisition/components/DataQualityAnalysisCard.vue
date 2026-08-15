<template>
  <div class="quality-grid">
    <div class="quality-grid__cell">
      <VChart class="quality-grid__chart" :option="completenessOption" autoresize />
    </div>
    <div class="quality-grid__cell">
      <VChart class="quality-grid__chart" :option="syncOption" autoresize />
    </div>
    <div class="quality-grid__cell">
      <VChart class="quality-grid__chart" :option="anomalyOption" autoresize />
    </div>
    <div class="quality-grid__cell">
      <VChart class="quality-grid__chart" :option="latencyOption" autoresize />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { BarChart, LineChart, PieChart } from 'echarts/charts';
  import type { BarSeriesOption, LineSeriesOption, PieSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    LegendComponent,
    MarkLineComponent,
    TitleComponent,
    TooltipComponent,
    type GridComponentOption,
    type LegendComponentOption,
    type TitleComponentOption,
    type TooltipComponentOption,
  } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
  import { CHART_SERIES_COLORS, useChartTheme, withAlpha } from '@/config/chart-theme';
  import type { DataQualityAnalysisData, DataQualityAnomalyKey, DataQualityLatencyKey, DataQualitySyncBinKey } from '@/mock/data-acquisition';

  use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent, MarkLineComponent]);

  type ECOption = ComposeOption<
    | BarSeriesOption
    | LineSeriesOption
    | PieSeriesOption
    | GridComponentOption
    | LegendComponentOption
    | TitleComponentOption
    | TooltipComponentOption
  >;

  const props = defineProps<{ data: DataQualityAnalysisData }>();
  const chartTheme = useChartTheme();
  const syncBinLabels: Record<DataQualitySyncBinKey, string> = {
    lt10ms: '<10ms',
    ms10to20: '10-20ms',
    ms20to50: '20-50ms',
    ms50to100: '50-100ms',
    gt100ms: '>100ms',
  };
  const anomalyLabels: Record<DataQualityAnomalyKey, string> = {
    missing: '缺测',
    outOfRange: '越限',
    duplicate: '重复',
    jump: '跳变',
    timeMisalignment: '时间错位',
  };
  const latencyLabels: Record<DataQualityLatencyKey, string> = {
    p50: 'P50',
    p75: 'P75',
    p90: 'P90',
    p95: 'P95',
    p99: 'P99',
  };
  const completenessColor = computed(() => chartTheme.value.success);
  const avgCompleteness = computed(
    () => props.data.completenessTrend.reduce((sum, item) => sum + item.value, 0) / Math.max(props.data.completenessTrend.length, 1),
  );

  const completenessOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '完整率趋势',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    legend: {
      top: 4,
      right: 8,
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      data: ['完整率', '均值'],
    },
    grid: { left: 48, right: 16, top: 28, bottom: 34, containLabel: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'category',
      name: '时间',
      nameLocation: 'middle',
      nameGap: 24,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      data: props.data.completenessTrend.map((item) => item.time),
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, interval: 4 },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '完整率(%)',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      min: 98.4,
      max: 99.6,
      axisLabel: {
        color: chartTheme.value.textMuted,
        fontSize: 10,
        formatter: (value: number) => Number(value).toPrecision(4),
        margin: 6,
      },
      splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbolSize: 6,
        name: '完整率',
        color: completenessColor.value,
        data: props.data.completenessTrend.map((item) => item.value),
        lineStyle: { width: 2, color: completenessColor.value },
        itemStyle: { color: completenessColor.value },
        areaStyle: { color: completenessColor.value, opacity: 0.18 },
        emphasis: {
          disabled: true,
          areaStyle: { color: completenessColor.value, opacity: 0.18 },
        },
      },
      {
        type: 'line',
        smooth: false,
        symbol: 'none',
        name: '均值',
        data: props.data.completenessTrend.map(() => Number(avgCompleteness.value.toFixed(2))),
        lineStyle: { width: 2, color: chartTheme.value.warning, type: 'dashed' },
        itemStyle: { color: chartTheme.value.warning },
        tooltip: { show: false },
      },
    ],
  }));

  const syncOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '时间同步误差分布',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    grid: { left: 40, right: 16, top: 30, bottom: 34, containLabel: false },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'category',
      name: '误差区间',
      nameLocation: 'middle',
      nameGap: 24,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      data: props.data.syncDiffBins.map((item) => syncBinLabels[item.key]),
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, interval: 0 },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '设备数',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10 },
      splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
    },
    series: [
      {
        type: 'bar',
        barWidth: 18,
        data: props.data.syncDiffBins.map((item, index) => ({
          value: item.value,
          itemStyle: { color: index < 2 ? chartTheme.value.success : index < 4 ? chartTheme.value.warning : chartTheme.value.danger },
        })),
      },
    ],
  }));

  const anomalyOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '数据异常原因占比',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
      formatter: (params: any) => {
        const source = props.data.anomalyRatio.find((item) => anomalyLabels[item.key] === params.name);
        return `${params.name}<br/>占比：${params.value}%<br/>样本数：${source?.count ?? 0}`;
      },
    },
    legend: {
      left: 'center',
      bottom: 6,
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      data: props.data.anomalyRatio.map((item) => anomalyLabels[item.key]),
    },
    series: [
      {
        type: 'pie',
        radius: ['38%', '56%'],
        center: ['50%', '50%'],
        label: { show: false },
        labelLine: { show: false },
        data: props.data.anomalyRatio.map((item, index) => ({
          name: anomalyLabels[item.key],
          value: Number((item.value * 100).toFixed(2)),
          itemStyle: {
            color: CHART_SERIES_COLORS[index] ?? CHART_SERIES_COLORS[0],
          },
        })),
      },
    ],
  }));

  const latencyOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '延迟分位分布',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    grid: { left: 40, right: 16, top: 30, bottom: 34, containLabel: false },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'category',
      name: '分位点',
      nameLocation: 'middle',
      nameGap: 24,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      data: props.data.latencyQuantiles.map((item) => latencyLabels[item.key]),
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, interval: 0 },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '时延(ms)',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10 },
      splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
    },
    series: [
      {
        type: 'bar',
        barWidth: 18,
        data: props.data.latencyQuantiles.map((item) => ({
          value: item.value,
          itemStyle: {
            color: item.key === 'p95' ? chartTheme.value.warning : item.key === 'p99' ? chartTheme.value.danger : chartTheme.value.primary,
          },
        })),
        markLine: {
          symbol: 'none',
          silent: true,
          lineStyle: { color: withAlpha(chartTheme.value.danger, 0.35), type: 'dashed' },
          label: {
            color: chartTheme.value.textFaint,
            fontSize: 10,
            formatter: '120ms',
            position: 'insideEndTop',
            distance: 6,
          },
          data: [{ yAxis: 120 }],
        },
      },
      {
        type: 'line',
        smooth: true,
        symbolSize: 6,
        data: props.data.latencyQuantiles.map((item) => item.value),
        lineStyle: { width: 2, color: chartTheme.value.success },
        itemStyle: { color: chartTheme.value.success },
      },
    ],
  }));
</script>

<style scoped lang="less">
  .quality-grid {
    width: 100%;
    height: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 6px;
    min-height: 0;
  }

  .quality-grid__cell {
    min-width: 0;
    min-height: 0;
    overflow: hidden;
  }

  .quality-grid__chart {
    width: 100%;
    height: 100%;
    min-height: 0;
  }
</style>
