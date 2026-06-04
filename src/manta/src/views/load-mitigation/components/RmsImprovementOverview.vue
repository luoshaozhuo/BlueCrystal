<template>
  <div class="evidence-chart-card">
    <div class="chart-head">
      <div>
        <div class="chart-title">RMS 改善总览</div>
        <div class="chart-subtitle">对比优化前后均方根水平变化</div>
      </div>
      <div class="head-badge">{{ summaryText }}</div>
    </div>
    <VChart class="chart-body" :option="chartOption" autoresize />
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { CanvasRenderer } from 'echarts/renderers';
  import { BarChart } from 'echarts/charts';
  import type { BarSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    TooltipComponent,
    GraphicComponent,
    type GridComponentOption,
    type TooltipComponentOption,
    type GraphicComponentOption,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS } from '@/config/chart-theme';
  import type { EvidenceBarDatum } from '@/mock/load-mitigation/optimization-evidence';
  import { useThemeTokens } from '@/config/chart-theme';

  use([
    CanvasRenderer,
    BarChart,
    GridComponent,
    TooltipComponent,
    GraphicComponent,
  ]);

  type ECOption = ComposeOption<
    | BarSeriesOption
    | GridComponentOption
    | TooltipComponentOption
    | GraphicComponentOption
  >;

  const props = defineProps<{
    unit: string;
    data: EvidenceBarDatum[];
  }>();

  const themeTokens = useThemeTokens();
  const ANALYSIS_BASELINE_COLOR = CHART_COMPARISON_COLORS.baseline;
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;

  function roundAxisValue(value: number, digits = 3) {
    return Number(value.toFixed(digits));
  }

  function buildAdaptiveAxisRange(values: number[]) {
    const safeValues = values.filter((value) => Number.isFinite(value));
    if (!safeValues.length) {
      return {
        min: 0,
        max: 1,
      };
    }

    const rawMin = Math.min(...safeValues);
    const rawMax = Math.max(...safeValues);

    if (rawMin === rawMax) {
      const padding = Math.max(Math.abs(rawMax) * 0.12, 0.1);
      return {
        min: roundAxisValue(rawMin - padding),
        max: roundAxisValue(rawMax + padding),
      };
    }

    const span = rawMax - rawMin;
    const padding = span * 0.16;

    return {
      min: roundAxisValue(Math.max(rawMin - padding, 0)),
      max: roundAxisValue(rawMax + padding),
    };
  }

  const summaryText = computed(() => {
    if (!props.data.length) return '-';
    const avgDrop =
      props.data.reduce(
        (sum, item) => sum + Math.abs(Math.min(item.changePct, 0)),
        0,
      ) / props.data.length;
    return `平均降幅 ${avgDrop.toFixed(1)}%`;
  });

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

    const labels = props.data.map((item) => item.label);
    const baseline = props.data.map((item) => item.baseline);
    const optimized = props.data.map((item) => item.optimized);
    const axisRange = buildAdaptiveAxisRange([...baseline, ...optimized]);

    return {
      animationDuration: 300,
      color: [ANALYSIS_BASELINE_COLOR, ANALYSIS_OPTIMIZED_COLOR],
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          const baselineItem = params.find(
            (item: any) => item.seriesName === '优化前',
          );
          const optimizedItem = params.find(
            (item: any) => item.seriesName === '优化后',
          );
          const diffPct =
            props.data[baselineItem?.dataIndex ?? 0]?.changePct ?? 0;
          return [
            `${baselineItem?.axisValue ?? '-'}`,
            `优化前：${Number(baselineItem?.value ?? 0).toFixed(2)} ${props.unit}`.trim(),
            `优化后：${Number(optimizedItem?.value ?? 0).toFixed(2)} ${props.unit}`.trim(),
            `变化：${diffPct.toFixed(1)}%`,
          ].join('<br/>');
        },
      },
      grid: {
        left: 42,
        right: 12,
        top: 24,
        bottom: 30,
      },
      xAxis: {
        type: 'category',
        name: '时间窗口宽度',
        nameLocation: 'middle',
        nameGap: 26,
        data: labels,
        axisLabel: { color: themeTokens.text3, fontSize: 11, interval: 0 },
        nameTextStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        axisLine: { lineStyle: { color: themeTokens.text4 } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: axisRange.min,
        max: axisRange.max,
        axisLabel: { color: themeTokens.text3 },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
        axisLine: { show: false },
      },
      series: [
        {
          name: '优化前',
          type: 'bar',
          barWidth: 12,
          data: baseline,
        },
        {
          name: '优化后',
          type: 'bar',
          barWidth: 12,
          data: optimized,
          label: {
            show: true,
            position: 'top',
            color: themeTokens.text3,
            fontSize: 10,
            formatter(params: any) {
              const diff = props.data[params.dataIndex]?.changePct ?? 0;
              return `${diff.toFixed(1)}%`;
            },
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
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
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

  .head-badge {
    padding: 3px 8px;
    border: 1px solid rgba(var(--primary-6), 0.28);
    border-radius: 999px;
    font-size: 11px;
    line-height: 1.2;
    color: rgb(var(--primary-6));
    background: rgba(var(--primary-6), 0.08);
    white-space: nowrap;
  }

  .chart-body {
    flex: 1;
    min-height: 0;
  }
</style>
