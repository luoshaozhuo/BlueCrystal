type MessageKey =
  | 'viewer.mousePositionDefault'
  | 'viewer.mousePositionLoading'
  | 'viewer.mousePositionUnavailable'
  | 'viewer.mousePositionTemplate'
  | 'viewer.turbineHoverTitle'
  | 'viewer.turbineHoverTimestamp'
  | 'viewer.turbineHoverRotorSpeed'
  | 'viewer.turbineHoverRotorAzimuth'
  | 'viewer.turbineHoverPitch1'
  | 'viewer.turbineHoverPitch2'
  | 'viewer.turbineHoverPitch3'
  | 'viewer.turbineHoverYawAngle'
  | 'viewer.turbineHoverWindSpeed'
  | 'viewer.turbineHoverWindDirection'
  | 'viewer.turbineHoverActivePower'
  | 'viewer.turbineHoverReactivePower'
  | 'viewer.turbineHoverNoData'
  | 'viewer.windFarmInfoLoadFailed'
  | 'viewer.terrainCenterSampleFailed'
  | 'viewer.offlineImageryCredit';

type MessageMap = Record<MessageKey, string>;

export const viewerZhCN: MessageMap = {
  'viewer.mousePositionDefault': '经度: -- 纬度: -- 高程: -- m',
  'viewer.mousePositionLoading': '加载中',
  'viewer.mousePositionUnavailable': '-- m',
  'viewer.mousePositionTemplate':
    '经度: {longitude} 纬度: {latitude} 高程: {height}',
  'viewer.turbineHoverTitle': '风机 #{id}',
  'viewer.turbineHoverTimestamp': '时间',
  'viewer.turbineHoverRotorSpeed': '叶轮转速',
  'viewer.turbineHoverRotorAzimuth': '叶轮方位角',
  'viewer.turbineHoverPitch1': '桨距角 1',
  'viewer.turbineHoverPitch2': '桨距角 2',
  'viewer.turbineHoverPitch3': '桨距角 3',
  'viewer.turbineHoverYawAngle': '偏航角',
  'viewer.turbineHoverWindSpeed': '风速',
  'viewer.turbineHoverWindDirection': '风向角',
  'viewer.turbineHoverActivePower': '有功功率',
  'viewer.turbineHoverReactivePower': '无功功率',
  'viewer.turbineHoverNoData': '暂无实时数据',
  'viewer.windFarmInfoLoadFailed': '获取风电场信息失败',
  'viewer.terrainCenterSampleFailed':
    '地形中心点高程采样失败：未读取到有效地形瓦片',
  'viewer.offlineImageryCredit': 'Offline Satellite Imagery',
};

export const viewerEnUS: MessageMap = {
  'viewer.mousePositionDefault': 'Lon: -- Lat: -- Elev: -- m',
  'viewer.mousePositionLoading': 'Loading',
  'viewer.mousePositionUnavailable': '-- m',
  'viewer.mousePositionTemplate':
    'Lon: {longitude} Lat: {latitude} Elev: {height}',
  'viewer.turbineHoverTitle': 'Turbine #{id}',
  'viewer.turbineHoverTimestamp': 'Timestamp',
  'viewer.turbineHoverRotorSpeed': 'Rotor Speed',
  'viewer.turbineHoverRotorAzimuth': 'Rotor Azimuth',
  'viewer.turbineHoverPitch1': 'Pitch 1',
  'viewer.turbineHoverPitch2': 'Pitch 2',
  'viewer.turbineHoverPitch3': 'Pitch 3',
  'viewer.turbineHoverYawAngle': 'Yaw Angle',
  'viewer.turbineHoverWindSpeed': 'Wind Speed',
  'viewer.turbineHoverWindDirection': 'Wind Direction',
  'viewer.turbineHoverActivePower': 'Active Power',
  'viewer.turbineHoverReactivePower': 'Reactive Power',
  'viewer.turbineHoverNoData': 'No realtime data',
  'viewer.windFarmInfoLoadFailed': 'Failed to load wind farm info',
  'viewer.terrainCenterSampleFailed':
    'Failed to sample center terrain elevation: no valid terrain tile available',
  'viewer.offlineImageryCredit': 'Offline Satellite Imagery',
};
