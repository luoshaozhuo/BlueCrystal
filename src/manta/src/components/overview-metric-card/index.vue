<template>
  <a-card class="overview-metric-card" :bordered="false">
    <a-spin v-if="loading" class="overview-metric-card__loading" />
    <div v-else class="overview-metric-card__content">
      <div class="overview-metric-card__title">{{ title }}</div>
      <div
        class="overview-metric-card__value"
        :class="[toneClass, { 'overview-metric-card__value--compact': compactValue }]"
      >
        <span
          v-if="trendSymbol"
          class="overview-metric-card__trend"
          :class="toneClass"
        >
          {{ trendSymbol }}
        </span>
        <span>{{ value }}</span>
        <span
          v-if="unit"
          class="overview-metric-card__unit"
          :class="{ 'overview-metric-card__unit--compact': compactValue }"
        >
          {{ unit }}
        </span>
      </div>
      <div v-if="footnote" class="overview-metric-card__footnote">
        {{ footnote }}
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue';

  const props = withDefaults(
    defineProps<{
      title: string;
      value: string;
      unit?: string;
      footnote?: string;
      trendSymbol?: string;
      tone?: 'positive' | 'negative' | 'neutral';
      compactValue?: boolean;
      loading?: boolean;
    }>(),
    {
      unit: '',
      footnote: '',
      trendSymbol: '',
      tone: 'neutral',
      compactValue: false,
      loading: false,
    },
  );

  const toneClass = computed(() => `is-${props.tone}`);
</script>

<style scoped lang="less">
  .overview-metric-card {
    min-width: 0;
    width: 100%;
    height: 100%;
    padding: 6px;
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .overview-metric-card :deep(.arco-card-body) {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .overview-metric-card__content {
    width: 100%;
    text-align: center;
    min-width: 0;
  }

  .overview-metric-card__loading {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
  }
  .overview-metric-card__title {
    font-size: 12px;
    line-height: 1.25;
    color: var(--color-text-2);
  }

  .overview-metric-card__value {
    margin-top: 6px;
    font-size: 18px;
    line-height: 1.2;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--color-text-1);
  }

  .overview-metric-card__value--compact {
    font-size: 15px;
  }

  .overview-metric-card__trend {
    margin-right: 4px;
  }

  .overview-metric-card__unit {
    margin-left: 4px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
  }

  .overview-metric-card__unit--compact {
    font-size: 11px;
  }

  .overview-metric-card__value.is-negative,
  .overview-metric-card__trend.is-negative {
    color: var(--color-success-light-4);
  }

  .overview-metric-card__value.is-positive,
  .overview-metric-card__trend.is-positive {
    color: var(--color-danger-light-4);
  }

  .overview-metric-card__value.is-neutral,
  .overview-metric-card__trend.is-neutral {
    color: rgb(var(--primary-6));
  }

  .overview-metric-card__footnote {
    margin-top: 4px;
    font-size: 11px;
    line-height: 1.3;
    color: var(--color-text-3);
  }
</style>
