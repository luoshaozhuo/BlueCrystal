import { mergeConfig } from 'vite';
import eslint from 'vite-plugin-eslint';
import baseConfig from './vite.config.base';

const enableEslintPlugin = process.env.VITE_ENABLE_ESLINT === 'true';
const shouldOpenBrowser = process.env.VITE_OPEN === 'true';

export default mergeConfig(
  {
    mode: 'development',
    server: {
      open: shouldOpenBrowser,
      fs: {
        strict: true,
      },
    },
    plugins: enableEslintPlugin
      ? [
          eslint({
            cache: false,
            include: ['src/**/*.ts', 'src/**/*.tsx', 'src/**/*.vue'],
            exclude: ['node_modules'],
          }),
        ]
      : [],
  },
  baseConfig,
);
