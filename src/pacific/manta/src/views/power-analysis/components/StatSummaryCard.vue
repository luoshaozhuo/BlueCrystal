<template>
  <OverviewMetricCard
    :title="title"
    :value="value"
    :unit="unit"
    :footnote="subtitle"
    :trend-symbol="trendSymbol"
    :tone="tone"
    :compact-value="compactValue"
    :loading="loading"
  />
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import OverviewMetricCard from '@/components/overview-metric-card/index.vue';

  const props = withDefaults(
    defineProps<{
      title: string;
      value: string;
      unit?: string;
      subtitle?: string;
      trend?: 'up' | 'down' | 'neutral';
      compactValue?: boolean;
      loading?: boolean;
    }>(),
    {
      unit: '',
      subtitle: '',
      trend: 'neutral',
      compactValue: false,
      loading: false,
    },
  );

  const trendSymbol = computed(() => {
    if (props.trend === 'up') return '↑';
    if (props.trend === 'down') return '↓';
    return '';
  });

  const tone = computed(() => {
    if (props.trend === 'up') return 'positive';
    if (props.trend === 'down') return 'negative';
    return 'neutral';
  });
</script>
