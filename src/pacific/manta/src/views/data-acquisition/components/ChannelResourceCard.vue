<template>
  <div class="channel-panel">
    <VChart class="channel-panel__chart" :option="panelOption" autoresize />
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { BarChart, LineChart } from 'echarts/charts';
  import type { BarSeriesOption, LineSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    MarkLineComponent,
    TitleComponent,
    TooltipComponent,
    type GridComponentOption,
    type TitleComponentOption,
    type TooltipComponentOption,
  } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
  import { CHART_SERIES_COLORS, useChartTheme, withAlpha } from '@/config/chart-theme';
  import type { ChannelCompositionKey, ChannelHealthMetricKey, ChannelResourceData } from '@/mock/data-acquisition';

  use([CanvasRenderer, BarChart, LineChart, GridComponent, TitleComponent, TooltipComponent, MarkLineComponent]);

  type ECOption = ComposeOption<
    | LineSeriesOption
    | BarSeriesOption
    | GridComponentOption
    | TitleComponentOption
    | TooltipComponentOption
  >;

  const props = defineProps<{ data: ChannelResourceData }>();
  const tokens = useChartTheme();
  const channelLabels: Record<ChannelCompositionKey, string> = {
    turbine: '风机通道',
    lidar: '激光雷达通道',
    control: '控制/管理通道',
    reserved: '预留通道',
  };

  const avgTraffic = computed(() => props.data.trafficTrend.reduce((sum, item) => sum + item.value, 0) / Math.max(props.data.trafficTrend.length, 1));
  const totalChannels = computed(() => props.data.channelComposition.reduce((sum, item) => sum + item.value, 0));
  const packetLossMetric = computed(() => props.data.healthMetrics.find((item) => item.key === 'packetLoss')?.value ?? 0);
  const jitterMetric = computed(() => props.data.healthMetrics.find((item) => item.key === 'jitter')?.value ?? 0);
  const delayMetric = computed(() => props.data.healthMetrics.find((item) => item.key === 'avgDelay')?.value ?? props.data.avgDelay);

  const healthRows = computed(() =>
    [
      {
        name: '带宽使用率',
        value: props.data.utilization,
        normalized: props.data.utilization,
        display: `${props.data.utilization}%`,
        tone: props.data.utilization > 80 ? tokens.value.warning : props.data.utilization >= 60 ? tokens.value.warning : tokens.value.success,
      },
      {
        name: '平均时延',
        value: delayMetric.value,
        normalized: Math.min(100, (delayMetric.value / 40) * 100),
        display: `${delayMetric.value}ms`,
        tone: delayMetric.value > 40 ? tokens.value.warning : delayMetric.value >= 25 ? tokens.value.warning : tokens.value.success,
      },
      {
        name: '抖动',
        value: jitterMetric.value,
        normalized: Math.min(100, (jitterMetric.value / 12) * 100),
        display: `${jitterMetric.value}ms`,
        tone: jitterMetric.value > 10 ? tokens.value.warning : jitterMetric.value >= 6 ? tokens.value.warning : tokens.value.success,
      },
      {
        name: '丢包率',
        value: packetLossMetric.value,
        normalized: Math.min(100, (packetLossMetric.value / 2) * 100),
        display: `${packetLossMetric.value}%`,
        tone: packetLossMetric.value > 1 ? tokens.value.warning : packetLossMetric.value >= 0.5 ? tokens.value.warning : tokens.value.success,
      },
    ],
  );

  const panelOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: [
      {
        text: '实时流量趋势',
        left: 'center',
        top: 4,
        textStyle: { ...tokens.value.titleTextStyle, color: tokens.value.focusTextLight, fontSize: 11 },
      },
      {
        text: '通道构成',
        left: '29%',
        top: '56%',
        textStyle: { ...tokens.value.titleTextStyle, color: tokens.value.focusTextLight, fontSize: 11 },
      },
      {
        text: '链路健康度',
        left: '76%',
        top: '56%',
        textStyle: { ...tokens.value.titleTextStyle, color: tokens.value.focusTextLight, fontSize: 11 },
      },
    ],
    grid: [
      { left: 34, right: 16, top: 28, height: '38%', containLabel: false },
      { left: 26, width: '39%', bottom: 12, height: '28%', containLabel: false },
      { right: 16, width: '39%', bottom: 12, height: '28%', containLabel: false },
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: tokens.value.tooltipBg,
      borderColor: tokens.value.tooltipBorder,
      textStyle: tokens.value.tooltipTextStyle,
      axisPointer: { type: 'shadow' },
    },
    xAxis: [
      {
        gridIndex: 0,
        type: 'category',
        data: props.data.trafficTrend.map((item) => item.time),
        axisLabel: { color: tokens.value.textMuted, fontSize: 10, interval: 1 },
        axisLine: { lineStyle: { color: tokens.value.textFaint } },
        axisTick: { show: false },
      },
      {
        gridIndex: 1,
        type: 'value',
        axisLabel: { color: tokens.value.textMuted, fontSize: 10 },
        splitLine: { lineStyle: { color: tokens.value.fillMuted } },
      },
      {
        gridIndex: 2,
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        gridIndex: 0,
        type: 'value',
        axisLabel: { color: tokens.value.textMuted, fontSize: 10, formatter: '{value}' },
        splitLine: { lineStyle: { color: tokens.value.fillMuted } },
      },
      {
        gridIndex: 1,
        type: 'category',
        data: props.data.channelComposition.map((item) => channelLabels[item.key]),
        axisLabel: { color: tokens.value.textMuted, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      {
        gridIndex: 2,
        type: 'category',
        data: healthRows.value.map((item) => item.name),
        axisLabel: { color: tokens.value.textMuted, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
    ],
    series: [
      {
        xAxisIndex: 0,
        yAxisIndex: 0,
        type: 'line',
        smooth: true,
        data: props.data.trafficTrend.map((item) => item.value),
        symbolSize: 6,
        lineStyle: { width: 2, color: tokens.value.primary },
        itemStyle: { color: tokens.value.primary },
        areaStyle: { color: withAlpha(tokens.value.primary, 0.14) },
        markLine: {
          symbol: 'none',
          silent: true,
          lineStyle: { color: withAlpha(tokens.value.warning, 0.45), type: 'dashed' },
          data: [
            {
              yAxis: Number(avgTraffic.value.toFixed(1)),
              name: '均值',
              label: {
                show: true,
                position: 'insideStartTop',
                color: withAlpha(tokens.value.warning, 0.85),
                fontSize: 10,
                formatter: '均值',
              },
            },
            {
              yAxis: props.data.peakBandwidth,
              name: '峰值带宽',
              label: {
                show: true,
                position: 'insideEndTop',
                color: tokens.value.textFaint,
                fontSize: 10,
                formatter: '峰值',
              },
            },
          ],
        },
        markPoint: {
          symbolSize: 28,
          label: { color: tokens.value.focusTextDark, fontSize: 10, formatter: 'P' },
          data: [{ type: 'max', name: '峰值' }],
        },
        tooltip: {
          valueFormatter: (value) => `${value} MB/s`,
        },
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'bar',
        barWidth: 12,
        showBackground: true,
        backgroundStyle: { color: tokens.value.markerFill },
        label: {
          show: true,
          position: 'insideRight',
          color: tokens.value.focusTextLight,
          fontSize: 10,
          formatter: (params: any) => `${params.value ?? 0}`,
        },
        data: props.data.channelComposition.map((item, index) => ({
          value: item.value,
          itemStyle: { color: CHART_SERIES_COLORS[index] ?? CHART_SERIES_COLORS[0] },
        })),
        tooltip: {
          formatter: (params: any) => {
            const item = props.data.channelComposition.find((entry) => channelLabels[entry.key] === params.name);
            if (!item) return '';
            const percent = ((item.value / Math.max(totalChannels.value, 1)) * 100).toFixed(1);
            return `${channelLabels[item.key]}<br/>数量：${item.value}<br/>占比：${percent}%`;
          },
        },
      },
      {
        xAxisIndex: 2,
        yAxisIndex: 2,
        type: 'bar',
        barWidth: 12,
        showBackground: true,
        backgroundStyle: { color: tokens.value.markerFill },
        label: {
          show: true,
          position: 'right',
          color: tokens.value.textMain,
          fontSize: 10,
          formatter: (params: any) => {
            const item = healthRows.value.find((entry) => entry.name === params.name);
            return item?.display ?? `${params.value ?? 0}`;
          },
        },
        data: healthRows.value.map((item) => ({
          value: item.normalized,
          itemStyle: { color: item.tone },
        })),
        tooltip: {
          formatter: (params: any) => {
            const item = healthRows.value.find((entry) => entry.name === params.name);
            if (!item) return '';
            return `${item.name}<br/>当前值：${item.display}`;
          },
        },
      },
    ],
  }));
</script>

<style scoped lang="less">
  .channel-panel {
    height: 100%;
    min-height: 0;
  }

  .channel-panel__chart {
    width: 100%;
    height: 100%;
    min-height: 0;
  }
</style>
