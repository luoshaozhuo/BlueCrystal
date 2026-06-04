<template>
  <div class="volatility-summary">
    <div class="volatility-summary__top">
      <section class="subpanel">
        <TailCcdfChart :data="data.tailCcdf" />
      </section>
    </div>

    <div class="volatility-summary__bottom-wrap">
      <a-row class="volatility-summary__bottom" :gutter="8">
        <a-col :span="12" class="volatility-summary__half">
          <section class="subpanel">
            <DistributionShiftChart :data="data.distributionShift" />
          </section>
        </a-col>

        <a-col :span="12" class="volatility-summary__half">
          <section class="subpanel">
            <BootstrapStabilityChart :data="data.bootstrapStability" />
          </section>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
  import type { VolatilityEvidence } from '@/types/power-analysis';
  import BootstrapStabilityChart from './BootstrapStabilityChart.vue';
  import DistributionShiftChart from './DistributionShiftChart.vue';
  import TailCcdfChart from './TailCcdfChart.vue';

  defineProps<{
    data: VolatilityEvidence;
  }>();
</script>

<style scoped lang="less">
  .volatility-summary {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
    overflow: hidden;
  }

  .volatility-summary__top,
  .volatility-summary__bottom-wrap,
  .volatility-summary__bottom,
  .volatility-summary__half {
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  .volatility-summary__top {
    flex: 1 1 0;
  }

  .volatility-summary__bottom-wrap {
    flex: 1 1 0;
  }

  .subpanel {
    height: 100%;
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    padding: 8px 10px;
    overflow: hidden;
    box-sizing: border-box;
  }
</style>
