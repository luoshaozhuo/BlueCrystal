import Mock from 'mockjs';
import type { MockParams } from '@/types/mock';
import { isLogin } from '@/utils/auth';
import setupMock, {
  failResponseWrap,
  successResponseWrap,
} from '@/utils/setup-mock';
import { createMenuListMock, createUserInfoMock } from './data';

setupMock({
  setup() {
    Mock.mock(new RegExp('/api/user/info'), () => {
      if (isLogin()) {
        return successResponseWrap(createUserInfoMock());
      }
      return failResponseWrap(null, '未登录', 50008);
    });

    Mock.mock(new RegExp('/api/user/login'), (params: MockParams) => {
      const { username, password } = JSON.parse(params.body);
      if (!username) {
        return failResponseWrap(null, '用户名不能为空', 50000);
      }
      if (!password) {
        return failResponseWrap(null, '密码不能为空', 50000);
      }
      if (username === 'admin' && password === 'admin') {
        window.localStorage.setItem('userRole', 'admin');
        return successResponseWrap({ token: '12345' });
      }
      if (username === 'user' && password === 'user') {
        window.localStorage.setItem('userRole', 'user');
        return successResponseWrap({ token: '54321' });
      }
      return failResponseWrap(null, '账号或者密码错误', 50000);
    });

    Mock.mock(new RegExp('/api/user/logout'), () => {
      return successResponseWrap(null);
    });

    Mock.mock(new RegExp('/api/user/menu'), () => {
      return successResponseWrap(createMenuListMock());
    });
  },
});

export * from './data';
