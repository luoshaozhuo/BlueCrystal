import { DEFAULT_LAYOUT } from '../base';
import { AppRouteRecordRaw } from '../types';

const LoadMitigation: AppRouteRecordRaw = {
  path: '/load-mitigation',
  name: 'LoadMitigation',
  component: DEFAULT_LAYOUT,
  redirect: '/load-mitigation/index',
  meta: {
    locale: 'menu.load-mitigation',
    requiresAuth: true,
    icon: 'icon-experiment',
    order: 3,
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'LoadMitigationIndex',
      component: () => import('@/views/load-mitigation/index.vue'),
      meta: {
        locale: 'menu.load-mitigation',
        requiresAuth: true,
      },
    },
  ],
};

export default LoadMitigation;
