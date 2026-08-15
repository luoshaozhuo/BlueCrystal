<template>
  <div class="evidence-chart-card">
    <div class="chart-head">
      <div class="chart-title">改善稳定性统计</div>
      <div class="chart-subtitle">展示改善窗口覆盖情况</div>
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
  import type { EvidenceStabilityDatum } from '@/mock/load-mitigation/optimization-evidence';
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
    data: EvidenceStabilityDatum[];
  }>();

  const themeTokens = useThemeTokens();
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;
  const stabilityLabels = {
    rmsDropWindowRatio: 'RMS 下降窗口占比',
    p95DropWindowRatio: 'P95 下降窗口占比',
    peakDropWindowRatio: 'Peak 下降窗口占比',
  } as const;

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

    return {
      animationDuration: 320,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          const item = params[0];
          return `${item?.axisValue ?? '-'}<br/>覆盖率：${Number(item?.value ?? 0).toFixed(1)}%`;
        },
      },
      grid: {
        left: 98,
        right: 14,
        top: 12,
        bottom: 20,
      },
      xAxis: {
        type: 'value',
        max: 100,
        axisLabel: { color: themeTokens.text3, formatter: '{value}%' },
        splitLine: { lineStyle: { color: themeTokens.fill3 } },
        axisLine: { show: false },
      },
      yAxis: {
        type: 'category',
        data: props.data.map((item) => stabilityLabels[item.key]),
        axisLabel: { color: themeTokens.text3, fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: props.data.map((item) => item.value),
          barWidth: 16,
          showBackground: true,
          backgroundStyle: {
            color: 'rgba(120, 157, 204, 0.10)',
            borderRadius: 999,
          },
          itemStyle: {
            color: ANALYSIS_OPTIMIZED_COLOR,
            borderRadius: 999,
          },
          label: {
            show: true,
            position: 'right',
            color: themeTokens.text2,
            formatter: '{c}%',
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
