import Mock from 'mockjs';
import setupMock, { successResponseWrap } from '@/utils/setup-mock';
import { getDataCollectionMock } from './rules';

let dataAcquisitionStep = 0;

setupMock({
  setup() {
    Mock.mock(new RegExp('/api/data-acquisition/page'), () => {
      const data = getDataCollectionMock(dataAcquisitionStep);
      dataAcquisitionStep += 1;
      return successResponseWrap(data);
    });
  },
});

export * from './fixtures';
export * from './rules';
