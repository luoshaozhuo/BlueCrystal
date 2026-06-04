<template>
  <div class="banner">
    <div class="banner-inner">
      <a-carousel class="carousel" animation-name="fade">
        <a-carousel-item v-for="item in carouselItem" :key="item.image">
          <div class="carousel-item">
            <img
              class="carousel-image"
              :class="item.className"
              :src="item.image"
            />
          </div>
        </a-carousel-item>
      </a-carousel>
    </div>
  </div>
</template>

<script lang="ts" setup>
  const bannerModules = import.meta.glob('@/assets/banner/*.{jpg,jpeg,png,webp}', {
    eager: true,
    import: 'default',
  }) as Record<string, string>;

  const carouselItem = Object.entries(bannerModules)
    .sort(([pathA], [pathB]) => pathA.localeCompare(pathB, undefined, { numeric: true }))
    .map(([, image]) => ({
      image,
      className: '',
    }));
</script>

<style lang="less" scoped>
  .banner {
    display: flex;
    align-items: center;
    justify-content: center;

    &-inner {
      flex: 1;
      height: 100%;
    }
  }

  .carousel {
    height: 100%;

    :deep(.arco-carousel-item) {
      height: 100%;
    }

    &-item {
      height: 100%;
      width: 100%;
    }

    &-image {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: cover;

    }
  }
</style>
