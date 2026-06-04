<template>
  <div class="wind-rose-stats">
    <VChart class="chart" :option="roseOption" autoresize />
    <VChart class="chart" :option="tiOption" autoresize />
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue';
  import { use } from 'echarts/core';
  import type { EChartsOption } from 'echarts';
  import { CanvasRenderer } from 'echarts/renderers';
  import { BarChart, LineChart } from 'echarts/charts';
  import {
    GridComponent,
    PolarComponent,
    TooltipComponent,
    AxisPointerComponent,
    LegendComponent,
    TitleComponent,
  } from 'echarts/components';
  import VChart from 'vue-echarts';
  import { useChartTheme } from '@/config/chart-theme';
  import type { WindRoseTiStats as WindRoseTiStatsData } from '@/types/lidar';

  use([
    CanvasRenderer,
    BarChart,
    LineChart,
    GridComponent,
    PolarComponent,
    TooltipComponent,
    AxisPointerComponent,
    LegendComponent,
    TitleComponent,
  ]);

  const props = defineProps<{
    data: WindRoseTiStatsData;
  }>();

  const chartTheme = useChartTheme();

  const roseOption = computed<EChartsOption>(() => {
    const sectors = props.data.sectors ?? [];

    if (!sectors.length) {
      return {};
    }

    return {
      color: [chartTheme.value.primary],
      title: {
        text: '风向玫瑰',
        left: 'center',
        top: 2,
        textStyle: {
          color: chartTheme.value.textMuted,
          fontSize: 11,
          fontWeight: 400,
        },
      },
      tooltip: {
        trigger: 'item',
        confine: true,
        backgroundColor: chartTheme.value.tooltipBg,
        borderColor: chartTheme.value.tooltipBorder,
        textStyle: chartTheme.value.tooltipTextStyle,
        formatter(params: any) {
          const item = sectors[params.dataIndex];
          if (!item) return '';
          return [
            `风向：${item.direction}`,
            `频率：${item.frequency.toFixed(1)}%`,
            `湍流度：${item.ti.toFixed(3)}`,
            `平均风速：${item.meanWindSpeed.toFixed(2)} m/s`,
          ].join('<br/>');
        },
      },
      polar: {
        center: ['50%', '56%'],
        radius: '68%',
      },
      angleAxis: {
        type: 'category',
        data: sectors.map((item) => item.direction),
        axisLine: {
          lineStyle: {
          color: chartTheme.value.axisLine,
          },
        },
        axisTick: {
          show: false,
        },
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 10,
        },
      },
      radiusAxis: {
        type: 'value',
        min: 0,
        splitNumber: 4,
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 10,
        },
        axisLine: {
          show: false,
        },
        splitLine: {
          lineStyle: {
            color: chartTheme.value.splitLine,
          },
        },
      },
      series: [
        {
          type: 'bar',
          coordinateSystem: 'polar',
          roundCap: true,
          data: sectors.map((item) => item.frequency),
        },
      ],
    };
  });

  const tiOption = computed<EChartsOption>(() => {
    const sectors = props.data.sectors ?? [];

    if (!sectors.length) {
      return {};
    }

    return {
      color: [chartTheme.value.primary, chartTheme.value.warning],
      title: {
        text: '湍流度 / 平均风速',
        left: 'center',
        top: 2,
        textStyle: {
          color: chartTheme.value.textMuted,
          fontSize: 11,
          fontWeight: 400,
        },
      },
      legend: {
        top: 32,
        left: 'center',
        itemWidth: 10,
        itemHeight: 10,
        textStyle: {
          color: chartTheme.value.textMuted,
          fontSize: 10,
        },
      },
      grid: {
        left: 32,
        right: 30,
        top: 62,
        bottom: 24,
        containLabel: true,
      },
      tooltip: {
        trigger: 'axis',
        confine: true,
        backgroundColor: chartTheme.value.tooltipBg,
        borderColor: chartTheme.value.tooltipBorder,
        textStyle: chartTheme.value.tooltipTextStyle,
        axisPointer: {
          type: 'line',
        },
      },
      xAxis: {
        type: 'category',
        data: sectors.map((item) => item.direction),
        axisLine: {
          lineStyle: {
            color: chartTheme.value.axisLine,
          },
        },
        axisTick: {
          show: false,
        },
        axisLabel: {
          color: chartTheme.value.textMuted,
          fontSize: 10,
          interval: 1,
        },
      },
      yAxis: [
        {
          type: 'value',
          name: 'TI',
          nameLocation: 'middle',
          nameGap: 30,
          axisLabel: {
            color: chartTheme.value.textMuted,
            fontSize: 10,
          },
          nameTextStyle: {
            color: chartTheme.value.textMuted,
            fontSize: 10,
          },
          axisLine: {
            show: false,
          },
          splitLine: {
            lineStyle: {
              color: chartTheme.value.splitLine,
            },
          },
        },
        {
          type: 'value',
          name: 'm/s',
          nameLocation: 'middle',
          nameGap: 30,
          axisLabel: {
            color: chartTheme.value.textMuted,
            fontSize: 10,
          },
          nameTextStyle: {
            color: chartTheme.value.textMuted,
            fontSize: 10,
          },
          axisLine: {
            show: false,
          },
          splitLine: {
            show: false,
          },
        },
      ],
      series: [
        {
          name: '湍流度',
          type: 'bar',
          data: sectors.map((item) => item.ti),
        },
        {
          name: '平均风速',
          type: 'line',
          yAxisIndex: 1,
          data: sectors.map((item) => item.meanWindSpeed),
          showSymbol: false,
        },
      ],
    };
  });
</script>

<style scoped lang="less">
  .wind-rose-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .chart {
    width: 100%;
    height: 100%;
    min-height: 0;
  }
</style>
