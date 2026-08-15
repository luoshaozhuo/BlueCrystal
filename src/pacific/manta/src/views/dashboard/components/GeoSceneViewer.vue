<template>
  <div class="viewer-root">
    <div ref="el" class="cesium-container"></div>
    <div v-if="hoveredTurbineInfo" class="turbine-hover-card">
      <div class="turbine-hover-title">
        {{ t('viewer.turbineHoverTitle', { id: hoveredTurbineInfo.id }) }}
      </div>
      <template v-if="hoveredTurbineInfo.status">
        <div
          v-for="line in hoveredTurbineStatusLines"
          :key="line.labelKey"
          class="turbine-hover-line"
        >
          {{ t(line.labelKey) }}: {{ line.valueText }}
        </div>
      </template>
      <div v-else class="turbine-hover-line">
        {{ t('viewer.turbineHoverNoData') }}
      </div>
    </div>
    <div class="mouse-position">{{ mousePositionText }}</div>
  </div>
</template>

<script setup lang="ts">
  import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
  import {
    CameraEventType,
    Cartesian2,
    Cartesian3,
    Cartographic,
    CesiumTerrainProvider,
    Color,
    ConstantProperty,
    Credit,
    DistanceDisplayCondition,
    Ellipsoid,
    Entity,
    HeadingPitchRoll,
    HorizontalOrigin,
    ImageryLayer,
    JulianDate,
    LabelStyle,
    Material,
    Math as CesiumMath,
    NearFarScalar,
    NodeTransformationProperty,
    PropertyBag,
    Quaternion,
    Rectangle,
    sampleTerrainMostDetailed,
    ScreenSpaceEventHandler,
    ScreenSpaceEventType,
    TerrainProvider,
    Transforms,
    UrlTemplateImageryProvider,
    VerticalOrigin,
    Viewer,
    WebMercatorTilingScheme,
  } from 'cesium';
  import { useI18n } from 'vue-i18n';
  import axios from 'axios';
  import {
    getTurbineBaseInfo,
    getTurbineRealtimeStatus,
    getWindFarmInfo,
  } from '@/api/generated/openapi';
  import type {
    TurbineBaseInfo,
    TurbineRealtimeStatus,
    WindFarmInfo,
  } from '@/api/generated/openapi';

  const { t, locale } = useI18n({ useScope: 'global' });

  type HoveredTurbineInfo = { id: string; status?: TurbineRealtimeStatus };
  type HoverStatusLine = {
    labelKey:
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
      | 'viewer.turbineHoverReactivePower';
    valueText: string;
  };

  // 用 const：变量名本身不变（不重新指向别的值）
  // el、mousePositionText、hoveredTurbineInfo 都是 ref(...) 返回的对象引用。
  // 你会改的是它们的 .value，不是把变量本身重新赋值，所以用 const 最合适。
  // 用 let：后续会重新赋值
  // viewer、mouseMoveHandler、removeCameraPreRenderListener、stopTurbineRealtimePolling、
  // stopViewerResizeTracking：先是 undefined，初始化后赋函数/实例，卸载时又设回 undefined。
  // mouseHeightSampleToken、lastMouseTerrainSampleAtMs：运行过程中会递增/更新时间戳。
  // isApplyingPanClamp：会在逻辑里在 true/false 间切换。
  const el = ref<HTMLDivElement | null>(null);
  const mousePositionText = ref(t('viewer.mousePositionDefault'));
  const hoveredTurbineInfo = ref<HoveredTurbineInfo | null>(null);
  let viewer: Viewer | undefined;
  let mouseMoveHandler: ScreenSpaceEventHandler | undefined;
  let mouseHeightSampleToken = 0;
  let lastMouseTerrainSampleAtMs = 0;
  let removeCameraPreRenderListener: (() => void) | undefined;
  let stopTurbineRealtimePolling: (() => void) | undefined;
  let stopViewerResizeTracking: (() => void) | undefined;
  let isApplyingPanClamp = false;

  // 是否启用本地离线影像贴图（public/imagery）
  const enableOfflineImagery = true;
  // 是否绘制等高线（会一定程度干扰风机识别，默认关闭）
  const drawContour = true;
  const contourUniforms = {
    width: 1,
    spacing: 20,
    color: Color.fromCssColorString('#FFFFFF').withAlpha(0.25),
  };
  const contourMaterial = Material.fromType(
    'ElevationContour',
    contourUniforms,
  );
  const verticalExaggeration = 1.0;

  const initialHeadingDegrees = 360;
  const initialPitchDegrees = -45;
  const initialRollDegrees = 0;
  // 鼠标滚轮缩放灵敏度（越小越平缓）
  const wheelZoomFactor = 1.2;
  const restrictCameraToTerrainBounds = true;
  // 最小缩放距离（米）
  const baseMinimumZoomDistance = 30;
  // 最大俯仰角（度），用于避免视角过度贴地
  const maximumTiltAngleDegrees = 80;
  // 初始相机高度（米）
  const initialCameraHeightMeters = 3300;
  // 相机最大高度（米）
  const maximumCameraHeightMeters = 6000;
  const initialOrientation = {
    heading: CesiumMath.toRadians(initialHeadingDegrees),
    pitch: CesiumMath.toRadians(initialPitchDegrees),
    roll: CesiumMath.toRadians(initialRollDegrees),
  };

  // 离线影像可见层级范围
  const offlineImageryMinZoom = 12;
  const offlineImageryMaxZoom = 15;
  // 渲染像素比上限（越高越清晰但更耗性能）
  const maxRenderPixelRatio = 2;
  const minimumRenderResolutionScale = 1;
  const msaaSampleCount = 2;
  // 风机模型可调参数（统一放在前面，便于集中调优）
  const turbineModelScale = 1.0;
  const turbineModelMinimumPixelSize = 20;
  const turbineModelMaximumScale = 80;
  const turbineModelColor = Color.WHITE;
  const turbineModelSilhouetteColor = Color.CYAN;
  const turbineModelSilhouetteSize = 0.2;
  const turbineLabelFont =
    '50 10px "Orbitron", "Rajdhani", "JetBrains Mono", "SFMono-Regular", Consolas, monospace';
  const turbineLabelHeightOffsetMeters = 6; // 标签相对于风机中心的高度偏移，避免与模型重叠
  const turbineHubMarkerHeightOffsetMeters = 2; // 风机中心点标记相对于风机中心的高度偏移，避免与模型重叠
  const turbineHubMarkerPixelSize = 5;
  const turbineRealtimePollIntervalMs = 1000;
  const turbineRotorSpeedSmoothingPerSecond = 6;
  const turbineRotorAzimuthCorrectionPerSecond = 0.2;
  const turbineRotorAzimuthCorrectionDeadbandDegrees = 6;
  const turbineBladePitchSmoothingPerSecond = 8;
  const turbineYawSmoothingPerSecond = 6;
  const mouseTerrainSampleIntervalMs = 120;

  type TurbineEntityBundle = {
    baseInfo: TurbineBaseInfo;
    modelEntity: Entity;
    markerEntity: Entity;
    labelEntity: Entity;
    targetRotorAngleDegrees: number;
    currentRotorAngleDegrees: number;
    targetRotorSpeedRpm: number;
    currentRotorSpeedRpm: number;
    targetBladePitchDegrees: [number, number, number];
    currentBladePitchDegrees: [number, number, number];
    targetYawAngleDegrees: number;
    currentYawAngleDegrees: number;
    isRotorAzimuthInitialized: boolean;
    isYawInitialized: boolean;
    latestRealtimeStatus?: TurbineRealtimeStatus;
  };

  type TurbineEntityBundleMap = Map<string, TurbineEntityBundle>;

  type LayerBounds = [number, number, number, number];

  type ViewerBootstrapData = {
    windFarmInfo: WindFarmInfo;
    terrainProvider: TerrainProvider;
    terrainBounds: LayerBounds;
    turbineBaseInfo: TurbineBaseInfo[];
  };

  type ViewerRuntimeContext = {
    centerLon: number;
    centerLat: number;
    terrainDisplayRectangle: Rectangle;
    panLimitRectangle: Rectangle;
    offlineImageryProvider?: UrlTemplateImageryProvider;
    initialCameraHeight: number;
    minimumZoomDistance: number;
    maximumZoomDistance: number;
  };

  const turbineEntityIdPrefixes = [
    'turbine-model-',
    'turbine-marker-',
    'turbine-label-',
  ];

  const hoveredTurbineStatusLines = computed(() => {
    const status = hoveredTurbineInfo.value?.status;
    if (!status) return [];
    return buildHoveredTurbineStatusLines(status);
  });

  /** ==================== UI 文本与悬浮状态 ==================== */

  /**
   * 组装鼠标位置显示文案（经纬度 + 高程）。
   */
  function formatMousePositionText(
    longitude: number,
    latitude: number,
    heightText: string,
  ) {
    return t('viewer.mousePositionTemplate', {
      longitude: longitude.toFixed(6),
      latitude: latitude.toFixed(6),
      height: heightText,
    });
  }

  /**
   * 设置当前悬停风机信息；当值未变化时跳过更新，减少无效响应式触发。
   */
  function setHoveredTurbineInfo(
    hoveredInfoRef: { value: HoveredTurbineInfo | null },
    nextValue: HoveredTurbineInfo | null,
  ) {
    const current = hoveredInfoRef.value;
    if (!current && !nextValue) return;
    if (
      current &&
      nextValue &&
      current.id === nextValue.id &&
      current.status === nextValue.status
    )
      return;
    hoveredInfoRef.value = nextValue;
  }

  /**
   * 按统一精度和单位格式化状态值。
   */
  function formatStatusValue(
    value: number,
    fractionDigits: number,
    unit: string,
  ) {
    return `${value.toFixed(fractionDigits)} ${unit}`;
  }

  /**
   * 将实时状态对象转换为悬浮信息面板可直接渲染的行数据。
   */
  function buildHoveredTurbineStatusLines(
    status: TurbineRealtimeStatus,
  ): HoverStatusLine[] {
    return [
      { labelKey: 'viewer.turbineHoverTimestamp', valueText: status.timestamp },
      {
        labelKey: 'viewer.turbineHoverRotorSpeed',
        valueText: formatStatusValue(status.rotorSpeed, 2, 'rpm'),
      },
      {
        labelKey: 'viewer.turbineHoverRotorAzimuth',
        valueText: formatStatusValue(status.rotorAzimuth, 2, '°'),
      },
      {
        labelKey: 'viewer.turbineHoverPitch1',
        valueText: formatStatusValue(status.pitch1, 2, '°'),
      },
      {
        labelKey: 'viewer.turbineHoverPitch2',
        valueText: formatStatusValue(status.pitch2, 2, '°'),
      },
      {
        labelKey: 'viewer.turbineHoverPitch3',
        valueText: formatStatusValue(status.pitch3, 2, '°'),
      },
      {
        labelKey: 'viewer.turbineHoverYawAngle',
        valueText: formatStatusValue(status.yawAngle, 2, '°'),
      },
      {
        labelKey: 'viewer.turbineHoverWindSpeed',
        valueText: formatStatusValue(status.windSpeed, 2, 'm/s'),
      },
      {
        labelKey: 'viewer.turbineHoverWindDirection',
        valueText: formatStatusValue(status.windDirection, 2, '°'),
      },
      {
        labelKey: 'viewer.turbineHoverActivePower',
        valueText: formatStatusValue(status.activePower, 3, 'MW'),
      },
      {
        labelKey: 'viewer.turbineHoverReactivePower',
        valueText: formatStatusValue(status.reactivePower, 3, 'MVar'),
      },
    ];
  }

  /** ==================== 拾取与几何工具 ==================== */

  /**
   * 从实体 ID（如 turbine-model-01）中提取风机 ID。
   */
  function resolveTurbineIdFromEntityId(entityId: string) {
    for (const prefix of turbineEntityIdPrefixes) {
      if (entityId.startsWith(prefix)) {
        return entityId.slice(prefix.length);
      }
    }
    return undefined;
  }

  /**
   * 根据拾取结果解析悬停风机 ID；若未命中风机则返回 null。
   */
  function resolveHoveredTurbineId(
    pickedObject: unknown,
    turbineEntityMap: TurbineEntityBundleMap,
  ) {
    const entity = (pickedObject as { id?: unknown } | undefined)?.id;
    const entityId =
      typeof entity === 'string'
        ? entity
        : entity instanceof Entity && typeof entity.id === 'string'
          ? entity.id
          : undefined;
    if (!entityId) return null;

    const turbineId = resolveTurbineIdFromEntityId(entityId);
    if (!turbineId || !turbineEntityMap.has(turbineId)) {
      return null;
    }
    return turbineId;
  }

  /**
   * 根据中心点和半径（米）构建经纬度矩形，用于相机平移限制。
   */
  function createRectangleAroundCenter(
    centerLonDeg: number,
    centerLatDeg: number,
    radiusMeters: number,
  ) {
    const earthRadius = 6378137;
    const centerLon = CesiumMath.toRadians(centerLonDeg);
    const centerLat = CesiumMath.toRadians(centerLatDeg);
    const safeCos = Math.max(1e-6, Math.abs(Math.cos(centerLat)));
    const deltaLat = radiusMeters / earthRadius;
    const deltaLon = radiusMeters / (earthRadius * safeCos);

    return Rectangle.fromRadians(
      centerLon - deltaLon,
      centerLat - deltaLat,
      centerLon + deltaLon,
      centerLat + deltaLat,
    );
  }

  /**
   * 将相对 public 资源路径转为带 BASE_URL 的可访问地址。
   */
  function resolvePublicAssetUrl(relativePath: string) {
    const base = import.meta.env.BASE_URL || '/';
    const normalizedBase = base.endsWith('/') ? base : `${base}/`;
    const normalizedPath = relativePath.replace(/^\//, '');
    return `${normalizedBase}${normalizedPath}`;
  }

  /** ==================== 数据加载与资源定位 ==================== */

  /**
   * 拉取风场基础信息（中心点、半径等）。
   */
  async function loadWindFarmInfo(): Promise<WindFarmInfo> {
    const payload = await getWindFarmInfo();
    const responseData = payload.data;
    if (!responseData?.data || responseData.code !== 20000) {
      throw new Error(responseData?.msg || t('viewer.windFarmInfoLoadFailed'));
    }
    return responseData.data;
  }

  /**
   * 拉取风机基础信息（位置、模型名等）。
   */
  async function loadTurbineBaseInfo(): Promise<TurbineBaseInfo[]> {
    const payload = await getTurbineBaseInfo();
    const responseData = payload.data;
    if (!responseData?.data || responseData.code !== 20000) {
      throw new Error(responseData?.msg || 'Failed to load turbine base info');
    }
    return responseData.data;
  }

  /**
   * 拉取风机实时状态（支持按 ID 过滤）。
   */
  async function loadTurbineRealtimeStatus(
    turbineIds?: string[],
  ): Promise<TurbineRealtimeStatus[]> {
    const idsQuery =
      turbineIds && turbineIds.length > 0 ? turbineIds.join(',') : undefined;
    const payload = await getTurbineRealtimeStatus({
      query: idsQuery ? { ids: idsQuery } : undefined,
    });
    const responseData = payload.data;
    if (!responseData?.data || responseData.code !== 20000) {
      throw new Error(
        responseData?.msg || 'Failed to load turbine realtime status',
      );
    }
    return responseData.data;
  }

  /**
   * 加载地形 Provider 与 terrain 边界配置。
   */
  async function loadRequiredTerrainConfig() {
    const terrainRootUrl = resolvePublicAssetUrl('terrain/');
    const terrainLayerUrl = resolvePublicAssetUrl('terrain/layer.json');
    const [terrainProvider, layerResponse] = await Promise.all([
      CesiumTerrainProvider.fromUrl(terrainRootUrl, {
        requestVertexNormals: true,
        requestWaterMask: false,
        requestMetadata: true,
      }),
      axios.get<{ bounds: LayerBounds }>(terrainLayerUrl),
    ]);

    return {
      terrainProvider,
      bounds: layerResponse.data.bounds,
    };
  }

  /**
   * 解析风机模型文件访问地址。
   */
  function resolveTurbineModelUrl(modelName: string) {
    const normalizedModelFileName = modelName.toLowerCase().endsWith('.glb')
      ? modelName
      : `${modelName}.glb`;
    return resolvePublicAssetUrl(`models/${normalizedModelFileName}`);
  }

  /**
   * 批量创建风机模型、中心点与标签实体，并初始化运行时状态容器。
   */
  async function addTurbineModelsToScene(
    viewerInstance: Viewer,
    turbines: TurbineBaseInfo[],
  ): Promise<TurbineEntityBundleMap> {
    const turbineEntities = new Map<string, TurbineEntityBundle>();

    turbines.forEach((turbine) => {
      const modelPosition = Cartesian3.fromDegrees(
        turbine.lon,
        turbine.lat,
        turbine.height,
      );
      const modelEntity = viewerInstance.entities.add({
        id: `turbine-model-${turbine.id}`,
        position: modelPosition,
        model: {
          uri: resolveTurbineModelUrl(turbine.modelName),
          scale: turbineModelScale,
          minimumPixelSize: turbineModelMinimumPixelSize,
          maximumScale: turbineModelMaximumScale,
          color: turbineModelColor,
          silhouetteColor: turbineModelSilhouetteColor,
          silhouetteSize: turbineModelSilhouetteSize,
        },
      });

      const markerEntity = viewerInstance.entities.add({
        id: `turbine-marker-${turbine.id}`,
        position: Cartesian3.fromDegrees(
          turbine.lon,
          turbine.lat,
          turbine.height + turbineHubMarkerHeightOffsetMeters,
        ),
        point: {
          pixelSize: turbineHubMarkerPixelSize,
          color: Color.fromCssColorString('#00E5FF').withAlpha(0.95),
          outlineColor:
            Color.fromCssColorString('#022A3A').withAlpha(0.95),
          outlineWidth: 2.5,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new NearFarScalar(300, 1.2, 12000, 0.8),
        },
      });

      const labelEntity = viewerInstance.entities.add({
        id: `turbine-label-${turbine.id}`,
        position: Cartesian3.fromDegrees(
          turbine.lon,
          turbine.lat,
          turbine.height + turbineLabelHeightOffsetMeters,
        ),
        label: {
          text: `#${turbine.id}`,
          font: turbineLabelFont,
          style: LabelStyle.FILL_AND_OUTLINE,
          fillColor: Color.fromCssColorString('#7DF9FF').withAlpha(0.95),
          outlineColor:
            Color.fromCssColorString('#00E5FF').withAlpha(0.75),
          outlineWidth: 2,
          showBackground: true,
          backgroundColor:
            Color.fromCssColorString('#091524').withAlpha(0.65),
          backgroundPadding: new Cartesian2(8, 5),
          verticalOrigin: VerticalOrigin.BOTTOM,
          horizontalOrigin: HorizontalOrigin.CENTER,
          pixelOffset: new Cartesian2(0, -8),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          distanceDisplayCondition: new DistanceDisplayCondition(
            0,
            12000,
          ),
        },
      });

      turbineEntities.set(turbine.id, {
        baseInfo: turbine,
        modelEntity,
        markerEntity,
        labelEntity,
        targetRotorAngleDegrees: 0,
        currentRotorAngleDegrees: 0,
        targetRotorSpeedRpm: 0,
        currentRotorSpeedRpm: 0,
        targetBladePitchDegrees: [0, 0, 0],
        currentBladePitchDegrees: [0, 0, 0],
        targetYawAngleDegrees: 0,
        currentYawAngleDegrees: 0,
        isRotorAzimuthInitialized: false,
        isYawInitialized: false,
      });
    });

    return turbineEntities;
  }

  /**
   * 应用轮毂与三支叶片的节点旋转变换。
   */
  function applyRotorNodeTransformations(bundle: TurbineEntityBundle) {
    if (!bundle.modelEntity.model) return;

    const hubRotation = Quaternion.fromAxisAngle(
      Cartesian3.UNIT_X,
      CesiumMath.toRadians(bundle.currentRotorAngleDegrees),
    );
    const blade1PitchRotation = Quaternion.fromAxisAngle(
      Cartesian3.UNIT_X,
      CesiumMath.toRadians(bundle.currentBladePitchDegrees[0]),
    );
    const blade2PitchRotation = Quaternion.fromAxisAngle(
      Cartesian3.UNIT_X,
      CesiumMath.toRadians(bundle.currentBladePitchDegrees[1]),
    );
    const blade3PitchRotation = Quaternion.fromAxisAngle(
      Cartesian3.UNIT_X,
      CesiumMath.toRadians(bundle.currentBladePitchDegrees[2]),
    );

    bundle.modelEntity.model.nodeTransformations = new PropertyBag({
      WT_Hub: new NodeTransformationProperty({
        rotation: hubRotation,
      }),
      WT_Blade1: new NodeTransformationProperty({
        rotation: blade1PitchRotation,
      }),
      WT_Blade2: new NodeTransformationProperty({
        rotation: blade2PitchRotation,
      }),
      WT_Blade3: new NodeTransformationProperty({
        rotation: blade3PitchRotation,
      }),
    });
  }

  /**
   * 将角度归一化到 [0, 360)。
   */
  function normalizeAngleDegrees(angleDegrees: number) {
    let normalized = angleDegrees % 360;
    if (normalized < 0) normalized += 360;
    return normalized;
  }

  /**
   * 计算两个角度间的最短有符号差值（范围 [-180, 180]）。
   */
  function shortestAngleDeltaDegrees(fromAngle: number, toAngle: number) {
    const delta = normalizeAngleDegrees(toAngle - fromAngle);
    return delta > 180 ? delta - 360 : delta;
  }

  /**
   * 将偏航角写入模型朝向。
   */
  function applyYawOrientationToTurbine(
    bundle: TurbineEntityBundle,
    yawAngleDegrees: number,
  ) {
    const modelPosition = Cartesian3.fromDegrees(
      bundle.baseInfo.lon,
      bundle.baseInfo.lat,
      bundle.baseInfo.height,
    );
    const orientation = Transforms.headingPitchRollQuaternion(
      modelPosition,
      new HeadingPitchRoll(CesiumMath.toRadians(yawAngleDegrees), 0, 0),
    );
    bundle.modelEntity.orientation = new ConstantProperty(orientation);
  }

  /**
   * 将实时状态写入风机运行目标值，并处理首次初始化同步。
   */
  function applyRealtimeStatusToTurbine(
    bundle: TurbineEntityBundle,
    status: TurbineRealtimeStatus,
  ) {
    bundle.latestRealtimeStatus = status;
    bundle.targetRotorSpeedRpm = Math.max(0, status.rotorSpeed);
    bundle.targetRotorAngleDegrees = normalizeAngleDegrees(status.rotorAzimuth);
    bundle.targetBladePitchDegrees = [
      status.pitch1,
      status.pitch2,
      status.pitch3,
    ];
    bundle.targetYawAngleDegrees = normalizeAngleDegrees(status.yawAngle);

    if (!bundle.isYawInitialized) {
      bundle.currentYawAngleDegrees = bundle.targetYawAngleDegrees;
      bundle.isYawInitialized = true;
      applyYawOrientationToTurbine(bundle, bundle.currentYawAngleDegrees);
    }

    if (!bundle.isRotorAzimuthInitialized) {
      bundle.currentRotorAngleDegrees = bundle.targetRotorAngleDegrees;
      bundle.currentRotorSpeedRpm = bundle.targetRotorSpeedRpm;
      bundle.currentBladePitchDegrees = [...bundle.targetBladePitchDegrees] as [
        number,
        number,
        number,
      ];
      bundle.isRotorAzimuthInitialized = true;
      applyRotorNodeTransformations(bundle);
    }
  }

  /**
   * 启动风机实时轮询与动画插值更新，返回停止函数。
   */
  function startTurbineRealtimePolling(
    viewerInstance: Viewer,
    turbineEntityMap: TurbineEntityBundleMap,
    hoveredInfoRef: { value: HoveredTurbineInfo | null },
  ) {
    // [步骤1] 初始化轮询上下文
    const turbineIds = [...turbineEntityMap.keys()];
    if (turbineIds.length === 0) {
      return () => undefined;
    }

    let disposed = false;
    let polling = false;
    let lastAnimationTimeMs = Date.now();

    // [步骤2] 周期拉取实时状态并同步到目标值
    const tick = async () => {
      if (disposed || polling) return;
      polling = true;
      try {
        const realtimeStatusList = await loadTurbineRealtimeStatus(turbineIds);
        realtimeStatusList.forEach((status) => {
          const bundle = turbineEntityMap.get(status.id);
          if (!bundle) return;
          applyRealtimeStatusToTurbine(bundle, status);

          if (hoveredInfoRef.value?.id === status.id) {
            setHoveredTurbineInfo(hoveredInfoRef, {
              id: status.id,
              status,
            });
          }
        });
        viewerInstance.scene.requestRender();
      } catch (error) {
        console.error('Failed to update turbine realtime status:', error);
      } finally {
        polling = false;
      }
    };

    void tick();
    const pollTimer = window.setInterval(() => {
      void tick();
    }, turbineRealtimePollIntervalMs);

    // [步骤3] 每帧插值更新转子/桨距/偏航，保证动画平滑
    let animationFrameId = 0;
    const animate = () => {
      if (disposed) return;

      const now = Date.now();
      const deltaSeconds = Math.max(0, (now - lastAnimationTimeMs) / 1000);
      lastAnimationTimeMs = now;
      const rotorSpeedSmoothingFactor =
        1 - Math.exp(-turbineRotorSpeedSmoothingPerSecond * deltaSeconds);
      const rotorCorrectionFactor =
        1 - Math.exp(-turbineRotorAzimuthCorrectionPerSecond * deltaSeconds);
      const bladePitchSmoothingFactor =
        1 - Math.exp(-turbineBladePitchSmoothingPerSecond * deltaSeconds);
      const yawSmoothingFactor =
        1 - Math.exp(-turbineYawSmoothingPerSecond * deltaSeconds);

      turbineEntityMap.forEach((bundle) => {
        if (bundle.isRotorAzimuthInitialized) {
          bundle.currentRotorSpeedRpm +=
            (bundle.targetRotorSpeedRpm - bundle.currentRotorSpeedRpm) *
            rotorSpeedSmoothingFactor;

          if (
            bundle.currentRotorSpeedRpm < 0.01 &&
            bundle.targetRotorSpeedRpm < 0.01
          ) {
            bundle.currentRotorSpeedRpm = 0;
          }

          bundle.currentRotorAngleDegrees = normalizeAngleDegrees(
            bundle.currentRotorAngleDegrees +
              bundle.currentRotorSpeedRpm * 6 * deltaSeconds,
          );

          const rotorDriftDelta = shortestAngleDeltaDegrees(
            bundle.currentRotorAngleDegrees,
            bundle.targetRotorAngleDegrees,
          );
          const driftMagnitude = Math.abs(rotorDriftDelta);
          if (driftMagnitude > turbineRotorAzimuthCorrectionDeadbandDegrees) {
            const effectiveDrift =
              Math.sign(rotorDriftDelta) *
              (driftMagnitude - turbineRotorAzimuthCorrectionDeadbandDegrees);
            bundle.currentRotorAngleDegrees = normalizeAngleDegrees(
              bundle.currentRotorAngleDegrees +
                effectiveDrift * rotorCorrectionFactor,
            );
          }

          bundle.currentBladePitchDegrees = bundle.currentBladePitchDegrees.map(
            (currentPitch, index) => {
              const targetPitch = bundle.targetBladePitchDegrees[index];
              return (
                currentPitch +
                (targetPitch - currentPitch) * bladePitchSmoothingFactor
              );
            },
          ) as [number, number, number];

          applyRotorNodeTransformations(bundle);
        }

        if (bundle.isYawInitialized) {
          const yawDelta = shortestAngleDeltaDegrees(
            bundle.currentYawAngleDegrees,
            bundle.targetYawAngleDegrees,
          );
          bundle.currentYawAngleDegrees = normalizeAngleDegrees(
            bundle.currentYawAngleDegrees + yawDelta * yawSmoothingFactor,
          );
          applyYawOrientationToTurbine(bundle, bundle.currentYawAngleDegrees);
        }
      });

      viewerInstance.scene.requestRender();
      animationFrameId = window.requestAnimationFrame(animate);
    };

    // [步骤4] 返回清理函数，停止轮询与动画
    animationFrameId = window.requestAnimationFrame(animate);

    return () => {
      disposed = true;
      window.clearInterval(pollTimer);
      if (animationFrameId) {
        window.cancelAnimationFrame(animationFrameId);
      }
    };
  }

  /** ==================== 交互处理 ==================== */

  /**
   * 将相机立即飞到目标位置（duration=0）。
   */
  function flyToInitialView(
    viewerInstance: Viewer | undefined,
    destination: Cartesian3,
    orientation: { heading: number; pitch: number; roll: number },
  ) {
    if (!viewerInstance) return;
    viewerInstance.camera.flyTo({
      destination,
      orientation,
      duration: 0,
    });
  }

  /**
   * 创建鼠标移动监听：实时显示经纬度与地形高程。
   */
  function createMouseMoveHandler(
    viewerInstance: Viewer,
    mouseTextRef: { value: string },
    turbineEntityMap: TurbineEntityBundleMap,
    hoveredInfoRef: { value: HoveredTurbineInfo | null },
  ) {
    const handler = new ScreenSpaceEventHandler(
      viewerInstance.scene.canvas,
    );
    handler.setInputAction((movement: { endPosition: Cartesian2 }) => {
      // [步骤1] 先处理风机悬停命中与信息面板显示
      const pickedObject = viewerInstance.scene.pick(movement.endPosition);
      const hoveredTurbineId = resolveHoveredTurbineId(
        pickedObject,
        turbineEntityMap,
      );
      if (hoveredTurbineId) {
        const bundle = turbineEntityMap.get(hoveredTurbineId);
        setHoveredTurbineInfo(hoveredInfoRef, {
          id: hoveredTurbineId,
          status: bundle?.latestRealtimeStatus,
        });
      } else {
        setHoveredTurbineInfo(hoveredInfoRef, null);
      }

      // [步骤2] 再处理鼠标位置经纬度与高程显示
      const ray = viewerInstance.camera.getPickRay(movement.endPosition);
      if (!ray) {
        mouseTextRef.value = t('viewer.mousePositionDefault');
        return;
      }

      const cartesian = viewerInstance.scene.globe.pick(
        ray,
        viewerInstance.scene,
      );
      if (!cartesian) {
        mouseTextRef.value = t('viewer.mousePositionDefault');
        return;
      }

      const cartographic = Cartographic.fromCartesian(cartesian);
      const longitude = CesiumMath.toDegrees(cartographic.longitude);
      const latitude = CesiumMath.toDegrees(cartographic.latitude);
      const terrainHeight = viewerInstance.scene.globe.getHeight(cartographic);
      if (Number.isFinite(terrainHeight ?? NaN)) {
        mouseTextRef.value = formatMousePositionText(
          longitude,
          latitude,
          `${(terrainHeight as number).toFixed(2)} m`,
        );
        return;
      }

      // [步骤3] 无直接高程时，按节流策略发起高精度地形采样
      mouseTextRef.value = formatMousePositionText(
        longitude,
        latitude,
        t('viewer.mousePositionLoading'),
      );
      const nowMs = Date.now();
      if (nowMs - lastMouseTerrainSampleAtMs < mouseTerrainSampleIntervalMs) {
        return;
      }
      lastMouseTerrainSampleAtMs = nowMs;

      const requestToken = ++mouseHeightSampleToken;
      const samplePoint = Cartographic.clone(cartographic);

      void sampleTerrainMostDetailed(viewerInstance.terrainProvider, [
        samplePoint,
      ])
        .then((updated) => {
          if (requestToken !== mouseHeightSampleToken) return;
          const sampledHeight = updated[0]?.height;
          if (!Number.isFinite(sampledHeight ?? NaN)) {
            mouseTextRef.value = formatMousePositionText(
              longitude,
              latitude,
              t('viewer.mousePositionUnavailable'),
            );
            return;
          }
          mouseTextRef.value = formatMousePositionText(
            longitude,
            latitude,
            `${(sampledHeight as number).toFixed(2)} m`,
          );
        })
        .catch(() => {
          if (requestToken !== mouseHeightSampleToken) return;
          mouseTextRef.value = formatMousePositionText(
            longitude,
            latitude,
            t('viewer.mousePositionUnavailable'),
          );
        });
    }, ScreenSpaceEventType.MOUSE_MOVE);

    return handler;
  }

  /** ==================== Viewer 构建与渲染配置 ==================== */

  /**
   * 根据边界创建离线影像 Provider；关闭开关时返回 undefined。
   */
  function createOfflineImageryProvider(bounds: LayerBounds) {
    if (!enableOfflineImagery) return undefined;

    const [west, south, east, north] = bounds;
    return new UrlTemplateImageryProvider({
      url: resolvePublicAssetUrl('imagery/{z}/{x}/{y}.jpg'),
      minimumLevel: offlineImageryMinZoom,
      maximumLevel: offlineImageryMaxZoom,
      tilingScheme: new WebMercatorTilingScheme(),
      rectangle: Rectangle.fromDegrees(west, south, east, north),
      credit: new Credit(t('viewer.offlineImageryCredit')),
    });
  }

  /** ==================== 启动流程编排 ==================== */

  /**
   * 创建 GeoSceneViewer 实例并设置基础 UI/交互选项。
   */
  function createGeoSceneViewer(
    container: HTMLDivElement,
    terrainProvider: TerrainProvider,
    offlineImageryProvider?: UrlTemplateImageryProvider,
  ) {
    return new Viewer(container, {
      terrainProvider,
      baseLayer: offlineImageryProvider
        ? new ImageryLayer(offlineImageryProvider)
        : false,
      useBrowserRecommendedResolution: false,
      requestRenderMode: true,
      animation: false,
      timeline: false,
      homeButton: true,
      geocoder: false,
      sceneModePicker: false,
      baseLayerPicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
      infoBox: false,
      selectionIndicator: false,
      shouldAnimate: false,
    });
  }

  /**
   * 监听容器尺寸变化并同步触发 Cesium resize，避免窗口放大后画面不拉伸。
   */
  function setupViewerResizeTracking(
    container: HTMLDivElement,
    viewerInstance: Viewer,
  ) {
    if (typeof ResizeObserver === 'undefined') {
      const onResize = () => {
        viewerInstance.resize();
        viewerInstance.scene.requestRender();
      };
      window.addEventListener('resize', onResize);
      return () => {
        window.removeEventListener('resize', onResize);
      };
    }

    let resizeRafId = 0;
    const resizeObserver = new ResizeObserver(() => {
      if (resizeRafId) return;
      resizeRafId = window.requestAnimationFrame(() => {
        resizeRafId = 0;
        viewerInstance.resize();
        viewerInstance.scene.requestRender();
      });
    });
    resizeObserver.observe(container);

    return () => {
      if (resizeRafId) {
        window.cancelAnimationFrame(resizeRafId);
        resizeRafId = 0;
      }
      resizeObserver.disconnect();
    };
  }

  /**
   * 配置渲染相关参数（像素比、FXAA、版权信息隐藏）。
   */
  function configureViewerRendering(viewerInstance: Viewer) {
    const devicePixelRatio =
      typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    viewerInstance.resolutionScale = Math.min(
      maxRenderPixelRatio,
      Math.max(minimumRenderResolutionScale, devicePixelRatio),
    );
    viewerInstance.scene.msaaSamples = msaaSampleCount;
    viewerInstance.scene.postProcessStages.fxaa.enabled = false;

    const creditContainer = viewerInstance.cesiumWidget
      .creditContainer as HTMLElement | null;
    if (creditContainer) {
      creditContainer.style.display = 'none';
    }
  }

  /**
   * 配置地球场景与地形显示范围。
   */
  function configureGlobeScene(
    viewerInstance: Viewer,
    terrainDisplayRectangle: Rectangle,
  ) {
    Object.assign(viewerInstance.scene.globe, {
      enableLighting: true,
      baseColor: Color.fromCssColorString('#808080'),
      showGroundAtmosphere: true,
      dynamicAtmosphereLighting: true,
      dynamicAtmosphereLightingFromSun: true,
      showSkirts: true,
      depthTestAgainstTerrain: true,
      maximumScreenSpaceError: 1.0,
    });
    viewerInstance.scene.globe.cartographicLimitRectangle =
      terrainDisplayRectangle;
    viewerInstance.scene.globe.translucency.enabled = false;
  }

  /**
   * 配置相机控制器（缩放、俯仰、惯性、事件类型）。
   */
  function configureCameraController(
    viewerInstance: Viewer,
    minimumZoomDistance: number,
    maximumZoomDistance: number,
  ) {
    const maximumTiltAngle = CesiumMath.toRadians(maximumTiltAngleDegrees);
    Object.assign(viewerInstance.scene.screenSpaceCameraController, {
      zoomFactor: wheelZoomFactor,
      maximumZoomDistance,
      minimumZoomDistance,
      maximumTiltAngle,
      inertiaZoom: 0,
      inertiaTranslate: 0,
      zoomEventTypes: [
        CameraEventType.WHEEL,
        CameraEventType.PINCH,
      ],
    });
    viewerInstance.camera.constrainedAxis = Cartesian3.UNIT_Z;
  }

  /**
   * 配置天空/雾效与固定时间，用于统一画面亮度与氛围。
   */
  function configureSkyAndClock(viewerInstance: Viewer) {
    viewerInstance.scene.verticalExaggeration = verticalExaggeration;
    viewerInstance.scene.verticalExaggerationRelativeHeight = 0.0;
    viewerInstance.scene.globe.enableLighting = true;
    viewerInstance.scene.skyBox = undefined as any;
    viewerInstance.scene.backgroundColor = new Color(
      0.75,
      0.85,
      0.95,
      1.0,
    );
    viewerInstance.scene.fog.enabled = false;

    if (viewerInstance.scene.skyAtmosphere) {
      viewerInstance.scene.skyAtmosphere.show = true;
      viewerInstance.scene.skyAtmosphere.hueShift = 0.02;
      viewerInstance.scene.skyAtmosphere.saturationShift = 0.15;
      viewerInstance.scene.skyAtmosphere.brightnessShift = 0.05;
    }

    const afternoonTime = JulianDate.fromDate(
      new Date(Date.UTC(2024, 5, 1, 7, 0)),
    );
    viewerInstance.clock.currentTime = afternoonTime;
    viewerInstance.clock.shouldAnimate = false;
  }

  /**
   * 绑定 Home 行为并设置初始视角。
   */
  function setupHomeAndInitialView(
    viewerInstance: Viewer,
    centerCartesian: Cartesian3,
  ) {
    viewerInstance.homeButton?.viewModel.command.beforeExecute.addEventListener(
      (event) => {
        event.cancel = true;
        flyToInitialView(viewerInstance, centerCartesian, initialOrientation);
      },
    );
    flyToInitialView(viewerInstance, centerCartesian, initialOrientation);
  }

  /**
   * 在 preRender 中限制相机平移范围，超出时回拉到允许区域。
   */
  function setupPanLimitClamp(
    viewerInstance: Viewer,
    panLimitRectangle: Rectangle,
  ) {
    if (!restrictCameraToTerrainBounds) return undefined;

    const camera = viewerInstance.camera;
    const epsilonLonLat = 1e-7;

    return viewerInstance.scene.preRender.addEventListener(() => {
      // [步骤1] 避免递归回调触发
      if (isApplyingPanClamp) return;

      const cameraCartographic = Cartographic.fromCartesian(
        camera.position,
      );
      if (!cameraCartographic) return;

      const clampedLon = CesiumMath.clamp(
        cameraCartographic.longitude,
        panLimitRectangle.west,
        panLimitRectangle.east,
      );
      const clampedLat = CesiumMath.clamp(
        cameraCartographic.latitude,
        panLimitRectangle.south,
        panLimitRectangle.north,
      );

      const needsLonLatClamp =
        Math.abs(clampedLon - cameraCartographic.longitude) > epsilonLonLat ||
        Math.abs(clampedLat - cameraCartographic.latitude) > epsilonLonLat;

      // [步骤2] 未越界则不处理
      if (!needsLonLatClamp) return;

      // [步骤3] 越界后保持朝向不变，仅回拉位置
      isApplyingPanClamp = true;
      camera.setView({
        destination: Cartesian3.fromRadians(
          clampedLon,
          clampedLat,
          cameraCartographic.height,
        ),
        orientation: {
          heading: camera.heading,
          pitch: camera.pitch,
          roll: camera.roll,
        },
      });
      isApplyingPanClamp = false;
    });
  }

  /**
   * 并行加载 Viewer 初始化所需的数据。
   */
  async function loadViewerBootstrapData(): Promise<ViewerBootstrapData> {
    const [
      windFarmInfo,
      { terrainProvider, bounds: terrainBounds },
      turbineBaseInfo,
    ] = await Promise.all([
      loadWindFarmInfo(),
      loadRequiredTerrainConfig(),
      loadTurbineBaseInfo(),
    ]);

    return {
      windFarmInfo,
      terrainProvider,
      terrainBounds,
      turbineBaseInfo,
    };
  }

  /**
   * 根据风场与地形信息计算 Viewer 运行上下文参数。
   */
  function createViewerRuntimeContext(
    windFarmInfo: WindFarmInfo,
    terrainBounds: LayerBounds,
  ): ViewerRuntimeContext {
    const centerLon = windFarmInfo.centerLon;
    const centerLat = windFarmInfo.centerLat;
    const radiusMeters = Math.max(1, windFarmInfo.radiusMeters);
    const [west, south, east, north] = terrainBounds;
    const terrainDisplayRectangle = Rectangle.fromDegrees(
      west,
      south,
      east,
      north,
    );
    const radiusPanLimitRectangle = createRectangleAroundCenter(
      centerLon,
      centerLat,
      radiusMeters,
    );
    const panLimitRectangle =
      Rectangle.intersection(
        radiusPanLimitRectangle,
        terrainDisplayRectangle,
      ) ?? radiusPanLimitRectangle;

    return {
      centerLon,
      centerLat,
      terrainDisplayRectangle,
      panLimitRectangle,
      offlineImageryProvider: createOfflineImageryProvider(terrainBounds),
      initialCameraHeight: initialCameraHeightMeters,
      minimumZoomDistance: baseMinimumZoomDistance,
      maximumZoomDistance: maximumCameraHeightMeters,
    };
  }

  /**
   * 使用初始化数据创建并配置场景、风机实体与交互。
   */
  async function initializeViewerScene(
    container: HTMLDivElement,
    bootstrapData: ViewerBootstrapData,
  ) {
    // [步骤1] 组装运行上下文并创建 Viewer
    const { windFarmInfo, terrainProvider, terrainBounds, turbineBaseInfo } =
      bootstrapData;
    const runtimeContext = createViewerRuntimeContext(
      windFarmInfo,
      terrainBounds,
    );

    viewer = createGeoSceneViewer(
      container,
      terrainProvider,
      runtimeContext.offlineImageryProvider,
    );
    stopViewerResizeTracking = setupViewerResizeTracking(container, viewer);
    configureViewerRendering(viewer);

    // [步骤2] 计算中心点并校验地形可用性
    try {
      const [sampledCenter] = await sampleTerrainMostDetailed(
        terrainProvider,
        [
          Cartographic.fromDegrees(
            runtimeContext.centerLon,
            runtimeContext.centerLat,
          ),
        ],
      );
      if (!Number.isFinite(sampledCenter?.height ?? NaN)) {
        console.warn(t('viewer.terrainCenterSampleFailed'));
      }
    } catch (error) {
      console.warn(t('viewer.terrainCenterSampleFailed'), error);
    }
    const centerCartographic = Cartographic.fromDegrees(
      runtimeContext.centerLon,
      runtimeContext.centerLat,
      runtimeContext.initialCameraHeight,
    );
    const centerCartesian =
      Ellipsoid.WGS84.cartographicToCartesian(centerCartographic);

    // [步骤3] 配置场景、挂载实体与启动实时更新
    setupHomeAndInitialView(viewer, centerCartesian);
    configureGlobeScene(viewer, runtimeContext.terrainDisplayRectangle);
    configureCameraController(
      viewer,
      runtimeContext.minimumZoomDistance,
      runtimeContext.maximumZoomDistance,
    );
    const turbineEntityMap = await addTurbineModelsToScene(
      viewer,
      turbineBaseInfo,
    );
    stopTurbineRealtimePolling = startTurbineRealtimePolling(
      viewer,
      turbineEntityMap,
      hoveredTurbineInfo,
    );
    removeCameraPreRenderListener = setupPanLimitClamp(
      viewer,
      runtimeContext.panLimitRectangle,
    );
    configureSkyAndClock(viewer);

    // [步骤4] 绑定错误监听与可选等高线材质
    viewer.scene.globe.terrainProvider.errorEvent?.addEventListener((error) => {
      console.error('Terrain error:', error);
    });

    if (drawContour) {
      viewer.scene.globe.material = contourMaterial;
    }

    // [步骤5] 绑定鼠标交互（悬停 + 坐标高程）
    mouseMoveHandler = createMouseMoveHandler(
      viewer,
      mousePositionText,
      turbineEntityMap,
      hoveredTurbineInfo,
    );
  }

  /** ==================== 生命周期 ==================== */

  onMounted(async () => {
    if (!el.value) return;
    try {
      const bootstrapData = await loadViewerBootstrapData();
      await initializeViewerScene(el.value, bootstrapData);
    } catch (error) {
      console.error('Failed to initialize GeoSceneViewer:', error);
    }
  });

  onBeforeUnmount(() => {
    setHoveredTurbineInfo(hoveredTurbineInfo, null);
    stopViewerResizeTracking?.();
    stopViewerResizeTracking = undefined;
    stopTurbineRealtimePolling?.();
    stopTurbineRealtimePolling = undefined;
    removeCameraPreRenderListener?.();
    removeCameraPreRenderListener = undefined;
    mouseMoveHandler?.destroy();
    mouseMoveHandler = undefined;
    viewer?.destroy();
    viewer = undefined;
  });

  watch(locale, () => {
    mousePositionText.value = t('viewer.mousePositionDefault');
  });
</script>

<style scoped>
  .viewer-root {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .cesium-container {
    width: 100%;
    height: 100%;
  }

  :deep(.cesium-viewer-toolbar) {
    top: 16px;
    right: auto;
    left: 50%;
    display: flex;
    gap: 8px;
    transform: translateX(-50%);
  }

  .mouse-position {
    position: absolute;
    left: 50%;
    bottom: 12px;
    z-index: 10;
    padding: 6px 10px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    font-size: 12px;
    line-height: 1.4;
    pointer-events: none;
    transform: translateX(-50%);
  }

  .turbine-hover-card {
    position: absolute;
    left: 12px;
    top: 12px;
    z-index: 10;
    min-width: 280px;
    padding: 10px 12px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.7);
    color: #fff;
    font-size: 12px;
    line-height: 1.45;
    text-align: left;
    pointer-events: none;
  }

  .turbine-hover-title {
    margin-bottom: 6px;
    font-weight: 600;
  }

  .turbine-hover-line + .turbine-hover-line {
    margin-top: 2px;
  }
</style>
