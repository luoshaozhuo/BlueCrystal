import { App, defineAsyncComponent } from 'vue';
import Breadcrumb from './breadcrumb/index.vue';

const Chart = defineAsyncComponent(() => import('./chart/index.vue'));

export default {
  install(Vue: App) {
    Vue.component('Chart', Chart);
    Vue.component('Breadcrumb', Breadcrumb);
  },
};
