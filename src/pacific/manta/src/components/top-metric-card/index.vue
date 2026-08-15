<template>
  <a-card class="top-metric-card" :bordered="false" :loading="loading">
    <div class="top-metric-card__content">
      <div class="top-metric-card__title">{{ label }}</div>
      <div v-if="isStatusMetric" class="top-metric-card__status" :class="statusClass">
        <span class="top-metric-card__dot" />
        <span>{{ value }}</span>
      </div>
      <div v-else class="top-metric-card__value" :class="statusClass">
        <span class="top-metric-card__number" :class="{ 'top-metric-card__number--theme': valueUseThemeColor }">
          {{ formattedValue }}
        </span>
        <span
          v-if="unit && unit !== '-'"
          class="top-metric-card__unit"
          :class="{ 'top-metric-card__unit--theme': valueUseThemeColor }"
        >
          {{ unit }}
        </span>
      </div>
      <div
        v-if="showTrend"
        class="top-metric-card__trend"
        :class="trendClass"
      >
        {{ Number(trend) > 0 ? '+' : '' }}{{ Number(trend).toFixed(trendDigits) }}
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue';

  const props = defineProps<{
    label: string;
    value: number | string;
    unit?: string;
    status?: 'normal' | 'warning' | 'offline';
    trend?: number;
    precision?: number;
    loading?: boolean;
    valueUseThemeColor?: boolean;
    reverseTrendColor?: boolean;
  }>();

  const isStatusMetric = computed(() => typeof props.value === 'string');
  const formattedValue = computed(() => {
    if (typeof props.value === 'string') return props.value;
    const digits = props.precision ?? 0;
    return props.value.toFixed(digits);
  });
  const showTrend = computed(() => typeof props.trend === 'number');
  const trendDigits = computed(() => (Math.abs(Number(props.trend ?? 0)) >= 1 ? 1 : 2));
  const statusClass = computed(() => `is-${props.status ?? 'normal'}`);
  const trendClass = computed(() => {
    const isNegative = Number(props.trend) < 0;
    if (props.reverseTrendColor) {
      return { 'is-negative': !isNegative, 'is-positive': isNegative };
    }
    return { 'is-negative': isNegative, 'is-positive': false };
  });
</script>

<style scoped lang="less">
  .top-metric-card {
    width: 100%;
    height: 100%;
    min-width: 0;
    padding: 6px;
    box-sizing: border-box;
  }

  .top-metric-card :deep(.arco-card-body) {
    width: 100%;
    height: 100%;
    padding: 6px 8px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .top-metric-card__content {
    width: 100%;
    text-align: center;
  }

  .top-metric-card__title {
    font-size: 11px;
    line-height: 1.1;
    color: var(--color-text-3);
  }

  .top-metric-card__value,
  .top-metric-card__status {
    margin-top: 6px;
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 4px;
    font-size: 18px;
    line-height: 1.1;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .top-metric-card__status {
    align-items: center;
    font-size: 16px;
  }

  .top-metric-card__unit {
    font-size: 11px;
    font-weight: 600;
  }

  .top-metric-card__unit--theme {
    color: rgb(var(--primary-6));
  }

  .top-metric-card__number--theme {
    color: rgb(var(--primary-6));
  }

  .top-metric-card__trend {
    margin-top: 4px;
    font-size: 10px;
    line-height: 1;
    color: var(--color-success-light-4);
  }

  .top-metric-card__trend.is-negative {
    color: var(--color-danger-light-4);
  }

  .top-metric-card__trend.is-positive {
    color: var(--color-success-light-4);
  }

  .top-metric-card__dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 8px currentColor;
  }

  .is-normal {
    color: var(--color-success-light-4);
  }

  .is-warning {
    color: var(--color-warning-light-4);
  }

  .is-offline {
    color: var(--color-danger-light-4);
  }
</style>
