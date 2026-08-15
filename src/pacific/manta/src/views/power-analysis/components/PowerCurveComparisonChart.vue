<template>
  <VChart class="power-curve-card__chart" :option="mainChartOption" autoresize />
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { BarChart, CustomChart, LineChart } from 'echarts/charts';
  import type {
    BarSeriesOption,
    CustomSeriesOption,
    LineSeriesOption,
  } from 'echarts/charts';
  import { CanvasRenderer } from 'echarts/renderers';
  import {
    GridComponent,
    LegendComponent,
    TooltipComponent,
    type GridComponentOption,
    type LegendComponentOption,
    type TooltipComponentOption,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS, useThemeTokens, withAlpha } from '@/config/chart-theme';
  import type { PowerCurvePoint, RayleighParameters } from '@/types/power-analysis';

  use([
    CanvasRenderer,
    LineChart,
    BarChart,
    CustomChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
  ]);

  type ECOption = ComposeOption<
    | LineSeriesOption
    | BarSeriesOption
    | CustomSeriesOption
    | GridComponentOption
    | TooltipComponentOption
    | LegendComponentOption
  >;

  const props = defineProps<{
    data: PowerCurvePoint[];
    rayleighParameters: RayleighParameters;
  }>();

  const themeTokens = useThemeTokens();
  const ANALYSIS_BASELINE_COLOR = CHART_COMPARISON_COLORS.baseline;
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;
  const ANALYSIS_ACCENT_COLOR = CHART_COMPARISON_COLORS.accent;
  const deltaColor = ANALYSIS_ACCENT_COLOR;

  const xAxisLabels = computed(() => props.data.map((item) => item.windSpeed.toFixed(1)));
  const deltaSeries = computed(() =>
    props.data.map((item) => Number((item.after - item.before).toFixed(3))),
  );

  function buildAxisRange(values: number[], paddingRatio = 0.12) {
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const span = Math.max(maxValue - minValue, Math.abs(maxValue) * 0.1, 0.05);
    const padding = span * paddingRatio;
    return {
      min: Number((minValue - padding).toFixed(3)),
      max: Number((maxValue + padding).toFixed(3)),
    };
  }

  const deltaErrorSeries = computed(() =>
    props.data.map((item) => {
      const delta = item.after - item.before;
      const error = Math.max(Math.abs(delta) * 0.28, 0.015);
      return [
        item.windSpeed.toFixed(1),
        Number(delta.toFixed(3)),
        Number((delta - error).toFixed(3)),
        Number((delta + error).toFixed(3)),
      ];
    }),
  );

  const powerAxisRange = computed(() =>
    buildAxisRange(
      props.data.flatMap((item) => [item.before, item.after]),
      0.08,
    ),
  );

  const deltaAxisRange = computed(() => {
    const bounds = deltaErrorSeries.value.flatMap((item) => [Number(item[2]), Number(item[3])]);
    const absoluteMax = Math.max(...bounds.map((item) => Math.abs(item)), 0.05);
    const padding = absoluteMax * 0.16;
    const limit = Number((absoluteMax + padding).toFixed(3));
    return {
      min: -limit,
      max: limit,
    };
  });

  function rayleighCdf(speed: number, sigma: number) {
    if (speed <= 0) return 0;
    return 1 - Math.exp(-(speed ** 2) / (2 * sigma ** 2));
  }

  const windSpeedBins = computed(() =>
    props.data.map((item, index, list) => {
      const current = item.windSpeed;
      const prev = list[index - 1]?.windSpeed ?? (current - (list[index + 1]?.windSpeed - current));
      const next = list[index + 1]?.windSpeed ?? (current + (current - list[index - 1]?.windSpeed));
      return {
        label: current.toFixed(1),
        center: current,
        lower: Number(((prev + current) / 2).toFixed(3)),
        upper: Number(((current + next) / 2).toFixed(3)),
      };
    }),
  );

  const windFrequencyBins = computed(() => {
    const sigma = props.rayleighParameters.sigma;
    const raw = windSpeedBins.value.map((bin) => {
      const probability = rayleighCdf(bin.upper, sigma) - rayleighCdf(bin.lower, sigma);
      return {
        ...bin,
        probability: Math.max(probability, 0),
      };
    });
    const totalProbability = raw.reduce((sum, item) => sum + item.probability, 0) || 1;
    return raw.map((item) => ({
      ...item,
      frequencyRatio: (item.probability / totalProbability) * 100,
    }));
  });

  const backgroundBands = computed(() => {
    const frequencies = windFrequencyBins.value.map((item) => item.frequencyRatio);
    const minFreq = Math.min(...frequencies, 0);
    const maxFreq = Math.max(...frequencies, 0);
    const alphaMax = 0.22;
    const alphaGamma = 5.5;
    return windFrequencyBins.value.map((item) => {
      const ratio =
        maxFreq === minFreq ? 0 : (item.frequencyRatio - minFreq) / (maxFreq - minFreq);
      const alpha = alphaMax * ratio ** alphaGamma;
      return {
        label: item.label,
        alpha: Number(alpha.toFixed(3)),
      };
    });
  });

  function renderErrorBar(params: any, api: any) {
    const category = api.value(0);
    const lower = api.value(2);
    const upper = api.value(3);
    const xCoord = api.coord([category, lower])[0];
    const lowCoord = api.coord([category, lower])[1];
    const highCoord = api.coord([category, upper])[1];
    const cap = 6;
    return {
      type: 'group',
      children: [
        {
          type: 'line',
          shape: { x1: xCoord, y1: highCoord, x2: xCoord, y2: lowCoord },
          style: { stroke: deltaColor, lineWidth: 1.4, opacity: 0.6 },
        },
        {
          type: 'line',
          shape: { x1: xCoord - cap, y1: highCoord, x2: xCoord + cap, y2: highCoord },
          style: { stroke: deltaColor, lineWidth: 1.4, opacity: 0.6 },
        },
        {
          type: 'line',
          shape: { x1: xCoord - cap, y1: lowCoord, x2: xCoord + cap, y2: lowCoord },
          style: { stroke: deltaColor, lineWidth: 1.4, opacity: 0.6 },
        },
      ],
    };
  }

  function renderFrequencyBand(params: any, api: any) {
    const category = api.value(0);
    const alpha = Number(api.value(1));
    const yMin = powerAxisRange.value.min;
    const yMax = powerAxisRange.value.max;
    const start = api.coord([category, yMin]);
    const end = api.coord([category, yMax]);
    const bandWidth = api.size([1, 0])[0];
    return {
      type: 'rect',
      shape: {
        x: start[0] - bandWidth / 2,
        y: end[1],
        width: bandWidth,
        height: start[1] - end[1],
      },
      style: {
        fill: withAlpha(ANALYSIS_OPTIMIZED_COLOR, alpha),
      },
      silent: true,
    };
  }

  const mainChartOption = computed(() => ({
    animationDuration: 320,
    color: [ANALYSIS_BASELINE_COLOR, ANALYSIS_OPTIMIZED_COLOR, deltaColor],
    legend: {
      top: 0,
      right: 0,
      itemWidth: 9,
      itemHeight: 9,
      itemGap: 12,
      textStyle: { color: themeTokens.text3, fontSize: 10 },
      data: ['基准', '优化后', '净收益'],
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: themeTokens.tooltipBg,
      borderColor: themeTokens.tooltipBorder,
      textStyle: themeTokens.tooltipTextStyle,
      formatter(params: any) {
        const beforeItem = params.find((item: any) => item.seriesName === '基准');
        const afterItem = params.find((item: any) => item.seriesName === '优化后');
        const deltaItem = params.find((item: any) => item.seriesName === '净收益');
        const windSpeed = Number(beforeItem?.axisValue ?? afterItem?.axisValue ?? 0);
        const beforeValue = Number(beforeItem?.value ?? 0);
        const afterValue = Number(afterItem?.value ?? 0);
        const deltaValue = Number(deltaItem?.value ?? afterValue - beforeValue);
        const errorDatum = deltaErrorSeries.value.find((item) => item[0] === windSpeed.toFixed(1));
        const lower = Number(errorDatum?.[2] ?? deltaValue);
        const upper = Number(errorDatum?.[3] ?? deltaValue);
        const freqDatum = windFrequencyBins.value.find((item) => item.center === windSpeed);
        return [
          `风速箱: ${windSpeed.toFixed(1)} m/s`,
          `基准: ${beforeValue.toFixed(2)} MW`,
          `优化后: ${afterValue.toFixed(2)} MW`,
          `净收益: ${deltaValue.toFixed(2)} MW`,
          `误差线范围: ${lower.toFixed(2)} ~ ${upper.toFixed(2)} MW`,
          `风频占比: ${Number(freqDatum?.frequencyRatio ?? 0).toFixed(1)}%`,
          '风频来源: 瑞丽分布',
        ].join('<br/>');
      },
    },
    grid: { left: 48, right: 52, top: 24, bottom: 36 },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: xAxisLabels.value,
      name: '风速 (m/s)',
      nameLocation: 'middle',
      nameGap: 26,
      axisLabel: { color: themeTokens.text3, fontSize: 11 },
      nameTextStyle: { color: themeTokens.text3, fontSize: 11 },
      splitLine: { show: false },
      axisLine: { lineStyle: { color: themeTokens.text4 } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '条件化平均功率 (MW)',
        min: powerAxisRange.value.min,
        max: powerAxisRange.value.max,
        nameLocation: 'middle',
        nameGap: 42,
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        nameTextStyle: { color: themeTokens.text3, fontSize: 11 },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
        axisLine: { show: false },
      },
      {
        type: 'value',
        name: '净收益 (MW)',
        min: deltaAxisRange.value.min,
        max: deltaAxisRange.value.max,
        nameLocation: 'middle',
        nameGap: 42,
        axisLabel: { color: themeTokens.text3, fontSize: 10 },
        nameTextStyle: { color: themeTokens.text3, fontSize: 11 },
        interval: Number(
          (((deltaAxisRange.value.max - deltaAxisRange.value.min) / 4) || 0.05).toFixed(3),
        ),
        splitLine: { show: false },
        axisLine: { show: false },
      },
    ],
    series: [
      {
        name: '风频背景',
        type: 'custom',
        renderItem: renderFrequencyBand,
        data: backgroundBands.value.map((item) => [item.label, item.alpha]),
        silent: true,
        tooltip: { show: false },
        z: -20,
      },
      {
        name: '净收益',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: '46%',
        itemStyle: {
          color(params: any) {
            return Number(params.value) >= 0
              ? withAlpha(deltaColor, 0.72)
              : withAlpha(ANALYSIS_BASELINE_COLOR, 0.78);
          },
          borderRadius(params: any) {
            return Number(params.value) >= 0 ? [4, 4, 0, 0] : [0, 0, 4, 4];
          },
        },
        emphasis: {
          itemStyle: {
            color(params: any) {
              return Number(params.value) >= 0 ? deltaColor : ANALYSIS_BASELINE_COLOR;
            },
          },
        },
        data: deltaSeries.value,
        z: 1,
      },
      {
        name: '净收益误差线',
        type: 'custom',
        yAxisIndex: 1,
        renderItem: renderErrorBar,
        data: deltaErrorSeries.value,
        silent: true,
        tooltip: { show: false },
        z: 2,
      },
      {
        name: '基准',
        type: 'line',
        smooth: 0.34,
        showSymbol: false,
        lineStyle: { width: 2, color: ANALYSIS_BASELINE_COLOR },
        data: props.data.map((item) => item.before),
        z: 3,
      },
      {
        name: '优化后',
        type: 'line',
        smooth: 0.34,
        showSymbol: false,
        lineStyle: { width: 2, color: ANALYSIS_OPTIMIZED_COLOR },
        areaStyle: { color: withAlpha(ANALYSIS_OPTIMIZED_COLOR, 0.08) },
        data: props.data.map((item) => item.after),
        z: 4,
      },
    ],
  }) as ECOption);
</script>

<style scoped lang="less">
  .power-curve-card__chart {
    flex: 1;
    min-height: 0;
    height: 100%;
  }
</style>
