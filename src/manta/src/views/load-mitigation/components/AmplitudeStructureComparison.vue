<template>
  <div class="amplitude-structure-chart">
    <div class="chart-head">
      <div class="chart-title">循环幅值结构对比</div>
      <div class="chart-subtitle">对比优化前后各幅值区间的占比变化</div>
    </div>
    <div class="chart-stage">
      <VChart class="chart-body" :option="chartOption" autoresize />
      <div v-if="normalizedData" class="chart-center-axis">
        <div
          v-for="row in normalizedData.meanBins"
          :key="row"
          class="chart-center-axis-label"
          :style="{ color: themeTokens.text3 }"
        >
          {{ row }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import type { ComposeOption } from 'echarts/core';
  import { use } from 'echarts/core';
  import { BarChart } from 'echarts/charts';
  import type { BarSeriesOption } from 'echarts/charts';
  import {
    GraphicComponent,
    GridComponent,
    LegendComponent,
    TooltipComponent,
    type GraphicComponentOption,
    type GridComponentOption,
    type LegendComponentOption,
    type TooltipComponentOption,
  } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
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

  interface NormalizedRow {
    meanBin: string;
    baseline: number[];
    optimized: number[];
  }

  interface RowSeriesDatum {
    value: number;
    rowIndex: number;
    rowLabel: string;
    amplitudeBin: string;
    baselineValue: number;
    optimizedValue: number;
  }

  const props = defineProps<{
    data?: AmplitudeStructureComparisonData | null;
  }>();
  const themeTokens = useThemeTokens();

  const amplitudeOrder = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60'];
  const amplitudePalette = [
    '#9FD3FF',
    '#4C7DFF',
    '#16C7C8',
    '#F4C84E',
    '#F28B39',
    '#DE4C4C',
  ];
  const axisTickValues = [0, 0.25, 0.5, 0.75, 1];

  function normalizeValues(values: number[]) {
    const safeValues = values.map((value) => Math.max(value, 0));
    const total = safeValues.reduce((sum, value) => sum + value, 0);
    if (!total) {
      return safeValues.map(() => 0);
    }
    return safeValues.map((value) => Number((value / total).toFixed(6)));
  }

  function buildRowMap(rows: MeanBinDistribution[]) {
    return new Map(rows.map((row) => [row.meanBin, row.values]));
  }

  function reorderRowValues(
    rowValues: number[] | undefined,
    sourceBins: string[],
    targetBins: string[],
  ) {
    return targetBins.map((bin) => {
      const sourceIndex = sourceBins.indexOf(bin);
      if (sourceIndex === -1 || !rowValues) return 0;
      return Number(rowValues[sourceIndex] ?? 0);
    });
  }

  const normalizedData = computed(() => {
    const source = props.data;
    if (!source) {
      return null;
    }
    const meanBins = Array.isArray(source.meanBins) ? source.meanBins : [];
    const sourceAmplitudeBins = Array.isArray(source.amplitudeBins)
      ? source.amplitudeBins
      : [];

    if (!meanBins.length || !sourceAmplitudeBins.length) {
      return null;
    }

    const baselineMap = buildRowMap(
      Array.isArray(source.baseline) ? source.baseline : [],
    );
    const optimizedMap = buildRowMap(
      Array.isArray(source.optimized) ? source.optimized : [],
    );

    const rows: NormalizedRow[] = meanBins.map((meanBin) => {
      const baselineValues = reorderRowValues(
        baselineMap.get(meanBin),
        sourceAmplitudeBins,
        amplitudeOrder,
      );
      const optimizedValues = reorderRowValues(
        optimizedMap.get(meanBin),
        sourceAmplitudeBins,
        amplitudeOrder,
      );

      return {
        meanBin,
        baseline: normalizeValues(baselineValues),
        optimized: normalizeValues(optimizedValues),
      };
    });

    return {
      meanBins,
      amplitudeBins: amplitudeOrder,
      rows,
    };
  });

  function formatPct(value: number) {
    return `${(value * 100).toFixed(1)}%`;
  }

  function formatPctPoint(value: number) {
    const sign = value > 0 ? '+' : '';
    return `${sign}${(value * 100).toFixed(1)} pct`;
  }

  function getSeriesId(side: 'baseline' | 'optimized', amplitudeBin: string) {
    return `${side}-${amplitudeBin}`;
  }

  const chartOption = computed<ECOption>(() => {
    const source = normalizedData.value;
    if (!source) {
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

    const { meanBins, amplitudeBins, rows } = source;
    const series: BarSeriesOption[] = [];

    amplitudeBins.forEach((bin, index) => {
      const baselineData: RowSeriesDatum[] = rows.map((row, rowIndex) => ({
        value: -row.baseline[index],
        rowIndex,
        rowLabel: row.meanBin,
        amplitudeBin: bin,
        baselineValue: row.baseline[index],
        optimizedValue: row.optimized[index],
      }));
      const optimizedData: RowSeriesDatum[] = rows.map((row, rowIndex) => ({
        value: row.optimized[index],
        rowIndex,
        rowLabel: row.meanBin,
        amplitudeBin: bin,
        baselineValue: row.baseline[index],
        optimizedValue: row.optimized[index],
      }));

      series.push({
        name: bin,
        id: getSeriesId('baseline', bin),
        type: 'bar',
        stack: 'baseline',
        xAxisIndex: 0,
        yAxisIndex: 0,
        barWidth: 22,
        legendHoverLink: true,
        itemStyle: {
          color: amplitudePalette[index],
          opacity: 0.96,
        },
        emphasis: {
          focus: 'self',
          itemStyle: {
            opacity: 1,
          },
        },
        data: baselineData,
      });

      series.push({
        name: bin,
        id: getSeriesId('optimized', bin),
        type: 'bar',
        stack: 'optimized',
        xAxisIndex: 1,
        yAxisIndex: 1,
        barWidth: 22,
        legendHoverLink: true,
        itemStyle: {
          color: amplitudePalette[index],
          opacity: 0.96,
        },
        emphasis: {
          focus: 'self',
          itemStyle: {
            opacity: 1,
          },
        },
        data: optimizedData,
      });
    });

    return {
      animationDuration: 350,
      color: amplitudePalette,
      legend: {
        top: 0,
        left: 'center',
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 14,
        textStyle: {
          color: themeTokens.text3,
          fontSize: 11,
        },
        data: amplitudeBins,
      },
      tooltip: {
        trigger: 'item',
        confine: true,
        position(point, _params, _dom, _rect, size) {
          const [mouseX, mouseY] = point as number[];
          const { contentSize, viewSize } = size;
          const offsetX = 20;
          const offsetY = 20;

          let left = mouseX + offsetX;
          let top = mouseY - contentSize[1] - offsetY;

          if (left + contentSize[0] > viewSize[0] - 8) {
            left = mouseX - contentSize[0] - offsetX;
          }

          if (top < 8) {
            top = mouseY + offsetY;
          }

          return [left, top];
        },
        backgroundColor: themeTokens.tooltipBg,
        borderColor: themeTokens.tooltipBorder,
        textStyle: themeTokens.tooltipTextStyle,
        formatter(params: any) {
          const datum = params.data as RowSeriesDatum;
          const baselineValue = datum?.baselineValue ?? 0;
          const optimizedValue = datum?.optimizedValue ?? 0;
          const diff = optimizedValue - baselineValue;

          return [
            `均值区间：${datum?.rowLabel ?? '-'}`,
            `幅值区间：${datum?.amplitudeBin ?? params.seriesName}`,
            `优化前占比：${formatPct(baselineValue)}`,
            `优化后占比：${formatPct(optimizedValue)}`,
            `变化量：${formatPctPoint(diff)}`,
          ].join('<br/>');
        },
      },
      grid: [
        { left: 12, right: '56%', top: 84, bottom: 24, containLabel: false },
        { left: '56%', right: 12, top: 84, bottom: 24, containLabel: false },
      ],
      graphic: [
        {
          type: 'text',
          top: 40,
          left: '21%',
          style: {
            text: '优化前',
            fill: themeTokens.text3,
            fontSize: 11,
            fontWeight: 600,
            textAlign: 'center',
          },
        },
        {
          type: 'text',
          top: 40,
          right: '21%',
          style: {
            text: '优化后',
            fill: themeTokens.text3,
            fontSize: 11,
            fontWeight: 600,
            textAlign: 'center',
          },
        },
      ],
      xAxis: [
        {
          type: 'value',
          gridIndex: 0,
          min: -1,
          max: 0,
          interval: 0.25,
          splitNumber: 4,
          axisLabel: {
            color: themeTokens.text3,
            formatter(value: number) {
              return `${Math.abs(value * 100).toFixed(0)}%`;
            },
          },
          nameTextStyle: {
            color: themeTokens.text3,
          },
          axisLine: {
            lineStyle: {
              color: themeTokens.text4,
            },
          },
          axisTick: {
            show: false,
            alignWithLabel: true,
          },
          splitLine: {
            show: false,
          },
          axisPointer: {
            show: false,
          },
          data: axisTickValues,
        },
        {
          type: 'value',
          gridIndex: 1,
          min: 0,
          max: 1,
          interval: 0.25,
          splitNumber: 4,
          axisLabel: {
            color: themeTokens.text3,
            formatter(value: number) {
              return `${(value * 100).toFixed(0)}%`;
            },
          },
          nameTextStyle: {
            color: themeTokens.text3,
          },
          axisLine: {
            lineStyle: {
              color: themeTokens.text4,
            },
          },
          axisTick: {
            show: false,
            alignWithLabel: true,
          },
          splitLine: {
            show: false,
          },
          axisPointer: {
            show: false,
          },
          data: axisTickValues,
        },
      ],
      yAxis: [
        {
          type: 'category',
          gridIndex: 0,
          inverse: true,
          data: meanBins,
          position: 'right',
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        {
          type: 'category',
          gridIndex: 1,
          inverse: true,
          data: meanBins,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
        },
      ],
      series,
    };
  });
</script>

<style scoped lang="less">
  .amplitude-structure-chart {
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
    position: absolute;
    inset: 0;
  }

  .chart-stage {
    flex: 1;
    min-height: 0;
    position: relative;
  }

  .chart-center-axis {
    position: absolute;
    top: 84px;
    bottom: 24px;
    left: 50%;
    width: 92px;
    transform: translateX(-50%);
    display: grid;
    grid-template-rows: repeat(6, minmax(0, 1fr));
    pointer-events: none;
  }

  .chart-center-axis-label {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    line-height: 1;
  }
</style>
