import defaultAvatar from '@/assets/images/default-avatar.svg';

export function createUserInfoMock() {
  const role = window.localStorage.getItem('userRole') || 'admin';
  return {
    name: 'admin',
    avatar: defaultAvatar,
    email: 'wangliqun@email.com',
    job: 'frontend',
    jobName: '前端艺术家',
    organization: 'Frontend',
    organizationName: '前端',
    location: 'beijing',
    locationName: '北京',
    introduction: '人潇洒，性温存',
    personalWebsite: 'https://www.arco.design',
    phone: '150****0000',
    registrationDate: '2013-05-10 12:10:00',
    accountId: '15012312300',
    certification: 1,
    role,
  };
}

export function createMenuListMock() {
  return [
    {
      path: '/dashboard',
      name: 'dashboard',
      meta: {
        locale: 'menu.server.dashboard',
        requiresAuth: true,
        icon: 'icon-dashboard',
        order: 1,
      },
      children: [
        {
          path: 'index',
          name: 'DashboardIndex',
          meta: {
            locale: 'menu.dashboard',
            requiresAuth: true,
          },
        },
        {
          path: 'https://arco.design',
          name: 'arcoWebsite',
          meta: {
            locale: 'menu.arcoWebsite',
            requiresAuth: true,
          },
        },
      ],
    },
  ];
}
