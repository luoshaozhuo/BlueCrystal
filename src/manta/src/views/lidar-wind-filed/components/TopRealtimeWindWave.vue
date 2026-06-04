<template>
  <div class="top-wave">
    <div class="chart-wrap">
      <VChart class="chart" :option="chartOption" autoresize />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { EChartsOption } from 'echarts';
  import { CanvasRenderer } from 'echarts/renderers';
  import { LineChart } from 'echarts/charts';
  import { GridComponent, TooltipComponent, AxisPointerComponent, MarkPointComponent } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { useChartTheme } from '@/config/chart-theme';
  import type { RealtimeWindWaveResponse } from '@/types/lidar';

  use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, AxisPointerComponent, MarkPointComponent]);

  const props = defineProps<{
    data: RealtimeWindWaveResponse;
  }>();
  const chartTheme = useChartTheme();

  const chartOption = computed<EChartsOption>(() => {
    const points = props.data.points ?? [];
    if (!points.length) return {};

    const minAxis = Math.floor((props.data.min60s - 0.15) * 10) / 10;
    const maxAxis = Math.ceil((props.data.max60s + 0.15) * 10) / 10;
    const last = points[points.length - 1];

    return {
      animationDuration: 180,
      grid: {
        left: 24,
        right: 10,
        top: 8,
        bottom: 18,
        containLabel: true,
      },
      tooltip: {
        trigger: 'axis',
        confine: true,
        axisPointer: {
          type: 'line',
          lineStyle: { color: chartTheme.value.info },
        },
        backgroundColor: chartTheme.value.tooltipBg,
        borderColor: chartTheme.value.tooltipBorder,
        textStyle: chartTheme.value.tooltipTextStyle,
        formatter(params: any) {
          const item = points[params[0]?.dataIndex ?? 0];
          return [
            `时间: ${item.ts}`,
            `风速: ${item.windSpeed.toFixed(2)} m/s`,
            `60s均值: ${props.data.mean60s.toFixed(2)} m/s`,
            `最小/最大: ${props.data.min60s.toFixed(2)} / ${props.data.max60s.toFixed(2)} m/s`,
          ].join('<br/>');
        },
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: points.map((item) => item.ts),
        axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
        axisTick: { show: false },
        axisLabel: {
          color: chartTheme.value.textMuted,
          margin: 6,
          formatter(value: string, index: number) {
            return index % 10 === 0 || index === points.length - 1 ? value.slice(3) : '';
          },
        },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: minAxis,
        max: maxAxis,
        splitNumber: 1,
        axisLabel: {
          color: chartTheme.value.textMuted,
          margin: 6,
          formatter(value: number) {
            return value.toFixed(1);
          },
        },
        nameGap: 18,
        splitLine: { show: false },
      },
      series: [
        {
          type: 'line',
          data: points.map((item) => item.windSpeed),
          smooth: 0.3,
          showSymbol: false,
          lineStyle: { width: 2, color: chartTheme.value.primary },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: chartTheme.value.info },
                { offset: 1, color: chartTheme.value.fillSoft },
              ],
            },
          },
          markPoint: {
            symbol: 'circle',
            symbolSize: 6,
            itemStyle: {
              color: chartTheme.value.primary,
              borderColor: chartTheme.value.bgPanel,
              borderWidth: 1.2,
            },
            data: [{ name: 'Latest', coord: [last.ts, last.windSpeed] }],
          },
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .top-wave {
    width: 100%;
    height: 100%;
    min-height: 0;
    display: flex;
  }

  .chart-wrap {
    flex: 1 1 auto;
    width: 100%;
    height: 100%;
    min-height: 0;
    display: flex;
  }

  .chart {
    width: 100%;
    height: 100% !important;
    min-height: 0;
    flex: 1 1 auto;
  }
</style>
