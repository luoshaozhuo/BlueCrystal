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
  import { CHART_COMPARISON_COLORS, useThemeTokens, withAlpha } from '@/config/chart-theme';
  import type { DistributionShiftEvidence, DistributionShiftGroup, QuantileStats } from '@/types/power-analysis';

  use([CanvasRenderer, ScatterChart, CustomChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent]);

  type ECOption = ComposeOption<
    | CustomSeriesOption
    | ScatterSeriesOption
    | GridComponentOption
    | LegendComponentOption
    | TitleComponentOption
    | TooltipComponentOption
  >;

  const props = defineProps<{ data: DistributionShiftEvidence }>();
  const themeTokens = useThemeTokens();

  const baselineColor = CHART_COMPARISON_COLORS.baseline;
  const optimizedColor = CHART_COMPARISON_COLORS.optimized;
  const baselineLegendColor = withAlpha(baselineColor, 0.78);
  const optimizedLegendColor = withAlpha(optimizedColor, 0.78);
  const GROUP_CENTERS = { Peak: 0, P95: 1, P99: 2 } as const;
  const BASE_OFFSET = -0.18;
  const OPT_OFFSET = 0.18;
  const boxHalfWidth = 0.05;
  const medianHalfWidth = 0.07;
  const whiskerHalfWidth = 0.025;

  function round(value: number, digits = 3) {
    return Number(value.toFixed(digits));
  }

  function getGroupCenter(metric: keyof typeof GROUP_CENTERS) {
    return GROUP_CENTERS[metric];
  }

  function getScenarioX(metric: keyof typeof GROUP_CENTERS, condition: '基准' | '优化后') {
    return getGroupCenter(metric) + (condition === '基准' ? BASE_OFFSET : OPT_OFFSET);
  }

  function createScatterPoints(groups: DistributionShiftGroup[], condition: '基准' | '优化后') {
    return groups.flatMap((group) => {
      const isBaseline = condition === '基准';
      const center = getScenarioX(group.metric, condition);
      const samples = isBaseline ? group.baselineSamples : group.optimizedSamples;
      const stats = isBaseline ? group.baselineStats : group.optimizedStats;

      return samples.map((value, sampleIndex) => {
        const jitterSeed = ((sampleIndex % 7) - 3) * 0.014 + Math.floor(sampleIndex / 7) * 0.002;
        return {
          value: [center + jitterSeed, value],
          metric: group.metric,
          condition,
          sampleValue: value,
          stats,
        };
      });
    });
  }

  function createBoxData(groups: DistributionShiftGroup[], condition: '基准' | '优化后') {
    return groups.map((group) => {
      const stats = condition === '基准' ? group.baselineStats : group.optimizedStats;
      return {
        value: [getScenarioX(group.metric, condition), stats.p10, stats.p25, stats.median, stats.p75, stats.p90],
        metric: group.metric,
        condition,
      };
    });
  }

  function getXSpan(api: any, center: number, halfWidth: number, y: number) {
    const left = api.coord([center - halfWidth, y])[0];
    const right = api.coord([center + halfWidth, y])[0];
    return { left, right };
  }

  function boxRender(color: string, fill: string) {
    return (_params: any, api: any) => {
      const x = Number(api.value(0));
      const p10 = Number(api.value(1));
      const p25 = Number(api.value(2));
      const median = Number(api.value(3));
      const p75 = Number(api.value(4));
      const p90 = Number(api.value(5));
      const whiskerTop = api.coord([x, p90]);
      const whiskerBottom = api.coord([x, p10]);
      const boxTop = api.coord([x, p75]);
      const boxBottom = api.coord([x, p25]);
      const medianPoint = api.coord([x, median]);
      const boxSpanTop = getXSpan(api, x, boxHalfWidth, p75);
      const boxSpanBottom = getXSpan(api, x, boxHalfWidth, p25);
      const medianSpan = getXSpan(api, x, medianHalfWidth, median);
      const whiskerTopSpan = getXSpan(api, x, whiskerHalfWidth, p90);
      const whiskerBottomSpan = getXSpan(api, x, whiskerHalfWidth, p10);

      return {
        type: 'group' as const,
        silent: true,
        children: [
          {
            type: 'line' as const,
            shape: {
              x1: whiskerTop[0],
              y1: whiskerTop[1],
              x2: whiskerBottom[0],
              y2: whiskerBottom[1],
            },
            style: { stroke: color, lineWidth: 1.2 },
          },
          {
            type: 'line' as const,
            shape: {
              x1: whiskerTopSpan.left,
              y1: whiskerTop[1],
              x2: whiskerTopSpan.right,
              y2: whiskerTop[1],
            },
            style: { stroke: color, lineWidth: 1.2 },
          },
          {
            type: 'line' as const,
            shape: {
              x1: whiskerBottomSpan.left,
              y1: whiskerBottom[1],
              x2: whiskerBottomSpan.right,
              y2: whiskerBottom[1],
            },
            style: { stroke: color, lineWidth: 1.2 },
          },
          {
            type: 'rect' as const,
            shape: {
              x: boxSpanTop.left,
              y: boxTop[1],
              width: Math.max(boxSpanTop.right - boxSpanTop.left, 2),
              height: Math.max(boxBottom[1] - boxTop[1], 2),
            },
            style: {
              fill,
              stroke: color,
              lineWidth: 1.2,
            },
          },
          {
            type: 'line' as const,
            shape: {
              x1: medianSpan.left,
              y1: medianPoint[1],
              x2: medianSpan.right,
              y2: medianPoint[1],
            },
            style: { stroke: color, lineWidth: 2 },
          },
        ],
      };
    };
  }

  const option = computed<ECOption>(() => {
    const allValues = props.data.groups.flatMap((group) => [...group.baselineSamples, ...group.optimizedSamples]);
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const span = Math.max(maxValue - minValue, 0.4);

    return {
      animationDuration: 260,
      title: {
        text: '分布迁移',
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
            itemStyle: { color: baselineLegendColor },
          },
          {
            name: '优化后',
            itemStyle: { color: optimizedLegendColor },
          },
        ],
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          const stats: QuantileStats = params.data?.stats;
          return [
            `指标: ${params.data?.metric ?? '-'}`,
            `工况: ${params.data?.condition ?? '-'}`,
            `样本值: ${Number(params.data?.sampleValue ?? 0).toFixed(3)}`,
            `Median: ${stats?.median.toFixed(3) ?? '-'}`,
            `P25 / P75: ${stats?.p25.toFixed(3) ?? '-'} / ${stats?.p75.toFixed(3) ?? '-'}`,
            `P10 / P90: ${stats?.p10.toFixed(3) ?? '-'} / ${stats?.p90.toFixed(3) ?? '-'}`,
          ].join('<br/>');
        },
      },
      grid: { left: 42, right: 10, top: 22, bottom: 28, containLabel: true },
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
        min: round(minValue - span * 0.08, 2),
        max: round(maxValue + span * 0.10, 2),
        name: '风险幅值',
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
          name: '基准',
          type: 'scatter',
          z: 2,
          clip: true,
          symbolSize: 7,
          itemStyle: { color: baselineLegendColor },
          data: createScatterPoints(props.data.groups, '基准'),
        },
        {
          name: '优化后',
          type: 'scatter',
          z: 2,
          clip: true,
          symbolSize: 7,
          itemStyle: { color: optimizedLegendColor },
          data: createScatterPoints(props.data.groups, '优化后'),
        },
        {
          name: '基准分位区间',
          type: 'custom',
          z: 5,
          silent: true,
          clip: true,
          renderItem: boxRender(baselineColor, withAlpha(baselineColor, 0.14)),
          data: createBoxData(props.data.groups, '基准'),
        },
        {
          name: '优化后分位区间',
          type: 'custom',
          z: 5,
          silent: true,
          clip: true,
          renderItem: boxRender(optimizedColor, withAlpha(optimizedColor, 0.14)),
          data: createBoxData(props.data.groups, '优化后'),
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
