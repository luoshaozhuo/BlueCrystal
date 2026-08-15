import Mock from 'mockjs';
import setupMock, { successResponseWrap } from '@/utils/setup-mock';
import {
  createCertificationMock,
  createLatestActivityMock,
  createMyProjectListMock,
  createMyTeamListMock,
  createProjectAndTeamListMock,
} from './data';

setupMock({
  setup() {
    Mock.mock(new RegExp('/api/user/my-project/list'), () => {
      return successResponseWrap(createMyProjectListMock());
    });

    Mock.mock(new RegExp('/api/user/latest-activity'), () => {
      return successResponseWrap(createLatestActivityMock());
    });

    Mock.mock(new RegExp('/api/user/visits'), () => {
      return successResponseWrap([
        { name: '主页访问量', visits: 5670, growth: 206.32 },
        { name: '项目访问量', visits: 5670, growth: 206.32 },
      ]);
    });

    Mock.mock(new RegExp('/api/user/project-and-team/list'), () => {
      return successResponseWrap(createProjectAndTeamListMock());
    });

    Mock.mock(new RegExp('/api/user/my-team/list'), () => {
      return successResponseWrap(createMyTeamListMock());
    });

    Mock.mock(new RegExp('/api/user/save-info'), () => {
      return successResponseWrap('ok');
    });

    Mock.mock(new RegExp('/api/user/certification'), () => {
      return successResponseWrap(createCertificationMock());
    });

    Mock.mock(new RegExp('/api/user/upload'), () => {
      return successResponseWrap('ok');
    });
  },
});

export * from './data';
