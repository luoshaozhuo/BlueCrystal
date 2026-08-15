<template>
  <div class="evidence-chart">
    <VChart class="evidence-chart__body" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { CustomChart, ScatterChart } from 'echarts/charts';
  import type { CustomSeriesOption, ScatterSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    TitleComponent,
    TooltipComponent,
    type GridComponentOption,
    type TitleComponentOption,
    type TooltipComponentOption,
  } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS, useThemeTokens, withAlpha } from '@/config/chart-theme';
  import type { BootstrapMetricEvidence } from '@/types/power-analysis';

  use([CanvasRenderer, ScatterChart, CustomChart, GridComponent, TitleComponent, TooltipComponent]);

  type ECOption = ComposeOption<
    | CustomSeriesOption
    | ScatterSeriesOption
    | GridComponentOption
    | TitleComponentOption
    | TooltipComponentOption
  >;

  const props = defineProps<{ data: { metrics: BootstrapMetricEvidence[] } }>();
  const themeTokens = useThemeTokens();
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;
  const GROUP_CENTERS = { Peak: 0, P95: 1, P99: 2 } as const;
  const JITTER_WIDTH = 0.16;

  function round(value: number, digits = 3) {
    return Number(value.toFixed(digits));
  }

  function ceilToStep(value: number, step: number) {
    return Math.ceil(value / step) * step;
  }

  function getGroupCenter(metric: keyof typeof GROUP_CENTERS) {
    return GROUP_CENTERS[metric];
  }

  function createScatterData() {
    return props.data.metrics.flatMap((metric) =>
      metric.samples.map((value, sampleIndex) => ({
        value: [
          getGroupCenter(metric.metric) + ((((sampleIndex * 17) % 97) / 96) - 0.5) * JITTER_WIDTH,
          value,
        ],
        metric: metric.metric,
        mean: metric.mean,
        median: metric.median,
        ci95: metric.ci95,
      })),
    );
  }

  const option = computed<ECOption>(() => {
    const allValues = props.data.metrics.flatMap((metric) => metric.samples);
    const maxValue = Math.max(...allValues, 0);
    const axisMax = Math.max(3, ceilToStep(maxValue, 3));

    return {
      animationDuration: 260,
      title: {
        text: '稳健性',
        left: 'center',
        top: 0,
        textStyle: {
          color: themeTokens.text3,
          fontSize: 10,
          fontWeight: 400,
        },
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          return [
            `指标: ${params.data?.metric ?? '-'}`,
            `改善率: ${Number(params.data?.value?.[1] ?? 0).toFixed(2)}%`,
            `均值: ${Number(params.data?.mean ?? 0).toFixed(2)}%`,
            `Median: ${Number(params.data?.median ?? 0).toFixed(2)}%`,
            `95% CI: ${Number(params.data?.ci95?.[0] ?? 0).toFixed(2)}% ~ ${Number(params.data?.ci95?.[1] ?? 0).toFixed(2)}%`,
          ].join('<br/>');
        },
      },
      grid: { left: 52, right: 16, top: 18, bottom: 34, containLabel: true },
      xAxis: {
        type: 'value',
        min: -0.5,
        max: 2.5,
        interval: 0.5,
        axisLabel: {
          color: themeTokens.text2,
          fontSize: 11,
          margin: 10,
          formatter(value: number) {
            if (Math.abs(value - 0) < 1e-6) return 'Peak';
            if (Math.abs(value - 1) < 1e-6) return 'P95';
            if (Math.abs(value - 2) < 1e-6) return 'P99';
            return '';
          },
        },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: axisMax,
        interval: 3,
        name: '改善率 (%)',
        nameLocation: 'middle',
        nameGap: 42,
        nameRotate: 90,
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
          align: 'center',
          verticalAlign: 'middle',
        },
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
      },
      series: [
        {
          type: 'scatter',
          z: 2,
          clip: true,
          symbolSize: 6,
          itemStyle: { color: withAlpha(ANALYSIS_OPTIMIZED_COLOR, 0.4) },
          data: createScatterData(),
        },
        {
          type: 'custom',
          z: 3,
          silent: true,
          clip: true,
          renderItem(params: any, api: any) {
            const x = api.value(0);
            const low = api.value(1);
            const high = api.value(2);
            const center = api.value(3);
            const top = api.coord([x, high]);
            const bottom = api.coord([x, low]);
            const middle = api.coord([x, center]);
            const cap = 8;

            return {
              type: 'group',
              children: [
                {
                  type: 'line',
                  shape: { x1: top[0], y1: top[1], x2: bottom[0], y2: bottom[1] },
                  style: { stroke: ANALYSIS_OPTIMIZED_COLOR, lineWidth: 2 },
                },
                {
                  type: 'line',
                  shape: { x1: top[0] - cap / 2, y1: top[1], x2: top[0] + cap / 2, y2: top[1] },
                  style: { stroke: ANALYSIS_OPTIMIZED_COLOR, lineWidth: 2 },
                },
                {
                  type: 'line',
                  shape: { x1: bottom[0] - cap / 2, y1: bottom[1], x2: bottom[0] + cap / 2, y2: bottom[1] },
                  style: { stroke: ANALYSIS_OPTIMIZED_COLOR, lineWidth: 2 },
                },
                {
                  type: 'circle',
                  shape: { cx: middle[0], cy: middle[1], r: 4 },
                  style: { fill: ANALYSIS_OPTIMIZED_COLOR, stroke: themeTokens.focusTextLight, lineWidth: 1.5 },
                },
              ],
            };
          },
          data: props.data.metrics.map((metric) => [getGroupCenter(metric.metric), metric.ci95[0], metric.ci95[1], metric.mean]),
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
