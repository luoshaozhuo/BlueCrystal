<template>
  <VChart class="chart" :option="chartOption" autoresize />
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { EChartsOption } from 'echarts';
  import { CanvasRenderer } from 'echarts/renderers';
  import { LineChart } from 'echarts/charts';
  import { GridComponent, TooltipComponent, AxisPointerComponent, TitleComponent } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { useChartTheme } from '@/config/chart-theme';
  import type { LidarInflowProfilePanelData } from '@/types/lidar';

  use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, AxisPointerComponent, TitleComponent]);

  const props = defineProps<{
    data: LidarInflowProfilePanelData;
  }>();
  const chartTheme = useChartTheme();

  function createAxisRange(values: number[], segments = 3) {
    const min = Math.min(...values);
    const max = Math.max(...values);

    if (min === max) {
      const padding = Math.abs(min || 1) * 0.1;
      return {
        min: min - padding,
        max: max + padding,
        interval: (padding * 2) / segments,
      };
    }

    const span = max - min;
    const padding = span * 0.1;
    const axisMin = min - padding;
    const axisMax = max + padding;

    return {
      min: axisMin,
      max: axisMax,
      interval: (axisMax - axisMin) / segments,
    };
  }

  function formatToPrecision(value: number, precision = 3) {
    return Number(value.toPrecision(precision)).toString();
  }

  const chartOption = computed((): EChartsOption => {
    const distances = props.data?.distances ?? [];
    const profiles = props.data?.profiles ?? [];

    if (!distances.length || !profiles.length) {
      return {};
    }

    const metrics = [
      { title: '风速(m/s)', key: 'windSpeed' as const, gridIndex: 0, color: chartTheme.value.primary },
      { title: '风向(°)', key: 'windDirection' as const, gridIndex: 1, color: chartTheme.value.info },
      { title: '横向风切变', key: 'horizontalShear' as const, gridIndex: 2, color: chartTheme.value.warning },
      { title: '纵向风切变', key: 'verticalShear' as const, gridIndex: 3, color: chartTheme.value.success },
    ];
    const yAxisRanges = metrics.map((item) => createAxisRange(profiles.map((profile) => profile[item.key])));

    return {
      grid: [
        { left: '12%', top: '10%', width: '33%', height: '30%', containLabel: false },
        { left: '60%', top: '10%', width: '33%', height: '30%', containLabel: false },
        { left: '12%', top: '56%', width: '33%', height: '30%', containLabel: false },
        { left: '60%', top: '56%', width: '33%', height: '30%', containLabel: false },
      ],
      axisPointer: {
        link: [{ xAxisIndex: [0, 1, 2, 3] }],
      },
      tooltip: {
        trigger: 'axis',
        confine: true,
        backgroundColor: chartTheme.value.tooltipBg,
        borderColor: chartTheme.value.tooltipBorder,
        textStyle: chartTheme.value.tooltipTextStyle,
        axisPointer: {
          type: 'line',
          label: {
            backgroundColor: chartTheme.value.tooltipBg,
            color: chartTheme.value.tooltipTextStyle.color,
          },
        },
        formatter(params: any) {
          const list = Array.isArray(params) ? params : [params];
          const distance = Number(list[0]?.axisValue);
          const profile = profiles.find((item) => item.distance === distance);

          if (!profile) {
            return '';
          }

          return [
            `探测距离：${profile.distance} m`,
            `风速：${profile.windSpeed.toFixed(2)} m/s`,
            `风向：${profile.windDirection.toFixed(1)}°`,
            `横向风切变：${profile.horizontalShear.toFixed(3)}`,
            `纵向风切变：${profile.verticalShear.toFixed(3)}`,
          ].join('<br/>');
        },
      },
      xAxis: metrics.map((item) => ({
        type: 'category',
        gridIndex: item.gridIndex,
        data: distances,
        boundaryGap: false,
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 11,
          interval: 0,
        },
        nameTextStyle: {
          color: chartTheme.value.textMuted,
          fontSize: 11,
        },
        axisLine: {
          lineStyle: {
            color: chartTheme.value.axisLine,
          },
        },
        axisTick: {
          show: false,
        },
        axisPointer: {
          show: true,
          snap: true,
        },
        name: item.gridIndex > 1 ? '探测距离(m)' : '',
        nameLocation: 'middle',
        nameGap: 28,
      })),
      yAxis: metrics.map((item) => ({
        type: 'value',
        gridIndex: item.gridIndex,
        scale: true,
        name: item.title,
        nameLocation: 'middle',
        nameGap: 52,
        min: yAxisRanges[item.gridIndex].min,
        max: yAxisRanges[item.gridIndex].max,
        interval: yAxisRanges[item.gridIndex].interval,
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 11,
          width: 44,
          align: 'right',
          formatter(value: number) {
            return formatToPrecision(value, 3);
          },
        },
        nameTextStyle: {
          color: chartTheme.value.textMuted,
          fontSize: 11,
          fontWeight: 400,
        },
        axisLine: {
          show: false,
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: chartTheme.value.splitLine,
          },
        },
      })),
      series: metrics.map((item) => ({
        name: item.title,
        type: 'line',
        xAxisIndex: item.gridIndex,
        yAxisIndex: item.gridIndex,
        data: profiles.map((profile) => profile[item.key]),
        symbol: 'circle',
        showSymbol: true,
        connectNulls: true,
        lineStyle: {
          width: 2,
          color: item.color,
        },
        itemStyle: {
          color: item.color,
        },
      })),
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
