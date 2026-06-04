<template>
  <div class="load-cycle-migration-chart">
    <div class="chart-head">
      <div class="chart-copy">
        <div class="chart-title">循环迁移差值</div>
        <div class="chart-subtitle">显示优化后相对基线的循环占比变化</div>
      </div>
      <a-radio-group
        v-model="currentMode"
        size="mini"
        class="chart-mode-switch"
      >
        <a-radio
          v-for="item in modeOptions"
          :key="item.value"
          :value="item.value"
        >
          {{ item.label }}
        </a-radio>
      </a-radio-group>
    </div>
    <div class="chart-stage">
      <VChart class="chart-body" :option="chartOption" autoresize />
      <div class="chart-x-axis-label" :style="{ color: themeTokens.text3 }">
        循环均值区间
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { computed, ref, watch } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { CanvasRenderer } from 'echarts/renderers';
  import { HeatmapChart } from 'echarts/charts';
  import type { HeatmapSeriesOption } from 'echarts/charts';
  import {
    GridComponent,
    TooltipComponent,
    VisualMapComponent,
    GraphicComponent,
    type GridComponentOption,
    type TooltipComponentOption,
    type VisualMapComponentOption,
    type GraphicComponentOption,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import type {
    MarkovMatrixComparisonData,
    MarkovMatrixMode,
  } from '@/mock/load-mitigation/markov-matrix';
  import { useThemeTokens } from '@/config/chart-theme';

  use([
    CanvasRenderer,
    HeatmapChart,
    GridComponent,
    TooltipComponent,
    VisualMapComponent,
    GraphicComponent,
  ]);

  type ECOption = ComposeOption<
    | HeatmapSeriesOption
    | GridComponentOption
    | TooltipComponentOption
    | VisualMapComponentOption
    | GraphicComponentOption
  >;

  interface HeatmapDatum {
    value: [number, number, number];
    baseline: number;
    optimized: number;
    baselineCount?: number | null;
    optimizedCount?: number | null;
  }

  const props = withDefaults(
    defineProps<{
      data?: MarkovMatrixComparisonData | null;
      mode?: MarkovMatrixMode;
      showCellLabel?: boolean;
      showVisualMap?: boolean;
    }>(),
    {
      mode: 'difference',
      showCellLabel: true,
      showVisualMap: false,
    },
  );

  const modeOptions: Array<{ label: string; value: MarkovMatrixMode }> = [
    { label: '差值', value: 'difference' },
    { label: '基线', value: 'baseline' },
    { label: '优化', value: 'optimized' },
  ];

  const currentMode = ref<MarkovMatrixMode>(props.mode);
  const themeTokens = useThemeTokens();

  watch(
    () => props.mode,
    (value) => {
      currentMode.value = value;
    },
  );

  function normalizeMatrix(
    matrix: number[][],
    rowCount: number,
    columnCount: number,
  ) {
    const safeMatrix = Array.from({ length: rowCount }, (_, rowIndex) =>
      Array.from({ length: columnCount }, (_, columnIndex) => {
        const value = Number(matrix?.[rowIndex]?.[columnIndex] ?? 0);
        return Number.isFinite(value) ? Math.max(value, 0) : 0;
      }),
    );
    const total = safeMatrix.reduce(
      (sum, row) => sum + row.reduce((rowSum, value) => rowSum + value, 0),
      0,
    );
    if (!total) {
      return safeMatrix.map((row) => row.map(() => 0));
    }
    return safeMatrix.map((row) =>
      row.map((value) => Number((value / total).toFixed(6))),
    );
  }

  function validateMatrixDimensions(
    matrix: number[][],
    rowCount: number,
    columnCount: number,
  ) {
    return (
      Array.isArray(matrix) &&
      matrix.length === rowCount &&
      matrix.every((row) => Array.isArray(row) && row.length === columnCount)
    );
  }

  function buildHeatmapData(
    baseline: number[][],
    optimized: number[][],
    baselineCounts?: number[][],
    optimizedCounts?: number[][],
  ) {
    const rowCount = baseline.length;
    const columnCount = baseline[0]?.length ?? 0;
    const result: HeatmapDatum[] = [];

    for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
      for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
        const baselineValue = baseline[rowIndex][columnIndex];
        const optimizedValue = optimized[rowIndex][columnIndex];
        const displayValue =
          currentMode.value === 'baseline'
            ? baselineValue
            : currentMode.value === 'optimized'
              ? optimizedValue
              : optimizedValue - baselineValue;

        result.push({
          value: [columnIndex, rowIndex, Number(displayValue.toFixed(6))],
          baseline: baselineValue,
          optimized: optimizedValue,
          baselineCount: baselineCounts?.[rowIndex]?.[columnIndex] ?? null,
          optimizedCount: optimizedCounts?.[rowIndex]?.[columnIndex] ?? null,
        });
      }
    }

    return result;
  }

  function formatPercent(value: number, withSign = false) {
    const prefix = withSign && value > 0 ? '+' : '';
    return `${prefix}${(value * 100).toFixed(2)}%`;
  }

  function formatPct(value: number) {
    const prefix = value > 0 ? '+' : '';
    return `${prefix}${(value * 100).toFixed(2)} pct`;
  }

  const preparedData = computed(() => {
    const source = props.data;
    if (!source) {
      return { status: 'empty' as const };
    }
    const meanBins = Array.isArray(source.meanBins) ? source.meanBins : [];
    const amplitudeBins = Array.isArray(source.amplitudeBins)
      ? source.amplitudeBins
      : [];

    if (!meanBins.length || !amplitudeBins.length) {
      return { status: 'empty' as const };
    }

    const rowCount = amplitudeBins.length;
    const columnCount = meanBins.length;

    if (
      !validateMatrixDimensions(source.baseline, rowCount, columnCount) ||
      !validateMatrixDimensions(source.optimized, rowCount, columnCount)
    ) {
      return { status: 'invalid' as const };
    }

    const baseline = normalizeMatrix(source.baseline, rowCount, columnCount);
    const optimized = normalizeMatrix(source.optimized, rowCount, columnCount);
    const heatmapData = buildHeatmapData(
      baseline,
      optimized,
      source.counts?.baseline,
      source.counts?.optimized,
    );

    const diffAbsMax = Math.max(
      ...heatmapData.map((item) => Math.abs(item.value[2])),
      0.0001,
    );
    const baselineMax = Math.max(...baseline.flat(), 0.0001);
    const optimizedMax = Math.max(...optimized.flat(), 0.0001);

    return {
      status: 'ready' as const,
      meanBins,
      amplitudeBins,
      heatmapData,
      diffAbsMax,
      baselineMax,
      optimizedMax,
    };
  });

  const chartOption = computed<ECOption>(() => {
    if (preparedData.value.status === 'empty') {
      return {
        animation: false,
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '暂无矩阵数据',
            fill: themeTokens.text3,
            fontSize: 14,
            fontWeight: 500,
          },
        },
      };
    }

    if (preparedData.value.status === 'invalid') {
      return {
        animation: false,
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '矩阵维度不一致',
            fill: themeTokens.danger6,
            fontSize: 14,
            fontWeight: 500,
          },
        },
      };
    }

    const {
      meanBins,
      amplitudeBins,
      heatmapData,
      diffAbsMax,
      baselineMax,
      optimizedMax,
    } = preparedData.value;
    const valueMax =
      currentMode.value === 'difference'
        ? diffAbsMax
        : currentMode.value === 'baseline'
          ? baselineMax
          : optimizedMax;

    const visualMapPieces =
      currentMode.value === 'difference'
        ? {
            min: -valueMax,
            max: valueMax,
            inRange: {
              color: ['#1b8a5a', '#23303d', '#c63f3f'],
            },
          }
        : {
            min: 0,
            max: valueMax,
            inRange: {
              color: ['#18232f', '#23415f', '#3c6d9f', '#d58c3d'],
            },
          };

    return {
      animation: false,
      grid: {
        left: 76,
        right: props.showVisualMap ? 54 : 14,
        top: 18,
        bottom: 28,
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          const datum = params.data as HeatmapDatum;
          const meanBin = meanBins[datum.value[0]];
          const amplitudeBin = amplitudeBins[datum.value[1]];
          if (currentMode.value === 'difference') {
            return [
              `幅值区间：${amplitudeBin}`,
              `均值区间：${meanBin}`,
              `基线占比：${formatPercent(datum.baseline)}`,
              `优化占比：${formatPercent(datum.optimized)}`,
              `变化量：${formatPct(datum.optimized - datum.baseline)}`,
            ].join('<br/>');
          }

          const isBaseline = currentMode.value === 'baseline';
          const currentValue = isBaseline ? datum.baseline : datum.optimized;
          const currentCount = isBaseline
            ? datum.baselineCount
            : datum.optimizedCount;
          return [
            `幅值区间：${amplitudeBin}`,
            `均值区间：${meanBin}`,
            `模式：${isBaseline ? '基线' : '优化'}`,
            `当前占比：${formatPercent(currentValue)}`,
            `样本循环数：${currentCount ?? '-'}`,
          ].join('<br/>');
        },
      },
      xAxis: {
        type: 'category',
        data: meanBins,
        axisLabel: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        axisLine: {
          lineStyle: {
            color: themeTokens.text4,
          },
        },
        axisTick: { show: false },
        splitArea: { show: false },
      },
      yAxis: {
        type: 'category',
        data: amplitudeBins,
        name: '循环幅值区间',
        nameLocation: 'middle',
        nameGap: 58,
        axisLabel: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        nameTextStyle: {
          color: themeTokens.text3,
          align: 'center',
          verticalAlign: 'middle',
          padding: [0, 0, 0, -6],
        },
        axisLine: {
          lineStyle: {
            color: themeTokens.text4,
          },
        },
        axisTick: { show: false },
      },
      visualMap: {
        show: props.showVisualMap,
        orient: 'vertical',
        right: 6,
        top: 'middle',
        itemHeight: 120,
        itemWidth: 8,
        textStyle: {
          color: themeTokens.text3,
          fontSize: 10,
        },
        calculable: false,
        ...visualMapPieces,
      },
      series: [
        {
          type: 'heatmap',
          data: heatmapData,
          progressive: 0,
          emphasis: {
            itemStyle: {
              borderColor: themeTokens.text1,
              borderWidth: 1,
            },
          },
          itemStyle: {
            borderColor: themeTokens.fill3,
            borderWidth: 1,
          },
          label: {
            show: props.showCellLabel,
            fontSize: 10,
            color: themeTokens.text3,
            formatter(params: any) {
              const datum = params.data as HeatmapDatum;
              if (currentMode.value === 'difference') {
                return formatPercent(datum.optimized - datum.baseline, true);
              }
              return formatPercent(datum.value[2]);
            },
          },
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .load-cycle-migration-chart {
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .chart-head {
    position: relative;
    display: flex;
    align-items: flex-start;
    justify-content: flex-start;
    gap: 12px;
    margin-bottom: 6px;
  }

  .chart-copy {
    min-width: 0;
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

  .chart-mode-switch {
    position: absolute;
    left: 50%;
    top: 0;
    transform: translateX(-50%);

    :deep(.arco-radio-group) {
      gap: 8px;
    }

    :deep(.arco-radio) {
      margin-right: 0;
    }

    :deep(.arco-radio-label) {
      color: var(--color-text-3);
      font-size: 11px;
      line-height: 1.3;
      transition: color 0.2s ease;
    }

    :deep(.arco-radio-checked .arco-radio-label) {
      color: var(--color-text-2);
    }

    :deep(.arco-radio-icon-hover::before) {
      background-color: transparent;
    }

    :deep(.arco-radio-mask) {
      border-color: var(--color-text-4);
      background-color: transparent;
    }

    :deep(.arco-radio-checked .arco-radio-mask) {
      border-color: rgb(var(--primary-6));
      background-color: rgb(var(--primary-6));
    }

    :deep(.arco-radio-checked .arco-radio-mask::after) {
      background-color: var(--color-white);
    }
  }

  .chart-stage {
    flex: 1;
    min-height: 0;
    position: relative;
  }

  .chart-body {
    position: absolute;
    inset: 0;
  }

  .chart-x-axis-label {
    position: absolute;
    left: 58px;
    bottom: 2px;
    font-size: 11px;
    line-height: 1;
    pointer-events: none;
  }
</style>
