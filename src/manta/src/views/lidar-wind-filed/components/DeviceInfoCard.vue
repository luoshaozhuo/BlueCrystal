<template>
  <a-card class="device-info-card" :bordered="false" :loading="loading">
    <div class="device-info-grid">
      <div v-for="item in infoItems" :key="item.label" class="device-info-item">
        <span class="device-info-label">{{ item.label }}</span>
        <span class="device-info-value">{{ item.value }}</span>
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import type { LidarDeviceInfo } from '@/types/lidar';

  const props = defineProps<{
    data: LidarDeviceInfo | null;
    loading?: boolean;
  }>();

  const infoItems = computed(() => {
    if (!props.data) return [];
    return [
      { label: '设备型号', value: props.data.deviceModel },
      { label: '设备编号', value: props.data.deviceId },
      { label: '扫描模式', value: props.data.scanMode },
      { label: '扫描层数', value: `${props.data.scanLayers}` },
      { label: '扫描角范围', value: props.data.scanAngleRange },
      { label: '采样频率', value: `${props.data.sampleFrequencyHz} Hz` },
    ];
  });
</script>

<style scoped lang="less">
  .device-info-card {
    width: 100%;
    height: 100%;
    min-width: 0;
    padding: 6px;
    box-sizing: border-box;
  }

  .device-info-card :deep(.arco-card-body) {
    height: 100%;
    padding: 6px 8px;
    display: flex;
    align-items: center;
  }

  .device-info-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 6px;
    width: 100%;
  }

  .device-info-item {
    display: flex;
    align-items: baseline;
    gap: 6px;
    min-width: 0;
    color: var(--color-text-2);
  }

  .device-info-label {
    font-size: 11px;
    line-height: 1.25;
    color: var(--color-text-3);
  }

  .device-info-value {
    font-size: 12px;
    line-height: 1.25;
    color: var(--color-text-2);
    font-weight: 400;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
