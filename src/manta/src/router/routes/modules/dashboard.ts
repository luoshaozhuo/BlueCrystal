import { DEFAULT_LAYOUT } from '../base';
import { AppRouteRecordRaw } from '../types';

const Dashboard: AppRouteRecordRaw = {
  path: '/dashboard',
  name: 'Dashboard',
  component: DEFAULT_LAYOUT,
  redirect: '/dashboard/index',
  meta: {
    locale: 'menu.dashboard',
    requiresAuth: true,
    icon: 'icon-dashboard',
    order: 1,
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'DashboardIndex',
      component: () => import('@/views/dashboard/index.vue'),
      meta: {
        locale: 'menu.dashboard',
        requiresAuth: true,
      },
    },
  ],
};

export default Dashboard;
