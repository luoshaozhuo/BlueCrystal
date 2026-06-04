<template>
  <div class="device-comm-panel">
    <div class="device-comm-panel__row">
      <a-card class="device-section-card" :bordered="false">
        <a-row :gutter="[8, 8]">
          <a-col v-for="device in turbineDevices" :key="device.id" :span="4">
            <a-tooltip
              content-class="device-chart-tooltip-overlay"
              :content-style="deviceTooltipContentStyle"
            >
              <template #content>
                <div>{{ device.id }}</div>
                <div>状态：{{ statusLabelMap[device.status] }}</div>
                <div>时延：{{ displayDelay(device) }}</div>
                <div>信号质量：{{ displaySignal(device) }}</div>
                <div>丢包率：{{ device.status === 'offline' ? '--' : `${device.packetLoss.toFixed(1)}%` }}</div>
                <div>最后心跳：{{ device.status === 'offline' ? '--' : `${device.heartbeatSec}s` }}</div>
                <div>最近异常次数：{{ device.anomalies }}</div>
              </template>
              <a-card class="device-item-card" :bordered="true" size="small">
                <div class="device-item-card__head">
                  <span class="device-item-card__id">{{ device.id }}</span>
                  <a-tag size="small" :color="statusTagColorMap[device.status]">
                    {{ statusLabelMap[device.status] }}
                  </a-tag>
                </div>
                <div class="device-item-card__meta">时延 {{ displayDelay(device) }}</div>
                <div class="device-item-card__meta">质量 {{ displaySignal(device) }}</div>
              </a-card>
            </a-tooltip>
          </a-col>
        </a-row>
      </a-card>

      <a-card class="device-section-card" :bordered="false">
        <a-row :gutter="[8, 8]">
          <a-col v-for="device in lidarDevices" :key="device.id" :span="12">
            <a-tooltip
              content-class="device-chart-tooltip-overlay"
              :content-style="deviceTooltipContentStyle"
            >
              <template #content>
                <div>{{ device.id }}</div>
                <div>状态：{{ statusLabelMap[device.status] }}</div>
                <div>时延：{{ displayDelay(device) }}</div>
                <div>信号质量：{{ displaySignal(device) }}</div>
                <div>丢包率：{{ device.status === 'offline' ? '--' : `${device.packetLoss.toFixed(1)}%` }}</div>
                <div>最后心跳：{{ device.status === 'offline' ? '--' : `${device.heartbeatSec}s` }}</div>
                <div>最近异常次数：{{ device.anomalies }}</div>
              </template>
              <a-card class="device-item-card" :bordered="true" size="small">
                <div class="device-item-card__head">
                  <span class="device-item-card__id">{{ device.id }}</span>
                  <a-tag size="small" :color="statusTagColorMap[device.status]">
                    {{ statusLabelMap[device.status] }}
                  </a-tag>
                </div>
                <div class="device-item-card__meta">时延 {{ displayDelay(device) }}</div>
                <div class="device-item-card__meta">质量 {{ displaySignal(device) }}</div>
              </a-card>
            </a-tooltip>
          </a-col>
        </a-row>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { useChartTheme } from '@/config/chart-theme';
  import type { DeviceCommItem, DeviceCommStatus } from '@/mock/data-acquisition';

  const props = defineProps<{
    data: {
      devices: DeviceCommItem[];
    };
  }>();
  const chartTheme = useChartTheme();

  const statusLabelMap: Record<DeviceCommStatus, string> = {
    online: '在线',
    warning: '告警',
    offline: '离线',
  };

  const statusTagColorMap: Record<DeviceCommStatus, string> = {
    online: 'arcoblue',
    warning: 'orange',
    offline: 'red',
  };

  const devices = computed(() => props.data?.devices ?? []);
  const turbineDevices = computed(() => devices.value.filter((item) => item.type === 'turbine'));
  const lidarDevices = computed(() => devices.value.filter((item) => item.type === 'lidar'));
  const deviceTooltipContentStyle = computed(() => ({
    background: chartTheme.value.tooltipBg,
    border: `1px solid ${chartTheme.value.tooltipBorder}`,
    color: chartTheme.value.tooltipText,
    fontSize: `${chartTheme.value.tooltipTextStyle.fontSize}px`,
    lineHeight: `${chartTheme.value.tooltipTextStyle.lineHeight}px`,
  }));

  function displayDelay(device: DeviceCommItem) {
    return device.status === 'offline' ? '--' : `${device.delay}ms`;
  }

  function displaySignal(device: DeviceCommItem) {
    return device.status === 'offline' ? '--' : `${device.signal}%`;
  }
</script>

<style scoped lang="less">
  .device-comm-panel {
    height: 100%;
    min-height: 0;
  }

  .device-comm-panel__row {
    display: flex;
    gap: 8px;
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  .device-section-card {
    flex: 1 1 0;
    height: 100%;
    min-height: 0;
  }

  .device-section-card:first-child {
    flex: 8 1 0;
  }

  .device-section-card:last-child {
    flex: 2 1 0;
  }

  .device-section-card :deep(.arco-card-body) {
    padding: 6px;
    height: 100%;
    overflow: hidden;
  }

  .device-item-card {
    min-height: 0;
  }

  .device-item-card :deep(.arco-card-body) {
    padding: 6px;
  }

  .device-item-card__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    margin-bottom: 4px;
  }

  .device-item-card__id {
    font-weight: 600;
    color: var(--color-text-1);
  }

  .device-item-card__meta {
    font-size: 11px;
    line-height: 1.35;
    color: var(--color-text-2);
  }

  :global(.device-chart-tooltip-overlay .arco-tooltip-content),
  :global(.device-chart-tooltip-overlay .arco-trigger-content) {
    background: v-bind('chartTheme.tooltipBg');
    color: v-bind('chartTheme.tooltipText');
  }
</style>
