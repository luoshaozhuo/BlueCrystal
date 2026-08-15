import localeLogin from '@/views/login/locale/zh-CN';

import localeSuccess from '@/views/result/success/locale/zh-CN';
import localeError from '@/views/result/error/locale/zh-CN';

import locale403 from '@/views/exception/403/locale/zh-CN';
import locale404 from '@/views/exception/404/locale/zh-CN';
import locale500 from '@/views/exception/500/locale/zh-CN';

import localeUserInfo from '@/views/user/info/locale/zh-CN';
import localeUserSetting from '@/views/user/setting/locale/zh-CN';
import { viewerZhCN } from '@/views/dashboard/components/GeoSceneViewer.locale';

import localeSettings from './zh-CN/settings';

export default {
  'menu.dashboard': '仪表板',
  'menu.data-acquisition': '数据采集',
  'menu.lidar-wind-field': '激光雷达',
  'menu.load-mitigation': '载荷分析',
  'menu.power-optimization': '功率分析',
  'navbar.docs': '文档中心',
  'navbar.action.locale': '切换为中文',
  'navbar.user.switchRoles': '切换角色',
  'navbar.user.userCenter': '用户中心',
  'navbar.user.userSettings': '用户设置',
  'navbar.user.logout': '退出登录',
  ...localeSettings,
  ...localeLogin,
  ...localeSuccess,
  ...localeError,
  ...locale403,
  ...locale404,
  ...locale500,
  ...localeUserInfo,
  ...localeUserSetting,
  ...viewerZhCN,
};
