<template>
  <div class="high-amplitude-risk-chart">
    <div class="chart-head">
      <div class="chart-title">高幅值占比对比</div>
      <div class="chart-subtitle">各均值段高幅值循环占比</div>
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
    LegendComponent,
    GraphicComponent,
    type GridComponentOption,
    type TooltipComponentOption,
    type LegendComponentOption,
    type GraphicComponentOption,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { CHART_COMPARISON_COLORS } from '@/config/chart-theme';
  import type {
    AmplitudeStructureComparisonData,
    MeanBinDistribution,
  } from '@/mock/load-mitigation/amplitude-structure';
  import { useThemeTokens } from '@/config/chart-theme';

  use([
    CanvasRenderer,
    BarChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    GraphicComponent,
  ]);

  type ECOption = ComposeOption<
    | BarSeriesOption
    | GridComponentOption
    | TooltipComponentOption
    | LegendComponentOption
    | GraphicComponentOption
  >;

  const props = withDefaults(
    defineProps<{
      data?: AmplitudeStructureComparisonData | null;
      highAmplitudeBins?: string[];
      showLabels?: boolean;
    }>(),
    {
      highAmplitudeBins: () => ['40-50', '50-60'],
      showLabels: false,
    },
  );
  const themeTokens = useThemeTokens();
  const ANALYSIS_BASELINE_COLOR = CHART_COMPARISON_COLORS.baseline;
  const ANALYSIS_OPTIMIZED_COLOR = CHART_COMPARISON_COLORS.optimized;

  function normalizeValues(values: number[], expectedLength: number) {
    const safe = Array.from({ length: expectedLength }, (_, index) =>
      Math.max(values[index] ?? 0, 0),
    );
    const total = safe.reduce((sum, value) => sum + value, 0);
    if (!total) return safe.map(() => 0);
    return safe.map((value) => value / total);
  }

  function buildRowMap(rows: MeanBinDistribution[]) {
    return new Map(rows.map((row) => [row.meanBin, row.values]));
  }

  function formatPct(value: number) {
    return `${value.toFixed(1)}%`;
  }

  function formatPctPoint(value: number) {
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(1)} pct`;
  }

  function compressBinsLabel(bins: string[]) {
    if (!bins.length) return '-';
    if (bins.length === 1) return bins[0];
    const first = bins[0].split('-')[0];
    const last = bins[bins.length - 1].split('-')[1];
    return `${first}-${last}`;
  }

  // 汇总每个均值区间内的高幅值循环占比
  function calculateHighAmplitudeRisk(
    data: AmplitudeStructureComparisonData,
    highAmplitudeBins: string[],
  ) {
    const amplitudeBins = Array.isArray(data.amplitudeBins)
      ? data.amplitudeBins
      : [];
    const meanBins = Array.isArray(data.meanBins) ? data.meanBins : [];
    const targetIndexes = highAmplitudeBins
      .map((bin) => amplitudeBins.indexOf(bin))
      .filter((index) => index >= 0);

    const baselineMap = buildRowMap(
      Array.isArray(data.baseline) ? data.baseline : [],
    );
    const optimizedMap = buildRowMap(
      Array.isArray(data.optimized) ? data.optimized : [],
    );

    const baselineRisk: number[] = [];
    const optimizedRisk: number[] = [];

    meanBins.forEach((meanBin) => {
      const baselineValues = normalizeValues(
        baselineMap.get(meanBin) ?? [],
        amplitudeBins.length,
      );
      const optimizedValues = normalizeValues(
        optimizedMap.get(meanBin) ?? [],
        amplitudeBins.length,
      );

      const baselineValue = targetIndexes.reduce(
        (sum, index) => sum + (baselineValues[index] ?? 0),
        0,
      );
      const optimizedValue = targetIndexes.reduce(
        (sum, index) => sum + (optimizedValues[index] ?? 0),
        0,
      );

      baselineRisk.push(Number((baselineValue * 100).toFixed(1)));
      optimizedRisk.push(Number((optimizedValue * 100).toFixed(1)));
    });

    return {
      meanBins,
      baselineRisk,
      optimizedRisk,
      effectiveHighAmplitudeBins: highAmplitudeBins.filter((bin) =>
        amplitudeBins.includes(bin),
      ),
    };
  }

  const riskSummary = computed(() => {
    const source = props.data;
    if (!source?.meanBins?.length || !source?.amplitudeBins?.length)
      return null;
    return calculateHighAmplitudeRisk(source, props.highAmplitudeBins);
  });

  const chartOption = computed<ECOption>(() => {
    if (!riskSummary.value) {
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
            fontWeight: 500,
          },
        },
      };
    }

    const {
      meanBins,
      baselineRisk,
      optimizedRisk,
      effectiveHighAmplitudeBins,
    } = riskSummary.value;

    const highAmplitudeLabel = compressBinsLabel(effectiveHighAmplitudeBins);
    const maxValue = Math.max(...baselineRisk, ...optimizedRisk);
    const yAxisMax = Math.max(30, Math.ceil((maxValue + 4) / 5) * 5);
    const yAxisInterval = yAxisMax / 5;

    const labelConfig = props.showLabels
      ? {
          show: true,
          position: 'top' as const,
          color: themeTokens.text3,
          fontSize: 11,
          formatter: '{c}%',
        }
      : { show: false };

    return {
      animationDuration: 350,
      color: [ANALYSIS_BASELINE_COLOR, ANALYSIS_OPTIMIZED_COLOR],
      legend: {
        top: 0,
        right: 0,
        itemWidth: 10,
        itemHeight: 10,
        textStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        data: ['优化前', '优化后'],
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
          shadowStyle: {
            color: 'rgba(120, 157, 204, 0.10)',
          },
        },
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
          const baselineValue = Number(baselineItem?.value ?? 0);
          const optimizedValue = Number(optimizedItem?.value ?? 0);
          const diff = optimizedValue - baselineValue;

          return [
            `均值区间：${baselineItem?.axisValue ?? '-'}`,
            `高幅值定义：${highAmplitudeLabel}`,
            `优化前占比：${formatPct(baselineValue)}`,
            `优化后占比：${formatPct(optimizedValue)}`,
            `变化量：${formatPctPoint(diff)}`,
          ].join('<br/>');
        },
      },
      grid: {
        left: 42,
        right: 16,
        top: 72,
        bottom: 28,
      },
      xAxis: {
        type: 'category',
        data: meanBins,
        axisLabel: {
          color: themeTokens.text3,
          interval: 0,
        },
        axisLine: {
          lineStyle: {
            color: themeTokens.text4,
          },
        },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        scale: false,
        name: '高幅值循环占比 (%)',
        min: 0,
        max: yAxisMax,
        interval: yAxisInterval,
        splitNumber: 5,
        axisLabel: {
          color: themeTokens.text3,
          formatter: '{value}%',
        },
        nameTextStyle: {
          color: themeTokens.text3,
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: themeTokens.text4,
          },
        },
        axisTick: { show: false },
        splitLine: {
          lineStyle: {
            color: themeTokens.fill3,
          },
        },
      },
      series: [
        {
          name: '优化前',
          type: 'bar',
          barWidth: 16,
          barGap: '20%',
          data: baselineRisk,
          label: labelConfig,
          itemStyle: {
            opacity: 0.92,
          },
        },
        {
          name: '优化后',
          type: 'bar',
          barWidth: 16,
          data: optimizedRisk,
          label: labelConfig,
          itemStyle: {
            opacity: 0.96,
          },
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .high-amplitude-risk-chart {
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .chart-head {
    flex: 0 0 auto;
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
