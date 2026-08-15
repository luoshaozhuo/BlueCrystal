/**
 * Image resource files used to compress the output of the production environment
 * 图片压缩
 * https://github.com/anncwb/vite-plugin-imagemin
 */
import viteImagemin from 'vite-plugin-imagemin';

export default function configImageminPlugin() {
  const imageminPlugin = viteImagemin({
    gifsicle: {
      optimizationLevel: 7,
      interlaced: false,
    },
    // PNG binaries are often blocked in CI/sandbox environments.
    // Skip PNG compression to avoid noisy runtime warnings.
    optipng: false,
    mozjpeg: {
      quality: 20,
    },
    pngquant: false,
    svgo: {
      plugins: [
        {
          name: 'removeViewBox',
        },
        {
          name: 'removeEmptyAttrs',
          active: false,
        },
      ],
    },
  });
  return imageminPlugin;
}
