<template>
  <VChart class="chart" :option="chartOption" autoresize />
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { EChartsOption } from 'echarts';
  import { CanvasRenderer } from 'echarts/renderers';
  import { LineChart } from 'echarts/charts';
  import {
    GridComponent,
    TooltipComponent,
    AxisPointerComponent,
    MarkLineComponent,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { useChartTheme } from '@/config/chart-theme';
  import type { TransferFunctionData } from '@/types/lidar';

  use([
    CanvasRenderer,
    LineChart,
    GridComponent,
    TooltipComponent,
    AxisPointerComponent,
    MarkLineComponent,
  ]);

  const props = defineProps<{
    data: TransferFunctionData;
  }>();
  const chartTheme = useChartTheme();

  const chartOption = computed<EChartsOption>(() => {
    const points = props.data.points ?? [];
    if (!points.length) {
      return {};
    }

    const markerLines = props.data.markerFrequencies.map((value) => ({
      xAxis: value,
      label: {
        formatter: `${value}Hz`,
        color: chartTheme.value.textMuted,
      },
    }));

    return {
      color: [chartTheme.value.primary, chartTheme.value.warning],
      animationDuration: 300,
      grid: [
        {
          left: 52,
          right: 18,
          top: 20,
          height: '34%',
        },
        {
          left: 52,
          right: 18,
          bottom: 30,
          height: '34%',
        },
      ],
      tooltip: {
        trigger: 'axis',
        confine: true,
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: chartTheme.value.tooltipBg,
            color: chartTheme.value.tooltipTextStyle.color,
          },
        },
        backgroundColor: chartTheme.value.tooltipBg,
        borderColor: chartTheme.value.tooltipBorder,
        textStyle: chartTheme.value.tooltipTextStyle,
      },
      xAxis: [
        {
          type: 'log',
          logBase: 10,
          min: 0.01,
          max: 1,
          gridIndex: 0,
          axisLabel: { show: false },
          splitLine: {
            lineStyle: { color: chartTheme.value.splitLine },
          },
          axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
        },
        {
          type: 'log',
          logBase: 10,
          min: 0.01,
          max: 1,
          gridIndex: 1,
          name: 'Frequency (Hz)',
          nameLocation: 'middle',
          nameGap: 26,
          nameTextStyle: { color: chartTheme.value.textMuted },
          axisLabel: {
            color: chartTheme.value.textMuted,
            formatter(value: number) {
              return value.toFixed(2);
            },
          },
          splitLine: {
            lineStyle: { color: chartTheme.value.splitLine },
          },
          axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
        },
      ],
      yAxis: [
        {
          type: 'value',
          name: 'Gain',
          min: 0,
          max: 1.1,
          nameTextStyle: { color: chartTheme.value.textMuted },
          axisLabel: {
            color: chartTheme.value.textMuted,
            formatter(value: number) {
              return Number(value).toFixed(1);
            },
          },
          splitLine: {
            lineStyle: { color: chartTheme.value.splitLine },
          },
        },
        {
          type: 'value',
          name: 'Phase (deg)',
          min: -100,
          max: 5,
          gridIndex: 1,
          nameTextStyle: { color: chartTheme.value.textMuted },
          axisLabel: {
            color: chartTheme.value.textMuted,
            formatter(value: number) {
              return Number(value).toFixed(0);
            },
          },
          splitLine: {
            lineStyle: { color: chartTheme.value.splitLine },
          },
        },
      ],
      series: [
        {
          name: 'Gain',
          type: 'line',
          xAxisIndex: 0,
          yAxisIndex: 0,
          smooth: 0.18,
          showSymbol: false,
          data: points.map((item) => [item.frequency, item.gain]),
          lineStyle: {
            width: 2,
            color: chartTheme.value.primary,
          },
          areaStyle: {
            color: chartTheme.value.fillSoft,
          },
          markLine: {
            symbol: 'none',
            silent: true,
            lineStyle: {
              color: chartTheme.value.warning,
              type: 'dashed',
            },
            data: markerLines,
          },
        },
        {
          name: 'Phase',
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          smooth: 0.18,
          showSymbol: false,
          data: points.map((item) => [item.frequency, item.phase]),
          lineStyle: {
            width: 2,
            color: chartTheme.value.warning,
          },
          areaStyle: {
            color: chartTheme.value.fillSoft,
          },
          markLine: {
            symbol: 'none',
            silent: true,
            lineStyle: {
              color: chartTheme.value.warning,
              type: 'dashed',
            },
            data: markerLines,
          },
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .chart {
    width: 100%;
    height: 100%;
    min-height: 0;
  }
</style>
