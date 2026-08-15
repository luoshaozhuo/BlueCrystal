<template>
  <div class="evidence-chart-card">
    <div class="chart-head">
      <div>
        <div class="chart-title">峰值分布 QQ 对比</div>
        <div class="chart-subtitle">对比优化前后峰值样本分布变化</div>
      </div>
    </div>
    <VChart class="chart-body" :option="chartOption" autoresize />
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { CanvasRenderer } from 'echarts/renderers';
  import { LineChart, ScatterChart } from 'echarts/charts';
  import type { LineSeriesOption, ScatterSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    TooltipComponent,
    LegendComponent,
    GraphicComponent,
    type GridComponentOption,
    type TooltipComponentOption,
    type LegendComponentOption,
    type GraphicComponentOption,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS } from '@/config/chart-theme';
  import type { PeakQqEvidence } from '@/mock/load-mitigation/optimization-evidence';
  import { useThemeTokens } from '@/config/chart-theme';

  use([
    CanvasRenderer,
    LineChart,
    ScatterChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    GraphicComponent,
  ]);

  type ECOption = ComposeOption<
    | LineSeriesOption
    | ScatterSeriesOption
    | GridComponentOption
    | TooltipComponentOption
    | LegendComponentOption
    | GraphicComponentOption
  >;

  interface QqPointDatum {
    quantile: number;
    before: number;
    after: number;
    delta: number;
    changeRatio: number;
  }

  interface QqPointMeta {
    value: [number, number];
    quantile: number;
    before: number;
    after: number;
    delta: number;
    changeRatio: number;
  }

  const props = defineProps<{
    unit: string;
    data: PeakQqEvidence;
  }>();

  const themeTokens = useThemeTokens();
  const ANALYSIS_BASELINE_COLOR = CHART_COMPARISON_COLORS.baseline;
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;

  function round(value: number, digits = 3) {
    return Number(value.toFixed(digits));
  }

  function sortNumeric(values: number[]) {
    return [...values].sort((left, right) => left - right);
  }

  function sampleQuantile(sortedValues: number[], quantile: number) {
    if (!sortedValues.length) return 0;
    if (sortedValues.length === 1) return sortedValues[0];
    const safeQuantile = Math.min(Math.max(quantile, 0), 1);
    const index = safeQuantile * (sortedValues.length - 1);
    const lowerIndex = Math.floor(index);
    const upperIndex = Math.ceil(index);
    const lowerValue = sortedValues[lowerIndex] ?? sortedValues[0];
    const upperValue =
      sortedValues[upperIndex] ?? sortedValues[sortedValues.length - 1];
    if (lowerIndex === upperIndex) return lowerValue;
    const weight = index - lowerIndex;
    return lowerValue + (upperValue - lowerValue) * weight;
  }

  function buildQqPoints(evidence: PeakQqEvidence): QqPointDatum[] {
    const beforeSorted = sortNumeric(evidence.beforePeaks);
    const afterSorted = sortNumeric(evidence.afterPeaks);
    const sampleCount = Math.min(beforeSorted.length, afterSorted.length);

    if (!sampleCount) return [];

    return Array.from({ length: sampleCount }, (_, index) => {
      const quantile = (index + 1) / (sampleCount + 1);
      const before = round(sampleQuantile(beforeSorted, quantile));
      const after = round(sampleQuantile(afterSorted, quantile));
      const delta = round(after - before);
      const changeRatio = before ? ((after - before) / before) * 100 : 0;

      return {
        quantile,
        before,
        after,
        delta,
        changeRatio,
      };
    });
  }

  function buildReferenceLine(points: QqPointDatum[]): [[number, number], [number, number]] {
    if (!points.length) return [[0, 0], [0, 0]];
    const allValues = points.flatMap((point) => [point.before, point.after]);
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    return [
      [round(minValue), round(minValue)],
      [round(maxValue), round(maxValue)],
    ];
  }

  function formatPercentChange(value: number) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  }

  const chartOption = computed<ECOption>(() => {
    const qqPoints = buildQqPoints(props.data);

    if (!qqPoints.length) {
      return {
        animation: false,
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '暂无有效数据',
            fill: themeTokens.text3,
            fontSize: 14,
          },
        },
      };
    }

    const scatterData: QqPointMeta[] = qqPoints.map((point) => ({
      value: [point.before, point.after],
      quantile: point.quantile,
      before: point.before,
      after: point.after,
      delta: point.delta,
      changeRatio: point.changeRatio,
    }));
    const referenceLine = buildReferenceLine(qqPoints);

    return {
      animationDuration: 300,
      color: [ANALYSIS_OPTIMIZED_COLOR, ANALYSIS_BASELINE_COLOR],
      legend: {
        top: 0,
        right: 0,
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { color: themeTokens.text3, fontSize: 11 },
        data: ['QQ散点', '参考线 y=x'],
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          if (params.seriesName !== 'QQ散点' || !params.data) {
            return '参考线 y=x';
          }

          const point = params.data as QqPointMeta;
          return [
            `分位点: Q${Math.round(point.quantile * 100)}`,
            `优化前: ${point.before.toFixed(3)} ${props.unit}`.trim(),
            `优化后: ${point.after.toFixed(3)} ${props.unit}`.trim(),
            `变化量: ${point.delta.toFixed(3)} ${props.unit}`.trim(),
            `变化比例: ${formatPercentChange(point.changeRatio)}`,
          ].join('<br/>');
        },
      },
      grid: {
        left: 52,
        right: 18,
        top: 42,
        bottom: 38,
      },
      xAxis: {
        type: 'value',
        name: `优化前峰值样本分位数${props.unit ? ` (${props.unit})` : ''}`,
        nameLocation: 'middle',
        nameGap: 28,
        min: referenceLine[0][0],
        max: referenceLine[1][0],
        axisLabel: {
          color: themeTokens.text3,
          fontSize: 11,
          formatter(value: number) {
            return Number(value).toFixed(props.unit === 'm/s^2' ? 2 : 1);
          },
        },
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        axisTick: { lineStyle: { color: themeTokens.text4 } },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
      },
      yAxis: {
        type: 'value',
        name: `优化后峰值样本分位数${props.unit ? ` (${props.unit})` : ''}`,
        nameLocation: 'middle',
        nameGap: 34,
        min: referenceLine[0][1],
        max: referenceLine[1][1],
        axisLabel: {
          color: themeTokens.text3,
          formatter(value: number) {
            return Number(value).toFixed(props.unit === 'm/s^2' ? 2 : 1);
          },
        },
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        axisTick: { lineStyle: { color: themeTokens.text4 } },
      },
      series: [
        {
          name: 'QQ散点',
          type: 'scatter',
          data: scatterData,
          symbolSize: 9,
          itemStyle: {
            color: ANALYSIS_OPTIMIZED_COLOR,
            borderColor: 'rgba(25, 194, 201, 0.28)',
            borderWidth: 1,
            shadowBlur: 10,
            shadowColor: 'rgba(25, 194, 201, 0.16)',
          },
          emphasis: {
            scale: 1.08,
          },
        },
        {
          name: '参考线 y=x',
          type: 'line',
          data: referenceLine,
          symbol: 'none',
          lineStyle: {
            color: ANALYSIS_BASELINE_COLOR,
            type: 'dashed',
            width: 1.5,
          },
          tooltip: { show: false },
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .evidence-chart-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .chart-head {
    margin-bottom: 6px;
  }

  .chart-title {
    font-size: 12px;
    line-height: 1.25;
    color: var(--color-text-2);
  }

  .chart-subtitle {
    margin-top: 2px;
    font-size: 11px;
    line-height: 1.3;
    color: var(--color-text-3);
  }

  .chart-body {
    flex: 1;
    min-height: 0;
  }
</style>
