import type {
  WindFarmInfo,
  WindFarmInfoResponse,
} from '@/api/generated/openapi';
import { successResponseWrap } from '@/utils/setup-mock';
const mockWindFarmInfo: WindFarmInfo = {
  name: '西山风电场',
  centerLon: 112.364649,
  centerLat: 37.9340015,
  radiusMeters: 2500,
};

export function createWindFarmInfoResponse(): WindFarmInfoResponse {
  return successResponseWrap({ ...mockWindFarmInfo }) as WindFarmInfoResponse;
}
