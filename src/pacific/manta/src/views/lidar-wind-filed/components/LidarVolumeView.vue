<template>
  <div class="chart-wrap">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script lang="ts" setup>
  import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
  import * as echarts from 'echarts';
  import 'echarts-gl';
  import { useChartTheme } from '@/config/chart-theme';
  import type { LidarForwardComposite3DResponse } from '@/types/lidar';

  const props = defineProps<{
    data: LidarForwardComposite3DResponse;
  }>();

  const chartRef = ref<HTMLDivElement | null>(null);
  const chartTheme = useChartTheme();
  let chart: echarts.ECharts | null = null;
  let resizeObserver: ResizeObserver | null = null;

  function getOutlineColor() {
    return chartTheme.value.textStrong;
  }

  function buildOption() {
    const rawPoints = props.data.rawPoints ?? [];
    const distances = props.data.distances ?? [];
    const textColor = chartTheme.value.textStrong;
    const subTextColor = chartTheme.value.textFaint;
    const distanceScale = 0.56;
    const speedValues = rawPoints.map((point) => point.windSpeed);
    const rawMinSpeed = speedValues.length ? Math.min(...speedValues) : 6;
    const rawMaxSpeed = speedValues.length ? Math.max(...speedValues) : 12;
    const visualMin = Math.floor(rawMinSpeed * 10) / 10;
    const visualMax = Math.ceil(rawMaxSpeed * 10) / 10;
    const safeVisualMax = visualMax <= visualMin ? visualMin + 0.5 : visualMax;
    const invalidCount = rawPoints.filter((point) => !point.isValid).length;
    const validRate = rawPoints.length ? ((rawPoints.length - invalidCount) / rawPoints.length) * 100 : 0;
    const initialCenter = [1.3, -18.2, 2.2] as [number, number, number];
    const planeExtent =
      Math.max(18, ...rawPoints.map((point) => Math.max(Math.abs(point.x), Math.abs(point.y)))) + 6;
    const maxDistance = Math.max(180, ...distances);
    const plottedMaxDistance = maxDistance * distanceScale;
    const viewControl = {
      projection: 'perspective',
      alpha: 23.6,
      beta: 0.7,
      distance: 135.4,
      minDistance: 118,
      maxDistance: 440,
      center: initialCenter,
      rotateSensitivity: 1,
      zoomSensitivity: 0.8,
      panSensitivity: 0.5,
      autoRotate: false,
    };

    const rawData = rawPoints.map((point) => ({
      value: [point.z * distanceScale, point.x, point.y, point.windSpeed, point.beamIndex, point.distance, point.quality, point.isValid ? 1 : 0],
      itemStyle: point.isValid
        ? {
            opacity: 0.74,
          }
        : {
            color: chartTheme.value.danger,
            opacity: 0.96,
          },
    }));

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        confine: true,
        backgroundColor: chartTheme.value.tooltipBg,
        borderColor: chartTheme.value.tooltipBorder,
        textStyle: chartTheme.value.tooltipTextStyle,
        formatter(params: any) {
          const v = params.value;
          if (params.seriesName === '原始测点') {
            return [
              '类型：原始测点',
              `波束：B${v[4] + 1}`,
              `距离：${v[5]} m`,
              `风速：${Number(v[3]).toFixed(2)} m/s`,
              `状态：${v[7] ? '有效' : '无效'}`,
              `质量：${Number(v[6]).toFixed(2)}`,
            ].join('<br/>');
          }
          return '';
        },
      },
      visualMap: {
        min: visualMin,
        max: safeVisualMax,
        dimension: 3,
        seriesIndex: [0],
        orient: 'vertical',
        right: 2,
        top: 'middle',
        itemHeight: 82,
        itemWidth: 6,
        text: [safeVisualMax.toFixed(1), visualMin.toFixed(1)],
        textGap: 8,
        textStyle: { color: subTextColor, fontSize: 10 },
        calculable: false,
        inRange: {
          color: chartTheme.value.visualMapColors,
        },
      },
      grid3D: {
        left: 0,
        right: 24,
        top: 30,
        bottom: 0,
        boxWidth: plottedMaxDistance + 12,
        boxDepth: planeExtent * 3.1,
        boxHeight: planeExtent * 3.1,
        environment: 'none',
        boxStyle: {
          color: 'transparent',
          opacity: 0,
          borderWidth: 0,
        },
        axisPointer: { show: false },
        viewControl,
        light: {
          main: { intensity: 1, shadow: false },
          ambient: { intensity: 0.7 },
        },
      },
      xAxis3D: {
        type: 'value',
        min: 0,
        max: plottedMaxDistance + 6,
        name: '',
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 9,
          padding: [4, 0, 0, 0],
          verticalAlign: 'middle',
          formatter: (v: number) => (v <= 0 ? '' : `${Math.round(v / distanceScale)}m`),
        },
        axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: chartTheme.value.splitLine, type: 'dashed' } },
      },
      yAxis3D: {
        type: 'value',
        min: -planeExtent,
        max: planeExtent,
        name: '',
        axisLabel: { color: chartTheme.value.textFaint, fontSize: 9 },
        axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
      },
      zAxis3D: {
        type: 'value',
        min: -planeExtent,
        max: planeExtent,
        name: '',
        axisLabel: { color: chartTheme.value.textFaint, fontSize: 9 },
        axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
      },
      graphic: [
        {
          type: 'group',
          right: 16,
          top: 8,
          silent: true,
          children: [
            {
              type: 'text',
              x: 0,
              y: 0,
              style: {
                text: `采样点数：${rawPoints.length}`,
                fill: subTextColor,
                fontSize: 11,
                fontWeight: 400,
              },
            },
            {
              type: 'text',
              x: 0,
              y: 18,
              style: {
                text: `无效数量：${invalidCount}`,
                fill: subTextColor,
                fontSize: 11,
                fontWeight: 400,
              },
            },
            {
              type: 'text',
              x: 0,
              y: 36,
              style: {
                text: `有效率：${validRate.toFixed(1)}%`,
                fill: subTextColor,
                fontSize: 11,
                fontWeight: 400,
              },
            },
          ],
        },
      ],
      series: [
        {
          name: '原始测点',
          type: 'scatter3D',
          coordinateSystem: 'cartesian3D',
          symbol: 'circle',
          symbolSize: 12,
          data: rawData,
          itemStyle: {
            opacity: 0.74,
          },
        },
      ],
    };
  }

  async function renderChart() {
    await nextTick();
    if (!chartRef.value) return;
    if (!chart) {
      chart = echarts.init(chartRef.value);
    }
    chart.setOption(buildOption(), true);
    chart.resize();
  }

  onMounted(async () => {
    await renderChart();
    if (chartRef.value) {
      resizeObserver = new ResizeObserver(() => {
        chart?.resize();
      });
      resizeObserver.observe(chartRef.value);
    }
  });

  onBeforeUnmount(() => {
    resizeObserver?.disconnect();
    resizeObserver = null;
    chart?.dispose();
    chart = null;
  });

  watch(
    () => props.data,
    async () => {
      await renderChart();
    },
    { deep: true },
  );

  watch(
    () => chartTheme.value,
    async () => {
      await renderChart();
    },
    { deep: true },
  );
</script>

<style scoped lang="less">
  .chart-wrap {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 240px;
    padding-top: 14px;
    box-sizing: border-box;
  }

  .chart {
    position: absolute;
    inset: 14px 0 0 0;
    width: 100%;
    height: calc(100% - 14px);
    min-height: 240px;
  }
</style>
