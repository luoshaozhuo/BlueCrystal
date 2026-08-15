import { DEFAULT_LAYOUT } from '../base';
import { AppRouteRecordRaw } from '../types';

const DataAcquisition: AppRouteRecordRaw = {
  path: '/data-acquisition',
  name: 'DataAcquisition',
  component: DEFAULT_LAYOUT,
  redirect: '/data-acquisition/index',
  meta: {
    locale: 'menu.data-acquisition',
    requiresAuth: true,
    icon: 'icon-storage',
    order: 5,
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'DataAcquisitionIndex',
      component: () => import('@/views/data-acquisition/index.vue'),
      meta: {
        locale: 'menu.data-acquisition',
        requiresAuth: true,
      },
    },
  ],
};

export default DataAcquisition;
