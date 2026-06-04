<template>
  <div class="storage-panel">
    <a-card class="storage-panel__card" :bordered="false">
      <div class="storage-panel__plot">
        <div class="storage-panel__chart-slot">
          <VChart class="storage-panel__chart" :option="partitionUsageOption" autoresize />
        </div>
        <div class="storage-panel__chart-slot">
          <VChart class="storage-panel__chart" :option="growthTrendOption" autoresize />
        </div>
      </div>
    </a-card>
    <a-card class="storage-panel__card storage-panel__card--side" :bordered="false">
      <div class="storage-panel__side">
        <div class="storage-panel__side-chart">
          <VChart class="storage-panel__chart" :option="remainingOption" autoresize />
        </div>
        <div class="storage-panel__side-info">
          <div class="storage-panel__side-label">预计还能使用</div>
          <div class="storage-panel__side-days">{{ supportDays.toFixed(0) }} 天</div>
          <div class="storage-panel__side-text">按最近30天平均增量估算</div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { ComposeOption } from 'echarts/core';
  import { BarChart, LineChart, PieChart } from 'echarts/charts';
  import type { BarSeriesOption, LineSeriesOption, PieSeriesOption } from 'echarts/charts';
  import { GraphicComponent, GridComponent, TitleComponent, TooltipComponent, type GraphicComponentOption, type GridComponentOption, type TitleComponentOption, type TooltipComponentOption } from 'echarts/components';
  import { CanvasRenderer } from 'echarts/renderers';
  import VChart from 'vue-echarts';
  import { CHART_SERIES_COLORS, useChartTheme, withAlpha } from '@/config/chart-theme';
  import type { StoragePartitionKey, StorageResourceData } from '@/mock/data-acquisition';

  use([CanvasRenderer, BarChart, LineChart, PieChart, GraphicComponent, GridComponent, TitleComponent, TooltipComponent]);

  type ECOption = ComposeOption<BarSeriesOption | LineSeriesOption | PieSeriesOption | GraphicComponentOption | GridComponentOption | TitleComponentOption | TooltipComponentOption>;

  const props = defineProps<{ data: StorageResourceData }>();
  const chartTheme = useChartTheme();
  const partitionLabels: Record<StoragePartitionKey, string> = {
    scadaRaw: 'SCADA原始库',
    lidarTimeseries: 'Lidar时序库',
    analysisResult: '分析结果库',
    archive: '归档区',
  };
  const growthLineColor = computed(() => chartTheme.value.success);
  const totalCapacity = computed(() => props.data.partitions.reduce((sum, item) => sum + item.total, 0));
  const totalUsed = computed(() => props.data.partitions.reduce((sum, item) => sum + item.used, 0));
  const growthValues = computed(() => props.data.growthTrend30d.map((item) => item.value));
  const avgGrowth = computed(() => growthValues.value.reduce((sum, item) => sum + item, 0) / Math.max(growthValues.value.length, 1));
  const supportDays = computed(() => (props.data.remainingSpace * 1024) / Math.max(avgGrowth.value, 1));
  const growthAxisMin = computed(() => {
    const min = Math.min(...growthValues.value);
    return Math.floor(min / 10) * 10;
  });
  const growthAxisMax = computed(() => {
    const max = Math.max(...growthValues.value);
    return Math.ceil(max / 10) * 10;
  });
  const growthAxisInterval = computed(() => {
    const span = Math.max(growthAxisMax.value - growthAxisMin.value, 4);
    return Math.max(1, Math.ceil(span / 4));
  });
  const remainingOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '剩余容量',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
      formatter: '{b}<br/>{c} TB ({d}%)',
    },
    series: [
      {
        type: 'pie',
        radius: ['52%', '72%'],
        center: ['50%', '58%'],
        label: { show: false },
        labelLine: { show: false },
        data: [
          { name: '剩余容量', value: Number(props.data.remainingSpace.toFixed(1)), itemStyle: { color: chartTheme.value.success } },
          { name: '已使用容量', value: Number(totalUsed.value.toFixed(1)), itemStyle: { color: withAlpha(chartTheme.value.axisLine, 0.22) } },
        ],
      },
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '51%',
        style: {
          text: `${props.data.remainingSpace.toFixed(1)} TB`,
          fill: chartTheme.value.textStrong,
          fontSize: 14,
          fontWeight: 700,
          textAlign: 'center',
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '63%',
        style: {
          text: `总容量 ${totalCapacity.value.toFixed(1)} TB`,
          fill: chartTheme.value.textMuted,
          fontSize: 10,
          textAlign: 'center',
        },
      },
    ],
  }));

  const partitionUsageOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '各分区已使用容量',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    grid: {
      left: 48,
      right: 16,
      top: 30,
      bottom: 34,
      containLabel: false,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'value',
      name: '容量(TB)',
      nameLocation: 'middle',
      nameGap: 24,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category',
      data: props.data.partitions.map((item) => partitionLabels[item.key]),
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        data: props.data.partitions.map((item, index) => ({
          value: item.used,
          itemStyle: {
            color: CHART_SERIES_COLORS[index] ?? CHART_SERIES_COLORS[0],
          },
        })),
      },
    ],
  }));

  const growthTrendOption = computed<ECOption>(() => ({
    animationDuration: 260,
    title: {
      text: '总容量增长趋势',
      left: 'center',
      top: 4,
      textStyle: {
        color: chartTheme.value.textMain,
        fontSize: 11,
        fontWeight: 500,
      },
    },
    grid: {
      left: 48,
      right: 16,
      top: 30,
      bottom: 34,
      containLabel: false,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartTheme.value.tooltipBg,
      borderColor: chartTheme.value.tooltipBorder,
      textStyle: chartTheme.value.tooltipTextStyle,
    },
    xAxis: {
      type: 'category',
      data: props.data.growthTrend30d.map((item) => item.date),
      name: '日期',
      nameLocation: 'middle',
      nameGap: 24,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10, interval: 4 },
      axisLine: { lineStyle: { color: chartTheme.value.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '增量(GB)',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { color: chartTheme.value.textMuted, fontSize: 10 },
      min: growthAxisMin.value,
      max: growthAxisMin.value + growthAxisInterval.value * 4,
      interval: growthAxisInterval.value,
      axisLabel: { color: chartTheme.value.textMuted, fontSize: 10 },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: chartTheme.value.splitLine } },
    },
    series: [
      {
        type: 'line',
        color: growthLineColor.value,
        data: props.data.growthTrend30d.map((item) => item.value),
        smooth: true,
        symbolSize: 5,
        lineStyle: { width: 2, color: growthLineColor.value },
        itemStyle: { color: growthLineColor.value },
        areaStyle: { color: growthLineColor.value, opacity: 0.18 },
        emphasis: {
          disabled: true,
          areaStyle: { color: growthLineColor.value, opacity: 0.18 },
        },
      },
    ],
  }));
</script>

<style scoped lang="less">
  .storage-panel {
    display: flex;
    gap: 8px;
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .storage-panel__card {
    flex: 1 1 auto;
    display: flex;
    min-width: 0;
    min-height: 0;
  }

  .storage-panel__card :deep(.arco-card-body) {
    width: 100%;
    height: 100%;
    min-height: 0;
    padding: 0;
  }

  .storage-panel__card--side {
    flex: 0 0 196px;
  }

  .storage-panel__side {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    min-height: 0;
  }

  .storage-panel__side-chart {
    flex: 0 0 58%;
    min-height: 0;
  }

  .storage-panel__side-info {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: 0;
    padding: 4px 12px 12px;
    text-align: center;
  }

  .storage-panel__side-label {
    color: var(--color-text-3);
    font-size: 10px;
    line-height: 1.2;
  }

  .storage-panel__side-days {
    color: var(--color-text-1);
    font-size: 22px;
    font-weight: 700;
    line-height: 1;
  }

  .storage-panel__side-text {
    color: var(--color-text-3);
    font-size: 10px;
    line-height: 1.3;
  }

  .storage-panel__plot {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    gap: 8px;
    min-height: 0;
  }

  .storage-panel__chart {
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .storage-panel__chart-slot {
    flex: 1 1 0;
    min-width: 0;
    min-height: 0;
  }

</style>
