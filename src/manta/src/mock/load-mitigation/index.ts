import Mock from 'mockjs';
import setupMock, { successResponseWrap } from '@/utils/setup-mock';
import { createLoadMitigationPageMock } from './rules';

setupMock({
  setup() {
    Mock.mock(new RegExp('/api/load-mitigation/page'), () => {
      return successResponseWrap(createLoadMitigationPageMock());
    });
  },
});

export * from './fixtures';
export * from './rules';
export * from './amplitude-structure';
export * from './markov-matrix';
export * from './optimization-evidence';
