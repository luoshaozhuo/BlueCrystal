import { createApp } from 'vue';
import ArcoVueIcon from '@arco-design/web-vue/es/icon';
import globalComponents from '@/components';
import router from './router';
import store from './store';
import i18n from './locale';
import directive from './directive';
import App from './App.vue';
// Styles are imported via arco-plugin. See config/plugin/arcoStyleImport.ts in the directory for details
// 样式通过 arco-plugin 插件导入。详见目录文件 config/plugin/arcoStyleImport.ts
// https://arco.design/docs/designlab/use-theme-package
import '@/assets/style/global.less';
import '@/bootstrap/cesium';
import '@/api/interceptor';
import '@arco-themes/vue-techblue/css/arco.css';
import defaultSettings from '@/config/settings.json';

async function bootstrap() {
  if (import.meta.env.DEV) {
    // Ensure mock handlers are registered before the first API requests.
    await import('./mock');
  }

  if (defaultSettings.theme === 'dark') {
    document.body.setAttribute('arco-theme', 'dark');
  } else {
    document.body.removeAttribute('arco-theme');
  }

  const app = createApp(App);
  app.use(ArcoVueIcon);
  app.use(router);
  app.use(store);
  app.use(i18n);
  app.use(globalComponents);
  app.use(directive);
  app.mount('#app');
}

bootstrap();
