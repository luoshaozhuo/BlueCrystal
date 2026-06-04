import Mock from 'mockjs';
import setupMock, { successResponseWrap } from '@/utils/setup-mock';
import {
  createTurbineBaseInfoData,
  createTurbineRealtimeStatusData,
} from './turbine-data';
import { createWindFarmInfoResponse } from './windfarm-data';

function parseRealtimeStatusIds(url: string) {
  let ids: string[] | undefined;
  const queryIndex = url.indexOf('?');
  if (queryIndex >= 0) {
    const queryString = url.slice(queryIndex + 1);
    const idsValue = new URLSearchParams(queryString).get('ids');
    if (idsValue) {
      ids = idsValue
        .split(',')
        .map((id) => id.trim())
        .filter(Boolean);
    }
  }
  return ids;
}

setupMock({
  setup() {
    Mock.mock(new RegExp('/api/wind-farm/info'), () => {
      return createWindFarmInfoResponse();
    });

    Mock.mock(new RegExp('/api/turbine/base-info'), () => {
      const data = Mock.mock({
        data: createTurbineBaseInfoData(),
      });
      return successResponseWrap(data.data);
    });

    Mock.mock(new RegExp('/api/turbine/realtime-status'), (params: { url: string }) => {
      const data = Mock.mock({
        data: createTurbineRealtimeStatusData(Date.now(), parseRealtimeStatusIds(params.url)),
      });
      return successResponseWrap(data.data);
    });
  },
});

export * from './windfarm-data';
export * from './turbine-data';
