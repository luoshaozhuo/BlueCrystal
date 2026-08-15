<template>
  <div class="evidence-chart-card">
    <div class="chart-head">
      <div class="chart-title">能量谱对比</div>
      <div class="chart-subtitle">对比优化前后频域能量分布变化</div>
    </div>
    <VChart class="chart-body" :option="chartOption" autoresize />
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { CanvasRenderer } from 'echarts/renderers';
  import { LineChart } from 'echarts/charts';
  import type { LineSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    TooltipComponent,
    LegendComponent,
    GraphicComponent,
    MarkAreaComponent,
    type GridComponentOption,
    type TooltipComponentOption,
    type LegendComponentOption,
    type GraphicComponentOption,
    type MarkAreaComponentOption,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS } from '@/config/chart-theme';
  import type { EnergySpectrumPoint } from '@/mock/load-mitigation/optimization-evidence';
  import { useThemeTokens } from '@/config/chart-theme';

  use([
    CanvasRenderer,
    LineChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    GraphicComponent,
    MarkAreaComponent,
  ]);

  type ECOption = ComposeOption<
    | LineSeriesOption
    | GridComponentOption
    | TooltipComponentOption
    | LegendComponentOption
    | GraphicComponentOption
    | MarkAreaComponentOption
  >;

  const props = defineProps<{
    data: EnergySpectrumPoint[];
  }>();

  const themeTokens = useThemeTokens();
  const ANALYSIS_BASELINE_COLOR = CHART_COMPARISON_COLORS.baseline;
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;

  function round(value: number, digits = 3) {
    return Number(value.toFixed(digits));
  }

  function formatPercentChange(value: number) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  }

  const chartOption = computed<ECOption>(() => {
    if (!props.data.length) {
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

    const beforeSeries = props.data.map((item) => [
      round(item.frequency, 1),
      round(item.before),
    ]);
    const afterSeries = props.data.map((item) => [
      round(item.frequency, 1),
      round(item.after),
    ]);
    const peakPoint = props.data.reduce((currentPeak, point) =>
      point.before > currentPeak.before ? point : currentPeak,
    );

    return {
      animationDuration: 320,
      color: [ANALYSIS_BASELINE_COLOR, ANALYSIS_OPTIMIZED_COLOR],
      legend: {
        top: 0,
        right: 0,
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { color: themeTokens.text3, fontSize: 11 },
        data: ['优化前', '优化后'],
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          const beforeItem = params.find((item: any) => item.seriesName === '优化前');
          const afterItem = params.find((item: any) => item.seriesName === '优化后');
          const frequency = Number(beforeItem?.value?.[0] ?? afterItem?.value?.[0] ?? 0);
          const beforeValue = Number(beforeItem?.value?.[1] ?? 0);
          const afterValue = Number(afterItem?.value?.[1] ?? 0);
          const delta = afterValue - beforeValue;
          const changeRatio = beforeValue ? (delta / beforeValue) * 100 : 0;

          return [
            `频率: ${frequency.toFixed(1)} Hz`,
            `优化前能量: ${beforeValue.toFixed(3)}`,
            `优化后能量: ${afterValue.toFixed(3)}`,
            `变化量: ${delta.toFixed(3)}`,
            `变化比例: ${formatPercentChange(changeRatio)}`,
          ].join('<br/>');
        },
      },
      grid: {
        left: 44,
        right: 14,
        top: 32,
        bottom: 38,
      },
      xAxis: {
        type: 'value',
        name: '频率 (Hz)',
        nameLocation: 'middle',
        nameGap: 28,
        min: 0,
        max: 30,
        axisLabel: {
          color: themeTokens.text3,
          fontSize: 11,
          formatter(value: number) {
            return Number(value).toFixed(0);
          },
        },
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '归一化能量',
        nameLocation: 'middle',
        nameGap: 36,
        axisLabel: {
          color: themeTokens.text3,
          formatter(value: number) {
            return Number(value).toFixed(1);
          },
        },
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
        axisLine: { show: false },
      },
      series: [
        {
          name: '优化前',
          type: 'line',
          data: beforeSeries,
          smooth: 0.28,
          showSymbol: false,
          lineStyle: {
            width: 2,
            color: ANALYSIS_BASELINE_COLOR,
          },
          areaStyle: {
            color: 'rgba(139, 149, 167, 0.08)',
          },
          markArea: {
            silent: true,
            itemStyle: {
              color: 'rgba(25, 194, 201, 0.06)',
            },
            data: [
              [
                { xAxis: Math.max(round(peakPoint.frequency - 1.5, 1), 0.5) },
                { xAxis: round(peakPoint.frequency + 1.5, 1) },
              ],
            ],
          },
        },
        {
          name: '优化后',
          type: 'line',
          data: afterSeries,
          smooth: 0.28,
          showSymbol: false,
          lineStyle: {
            width: 2,
            color: ANALYSIS_OPTIMIZED_COLOR,
          },
          areaStyle: {
            color: 'rgba(25, 194, 201, 0.09)',
          },
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
