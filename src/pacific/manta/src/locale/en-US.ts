import localeLogin from '@/views/login/locale/en-US';

import localeSuccess from '@/views/result/success/locale/en-US';
import localeError from '@/views/result/error/locale/en-US';

import locale403 from '@/views/exception/403/locale/en-US';
import locale404 from '@/views/exception/404/locale/en-US';
import locale500 from '@/views/exception/500/locale/en-US';

import localeUserInfo from '@/views/user/info/locale/en-US';
import localeUserSetting from '@/views/user/setting/locale/en-US';
import { viewerEnUS } from '@/views/dashboard/components/GeoSceneViewer.locale';

import localeSettings from './en-US/settings';

export default {
  'menu.dashboard': 'Dashboard',
  'menu.data-acquisition': 'Data Acquisition',
  'menu.lidar-wind-field': 'Lidar Wind Field',
  'menu.load-mitigation': 'Load Mitigation',
  'menu.power-optimization': 'Power Optimization',
  'navbar.docs': 'Docs',
  'navbar.action.locale': 'Switch to English',
  'navbar.user.switchRoles': 'Switch Roles',
  'navbar.user.userCenter': 'User Center',
  'navbar.user.userSettings': 'User Settings',
  'navbar.user.logout': 'Logout',
  ...localeSettings,
  ...localeLogin,
  ...localeSuccess,
  ...localeError,
  ...locale403,
  ...locale404,
  ...locale500,
  ...localeUserInfo,
  ...localeUserSetting,
  ...viewerEnUS,
};
