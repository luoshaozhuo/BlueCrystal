<template>
  <div class="container">
    <div class="logo">
      <img
        class="app-logo"
        alt="logo"
        :src="logoUrl"
        :style="{ filter: 'brightness(0) invert(1)' }"
      />
      <a-typography-title
        class="logo-text"
        :style="{ margin: 0, fontSize: '18px', color: '#fff' }"
        :heading="5"
      >
        LiDance
      </a-typography-title>
    </div>
    <LoginBanner />
    <div class="content">
      <div class="content-inner">
        <LoginForm />
      </div>
      <div class="footer">
        <Footer />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import logoUrl from '@/assets/logo.svg?url';
  import Footer from '@/components/footer/index.vue';
  import LoginBanner from './components/banner.vue';
  import LoginForm from './components/login-form.vue';
</script>

<style lang="less" scoped>
  .container {
    display: flex;
    height: 100vh;

    .banner {
      width: 550px;
      background: linear-gradient(163.85deg, #1d2129 0%, #00308f 100%);
    }

    .content {
      position: relative;
      display: flex;
      flex: 1;
      align-items: center;
      justify-content: center;
      padding-bottom: 40px;
    }

    .footer {
      position: absolute;
      right: 0;
      bottom: 0;
      width: 100%;
    }
  }

  .logo {
    position: fixed;
    top: 24px;
    left: 22px;
    z-index: 10;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    pointer-events: none;

    .app-logo {
      width: 36px;
      height: 36px;
      flex: 0 0 auto;
      object-fit: contain;
    }

    &-text {
      margin: 0;
    }
  }
</style>

<style lang="less" scoped>
  // responsive
  @media (max-width: @screen-lg) {
    .container {
      .banner {
        width: 25%;
      }
    }
  }
</style>
