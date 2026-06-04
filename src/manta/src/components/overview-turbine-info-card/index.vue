<template>
  <a-card class="overview-turbine-info-card" :bordered="false">
    <a-spin v-if="loading" class="overview-turbine-info-card__loading" />
    <div v-else class="overview-turbine-info-card__list">
      <div v-for="item in items" :key="item.label" class="meta-line">
        <span class="label">{{ item.label }}</span>
        <span>{{ item.value }}</span>
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
  withDefaults(
    defineProps<{
      items: Array<{
        label: string;
        value: string;
      }>;
      loading?: boolean;
    }>(),
    {
      loading: false,
    },
  );
</script>

<style scoped lang="less">
  .overview-turbine-info-card {
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

  .overview-turbine-info-card :deep(.arco-card-body) {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .overview-turbine-info-card__list {
    width: fit-content;
    max-width: 100%;
    margin: 0 auto;
    min-width: 0;
    display: grid;
    gap: 8px;
    font-size: 12px;
    line-height: 1.25;
    justify-content: center;
    justify-items: start;
  }

  .overview-turbine-info-card__loading {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
  }
  .meta-line {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 6px;
    min-height: 0;
    color: var(--color-text-2);
    text-align: left;
  }

  .meta-line .label {
    flex: 0 0 auto;
    text-align: left;
    padding-right: 0;
    color: var(--color-text-3);
  }

  .meta-line span:last-child {
    flex: 0 0 auto;
    text-align: left;
    font-variant-numeric: tabular-nums;
  }
</style>
