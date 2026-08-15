<template>
  <div class="consistency-chart">
    <VChart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { EChartsOption } from 'echarts';
  import { CanvasRenderer } from 'echarts/renderers';
  import { LineChart, ScatterChart } from 'echarts/charts';
  import {
    GraphicComponent,
    GridComponent,
    TooltipComponent,
    AxisPointerComponent,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { useChartTheme } from '@/config/chart-theme';
  import type { ConsistencyAlignmentData } from '@/types/lidar';

  use([
    CanvasRenderer,
    LineChart,
    ScatterChart,
    GraphicComponent,
    GridComponent,
    TooltipComponent,
    AxisPointerComponent,
  ]);

  const props = defineProps<{
    data: ConsistencyAlignmentData;
  }>();
  const chartTheme = useChartTheme();

  const chartOption = computed<EChartsOption>(() => {
    const points = props.data.points ?? [];
    if (!points.length) {
      return {};
    }

    const values = points.flatMap((item) => [item.lidarWindSpeed, item.nacelleWindSpeed]);
    const min = Math.floor(Math.min(...values) - 0.5);
    const max = Math.ceil(Math.max(...values) + 0.5);
    const { slope, intercept } = props.data.regression;
    const regressionLine = [
      [min, slope * min + intercept],
      [max, slope * max + intercept],
    ];

    return {
      animationDuration: 320,
      title: [
        {
          text: `Corr ${props.data.stats.corr.toFixed(3)}   Bias ${props.data.stats.bias.toFixed(3)} m/s   RMSE ${props.data.stats.rmse.toFixed(3)} m/s`,
          right: 12,
          textStyle: {
            color: chartTheme.value.textMuted,
            fontSize: 11,
            fontWeight: 400,
          },
        },
      ],
      grid: {
        left: 44,
        right: 20,
        top: 36,
        bottom: 30,
        containLabel: false,
      },
      tooltip: {
        trigger: 'item',
        confine: true,
        backgroundColor: chartTheme.value.tooltipBg,
        borderColor: chartTheme.value.tooltipBorder,
        textStyle: chartTheme.value.tooltipTextStyle,
        formatter(params: any) {
          return [
            `Lidar: ${Number(params.value[0]).toFixed(2)} m/s`,
            `Nacelle: ${Number(params.value[1]).toFixed(2)} m/s`,
          ].join('<br/>');
        },
      },
      xAxis: {
        type: 'value',
        min,
        max,
        name: '雷达风速 (m/s)',
        nameLocation: 'middle',
        nameGap: 28,
        nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 10,
          formatter(value: number) {
            return Number(value).toFixed(1);
          },
        },
        axisLine: {
          lineStyle: { color: chartTheme.value.axisLine },
        },
        splitLine: {
          lineStyle: { color: chartTheme.value.splitLine },
        },
      },
      yAxis: {
        type: 'value',
        min,
        max,
        name: '机舱风速 (m/s)',
        nameLocation: 'middle',
        nameGap: 34,
        nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 10,
          formatter(value: number) {
            return Number(value).toFixed(1);
          },
        },
        axisLine: {
          lineStyle: { color: chartTheme.value.axisLine },
        },
        splitLine: {
          lineStyle: { color: chartTheme.value.splitLine },
        },
      },
      series: [
        {
          name: 'Samples',
          type: 'scatter',
          data: points.map((item) => [item.lidarWindSpeed, item.nacelleWindSpeed]),
          symbolSize: 7,
          itemStyle: {
            color: chartTheme.value.info,
          },
        },
        {
          name: 'y=x',
          type: 'line',
          data: [
            [min, min],
            [max, max],
          ],
          showSymbol: false,
          lineStyle: {
            width: 1.4,
            type: 'dashed',
            color: chartTheme.value.textFaint,
          },
        },
        {
          name: 'Regression',
          type: 'line',
          data: regressionLine,
          showSymbol: false,
          lineStyle: {
            width: 2,
            color: chartTheme.value.warning,
          },
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .consistency-chart {
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .chart {
    width: 100%;
    height: 100%;
    min-height: 0;
    box-sizing: border-box;
  }
</style>
