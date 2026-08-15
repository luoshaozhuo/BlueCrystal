import { DEFAULT_LAYOUT } from '../base';
import { AppRouteRecordRaw } from '../types';

const PowerOptimization: AppRouteRecordRaw = {
  path: '/power-optimization',
  name: 'PowerOptimization',
  component: DEFAULT_LAYOUT,
  redirect: '/power-optimization/index',
  meta: {
    locale: 'menu.power-optimization',
    requiresAuth: true,
    icon: 'icon-thunderbolt',
    order: 3,
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'PowerOptimizationIndex',
      component: () => import('@/views/power-analysis/index.vue'),
      meta: {
        locale: 'menu.power-optimization',
        requiresAuth: true,
      },
    },
  ],
};

export default PowerOptimization;
