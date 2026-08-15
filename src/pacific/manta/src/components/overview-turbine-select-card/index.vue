<template>
  <a-card class="overview-turbine-select-card" :bordered="false">
    <a-spin v-if="loading" class="overview-turbine-select-card__loading" />
    <div v-else class="overview-turbine-select-card__content">
      <div class="overview-turbine-select-card__label">{{ label }}</div>
      <a-select
        :model-value="modelValue"
        class="overview-turbine-select-card__select"
        :options="options"
        :placeholder="placeholder"
        size="large"
        @update:model-value="handleUpdate"
      />
    </div>
  </a-card>
</template>

<script setup lang="ts">
  withDefaults(
    defineProps<{
      modelValue: string;
      options: Array<{ label: string; value: string }>;
      label?: string;
      placeholder?: string;
      loading?: boolean;
    }>(),
    {
      label: '机组编号',
      placeholder: '选择机组',
      loading: false,
    },
  );

  const emit = defineEmits<{
    (event: 'update:modelValue', value: string): void;
  }>();

  function handleUpdate(value: string | number | Record<string, unknown> | undefined) {
    emit('update:modelValue', String(value ?? ''));
  }
</script>

<style scoped lang="less">
  .overview-turbine-select-card {
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

  .overview-turbine-select-card :deep(.arco-card-body) {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .overview-turbine-select-card__content {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    min-width: 0;
  }

  .overview-turbine-select-card__loading {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
  }
  .overview-turbine-select-card__label {
    font-size: 12px;
    line-height: 1.25;
    color: var(--color-text-3);
  }

  :deep(.overview-turbine-select-card__select .arco-select-view) {
    display: flex;
    align-items: center;
    justify-content: center;
    height: auto;
    padding: 0;
    border: 0;
    background: transparent;
    box-shadow: none;
  }

  :deep(.overview-turbine-select-card__select .arco-select-view-value) {
    width: 100%;
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: 0.04em;
    font-variant-numeric: tabular-nums;
    color: var(--color-text-1);
  }

  :deep(.overview-turbine-select-card__select .arco-select-view-suffix) {
    display: none;
  }
</style>
