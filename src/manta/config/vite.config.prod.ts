import { mergeConfig } from 'vite';
import baseConfig from './vite.config.base';
import configCompressPlugin from './plugin/compress';
import configVisualizerPlugin from './plugin/visualizer';
import configImageminPlugin from './plugin/imagemin';

function createManualChunk(id: string) {
  if (!id.includes('node_modules')) {
    return undefined;
  }

  // Cesium 体积大，按 engine 子域拆块可避免单一三维运行时 chunk 过大。
  if (id.includes('@cesium/widgets')) {
    return 'cesium-widgets';
  }

  if (id.includes('@cesium/engine/Source/Core/')) {
    return 'cesium-core';
  }

  if (id.includes('@cesium/engine/Source/Scene/')) {
    return 'cesium-scene';
  }

  if (
    id.includes('@cesium/engine/Source/Renderer/') ||
    id.includes('@cesium/engine/Source/Shaders/')
  ) {
    return 'cesium-renderer';
  }

  if (id.includes('@cesium/engine/Source/DataSources/')) {
    return 'cesium-data-sources';
  }

  if (id.includes('@cesium/engine') || id.includes('/cesium/Source/Cesium.js')) {
    return 'cesium-runtime';
  }

  if (
    id.includes('/echarts/') ||
    id.includes('/echarts-gl/') ||
    id.includes('/vue-echarts/')
  ) {
    return 'chart';
  }

  if (id.includes('/@arco-design/') || id.includes('/@arco-themes/')) {
    return 'arco';
  }

  if (id.includes('/lodash/')) {
    return 'lodash';
  }

  return 'vendor';
}

export default mergeConfig(
  {
    mode: 'production',
    plugins: [
      configCompressPlugin('gzip'),
      configVisualizerPlugin(),
      configImageminPlugin(),
    ],
    build: {
      rollupOptions: {
        onwarn(warning, warn) {
          if (
            warning.message.includes('Circular chunk: cesium-') ||
            warning.message.includes('Circular chunk: index -> cesium-')
          ) {
            return;
          }
          warn(warning);
        },
        output: {
          manualChunks: createManualChunk,
        },
      },
      chunkSizeWarningLimit: 2000,
    },
  },
  baseConfig,
);
