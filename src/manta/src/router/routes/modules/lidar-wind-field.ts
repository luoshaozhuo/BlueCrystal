import { DEFAULT_LAYOUT } from '../base';
import { AppRouteRecordRaw } from '../types';

const LidarWindField: AppRouteRecordRaw = {
  path: '/lidar-wind-field',
  name: 'LidarWindField',
  component: DEFAULT_LAYOUT,
  redirect: '/lidar-wind-field/index',
  meta: {
    locale: 'menu.lidar-wind-field',
    requiresAuth: true,
    icon: 'icon-compass',
    order: 4,
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'LidarWindFieldIndex',
      component: () => import('@/views/lidar-wind-filed/index.vue'),
      meta: {
        locale: 'menu.lidar-wind-field',
        requiresAuth: true,
      },
    },
  ],
};

export default LidarWindField;
