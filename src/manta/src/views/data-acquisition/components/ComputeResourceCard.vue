<template>
  <div class="compute-panel">
    <div class="compute-panel__grid">
      <div class="compute-panel__cell compute-panel__cell--left">
        <VChart class="compute-panel__chart" :option="serviceLoadOption" autoresize />
      </div>
      <div class="compute-panel__cell compute-panel__cell--right">
        <div class="compute-panel__stack">
          <div class="compute-panel__cell">
            <VChart class="compute-panel__chart" :option="cpuUsageOption" autoresize />
          </div>
          <div class="compute-panel__cell">
            <VChart class="compute-panel__chart" :option="memoryUsageOption" autoresize />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { BarChart, LineChart } from 'echarts/charts';
  import type { BarSeriesOption, LineSeriesOption } from 'echarts/charts';
  import { GridComponent, TitleComponent, TooltipComponent, type GridComponentOption, type TitleComponentOption, type TooltipComponentOption } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
  import { useChartTheme, withAlpha } from '@/config/chart-theme';
  import type { ComputeResourceData, ComputeServiceKey } from '@/mock/data-acquisition';

  use([CanvasRenderer, BarChart, LineChart, GridComponent, TitleComponent, TooltipComponent]);

  type ECOption = ComposeOption<BarSeriesOption | LineSeriesOption | GridComponentOption | TitleComponentOption | TooltipComponentOption>;

  const props = defineProps<{ data: ComputeResourceData }>();
  const chartTheme = useChartTheme();
  const serviceLabels: Record<ComputeServiceKey, string> = {
    collector: '采集服务',
    cleaning: '清洗服务',
    quality: '质检服务',
    analysis: '分析服务',
    index: '索引服务',
    forwarder: '转发服务',
  };
  const cpuLineColor = computed(() => chartTheme.value.primary);
  const memoryLineColor = computed(() => chartTheme.value.success);

  const panelOption = computed<ECOption>(() => ({
    animation: false,
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'value', show: false },
    series: [],
  }));

  const serviceLoadOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '服务负载分布（实时）',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    grid: {
      left: 54,
      right: 18,
      top: 28,
      bottom: 20,
      containLabel: false,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, formatter: '{value}%' },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: props.data.services.map((item) => serviceLabels[item.key]),
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        name: 'CPU',
        type: 'bar',
        barWidth: 10,
        data: props.data.services.map((item) => ({
          value: item.cpu,
          itemStyle: { color: item.status === 'warning' ? chartTheme.value.warning : chartTheme.value.primary },
        })),
      },
      {
        name: '内存',
        type: 'bar',
        barWidth: 10,
        data: props.data.services.map((item) => ({
          value: item.memory,
          itemStyle: { color: item.status === 'warning' ? chartTheme.value.warning : chartTheme.value.success },
        })),
      },
    ],
  }));

  const cpuUsageOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: 'CPU 使用率（最近1分钟）',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    grid: {
      left: 38,
      right: 18,
      top: 28,
      bottom: 24,
      containLabel: false,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'category',
      data: props.data.usageTrend1m.map((item) => item.time),
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, interval: 1 },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, formatter: '{value}%' },
      splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbolSize: 5,
        color: cpuLineColor.value,
        data: props.data.usageTrend1m.map((item) => item.cpu),
        lineStyle: { width: 2, color: cpuLineColor.value },
        itemStyle: { color: cpuLineColor.value },
        areaStyle: { color: cpuLineColor.value, opacity: 0.18 },
        emphasis: {
          disabled: true,
          areaStyle: { color: cpuLineColor.value, opacity: 0.18 },
        },
      },
    ],
  }));

  const memoryUsageOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '内存使用率（最近1分钟）',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    grid: {
      left: 38,
      right: 18,
      top: 28,
      bottom: 24,
      containLabel: false,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'category',
      data: props.data.usageTrend1m.map((item) => item.time),
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, interval: 1 },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, formatter: '{value}%' },
      splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbolSize: 5,
        color: memoryLineColor.value,
        data: props.data.usageTrend1m.map((item) => item.memory),
        lineStyle: { width: 2, color: memoryLineColor.value },
        itemStyle: { color: memoryLineColor.value },
        areaStyle: { color: memoryLineColor.value, opacity: 0.18 },
        emphasis: {
          disabled: true,
          areaStyle: { color: memoryLineColor.value, opacity: 0.18 },
        },
      },
    ],
  }));
</script>

<style scoped lang="less">
  .compute-panel {
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .compute-panel__grid {
    display: flex;
    gap: 8px;
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .compute-panel__stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .compute-panel__cell {
    min-width: 0;
    min-height: 0;
    width: 100%;
    height: 100%;
  }

  .compute-panel__cell--left {
    flex: 1 1 50%;
  }

  .compute-panel__cell--right {
    flex: 1 1 50%;
  }

  .compute-panel__chart {
    width: 100%;
    height: 100%;
    min-height: 0;
  }
</style>
