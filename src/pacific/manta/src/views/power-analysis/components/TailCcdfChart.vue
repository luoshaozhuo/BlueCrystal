<template>
  <div class="evidence-chart">
    <VChart class="evidence-chart__body" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { CustomChart, LineChart, ScatterChart } from 'echarts/charts';
  import type { CustomSeriesOption, LineSeriesOption, ScatterSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    LegendComponent,
    TitleComponent,
    TooltipComponent,
    type GridComponentOption,
    type LegendComponentOption,
    type TitleComponentOption,
    type TooltipComponentOption,
  } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS, useThemeTokens } from '@/config/chart-theme';
  import type { TailCcdfEvidence } from '@/types/power-analysis';

  use([CanvasRenderer, LineChart, ScatterChart, CustomChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent]);

  type ECOption = ComposeOption<
    | CustomSeriesOption
    | LineSeriesOption
    | ScatterSeriesOption
    | GridComponentOption
    | LegendComponentOption
    | TitleComponentOption
    | TooltipComponentOption
  >;

  const props = defineProps<{ data: TailCcdfEvidence }>();
  const themeTokens = useThemeTokens();
  const baselineColor = CHART_COMPARISON_COLORS.baseline;
  const optimizedColor = CHART_COMPARISON_COLORS.optimized;
  const markerLabels = {
    baselineP95: '基准 P95',
    baselineP99: '基准 P99',
    optimizedP95: '优化后 P95',
    optimizedP99: '优化后 P99',
  } as const;

  function round(value: number, digits = 3) {
    return Number(value.toFixed(digits));
  }

  function createRugSeries(name: string, samples: number[], yBase: number, color: string): CustomSeriesOption {
    return {
      name,
      type: 'custom',
      silent: true,
      z: 1,
      renderItem(params: any, api: any) {
        const x = api.value(0);
        const y = api.value(1);
        const start = api.coord([x, y]);
        const end = api.coord([x, y + 0.035]);

        return {
          type: 'line',
          shape: {
            x1: start[0],
            y1: start[1],
            x2: end[0],
            y2: end[1],
          },
          style: {
            stroke: color,
            lineWidth: 1,
            opacity: 0.5,
          },
        };
      },
      data: samples.map((value) => [value, yBase]),
    };
  }

  const option = computed<ECOption>(() => {
    const minThreshold = Math.min(...props.data.thresholds);
    const maxThreshold = Math.max(...props.data.thresholds);

    return {
      animationDuration: 260,
      title: {
        text: '局部概率',
        left: 'center',
        top: 0,
        textStyle: {
          color: themeTokens.text3,
          fontSize: 10,
          fontWeight: 400,
        },
      },
      legend: {
        top: 0,
        right: 0,
        itemWidth: 8,
        itemHeight: 8,
        textStyle: { color: themeTokens.text3, fontSize: 10 },
        data: [
          {
            name: '基准',
            itemStyle: { color: baselineColor },
          },
          {
            name: '优化后',
            itemStyle: { color: optimizedColor },
          },
        ],
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          const items: any[] = Array.isArray(params) ? params : [params];
          const baselineItem = items.find((item) => item.seriesName === '基准');
          const optimizedItem = items.find((item) => item.seriesName === '优化后');
          const threshold = Number(baselineItem?.axisValue ?? optimizedItem?.axisValue ?? 0);
          return [
            `阈值: ${threshold.toFixed(3)}`,
            `基准 P(X>x): ${(Number(baselineItem?.value?.[1] ?? baselineItem?.value ?? 0) * 100).toFixed(1)}%`,
            `优化后 P(X>x): ${(Number(optimizedItem?.value?.[1] ?? optimizedItem?.value ?? 0) * 100).toFixed(1)}%`,
          ].join('<br/>');
        },
      },
      grid: { left: 42, right: 10, top: 22, bottom: 26, containLabel: true },
      xAxis: {
        type: 'value',
        min: round(minThreshold - 0.04, 2),
        max: round(maxThreshold + 0.04, 2),
        name: '风险阈值',
        nameLocation: 'middle',
        nameGap: 24,
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 1,
        name: '超越概率 P(X > x)',
        nameLocation: 'middle',
        nameGap: 42,
        nameRotate: 90,
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
          align: 'center',
          verticalAlign: 'middle',
        },
        axisLabel: {
          color: themeTokens.text3,
          fontSize: 10,
          formatter(value: number) {
            return `${Math.round(value * 100)}%`;
          },
        },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
      },
      series: [
        {
          name: '基准',
          type: 'line',
          smooth: 0.18,
          symbol: 'none',
          z: 3,
          clip: true,
          lineStyle: { width: 2, color: baselineColor },
          data: props.data.thresholds.map((threshold, index) => [threshold, props.data.baselineCcdf[index]]),
        },
        {
          name: '优化后',
          type: 'line',
          smooth: 0.18,
          symbol: 'none',
          z: 3,
          clip: true,
          lineStyle: { width: 2.2, color: optimizedColor },
          data: props.data.thresholds.map((threshold, index) => [threshold, props.data.optimizedCcdf[index]]),
        },
        createRugSeries('基准样本', props.data.baselineSamples, 0.02, baselineColor),
        createRugSeries('优化后样本', props.data.optimizedSamples, 0.07, optimizedColor),
        {
          name: '分位标记',
          type: 'scatter',
          z: 4,
          clip: true,
          symbolSize: 8,
          itemStyle: { color: baselineColor },
          tooltip: {
            formatter(params: any) {
              return [
                `${params.data.markerLabel}`,
                `阈值: ${Number(params.data.value[0]).toFixed(3)}`,
                `P(X>x): ${(Number(params.data.value[1]) * 100).toFixed(1)}%`,
              ].join('<br/>');
            },
          },
          label: {
            show: true,
            position: 'top',
            distance: 6,
            color: baselineColor,
            fontSize: 10,
            formatter(params: any) {
              return params.data.markerLabel;
            },
          },
          data: [
            { value: [props.data.markers.baseline.p95.x, props.data.markers.baseline.p95.y], markerLabel: markerLabels[props.data.markers.baseline.p95.labelKey] },
            { value: [props.data.markers.baseline.p99.x, props.data.markers.baseline.p99.y], markerLabel: markerLabels[props.data.markers.baseline.p99.labelKey] },
          ],
        },
        {
          name: '优化分位标记',
          type: 'scatter',
          z: 4,
          clip: true,
          symbolSize: 8,
          itemStyle: { color: optimizedColor },
          tooltip: {
            formatter(params: any) {
              return [
                `${params.data.markerLabel}`,
                `阈值: ${Number(params.data.value[0]).toFixed(3)}`,
                `P(X>x): ${(Number(params.data.value[1]) * 100).toFixed(1)}%`,
              ].join('<br/>');
            },
          },
          label: {
            show: true,
            position: 'top',
            distance: 6,
            color: optimizedColor,
            fontSize: 10,
            formatter(params: any) {
              return params.data.markerLabel;
            },
          },
          data: [
            { value: [props.data.markers.optimized.p95.x, props.data.markers.optimized.p95.y], markerLabel: markerLabels[props.data.markers.optimized.p95.labelKey] },
            { value: [props.data.markers.optimized.p99.x, props.data.markers.optimized.p99.y], markerLabel: markerLabels[props.data.markers.optimized.p99.labelKey] },
          ],
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .evidence-chart {
    position: relative;
    flex: 1;
    min-height: 0;
  }

  .evidence-chart__body {
    width: 100%;
    height: 100%;
    min-height: 0;
  }
</style>
