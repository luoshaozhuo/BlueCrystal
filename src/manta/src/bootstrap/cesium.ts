import { Resource } from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';

const baseUrl = import.meta.env.BASE_URL || '/';
const normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
const cesiumBaseUrl = `${normalizedBaseUrl}cesium/`;

(globalThis as { CESIUM_BASE_URL?: string }).CESIUM_BASE_URL = cesiumBaseUrl;

(
  Resource as typeof Resource & {
    supportsImageBitmapOptions?: () => Promise<boolean>;
  }
).supportsImageBitmapOptions = () => Promise.resolve(false);

const nativeCreateImageBitmap = globalThis.createImageBitmap?.bind(globalThis);

const loadImageElementFromBlob = (blob: Blob) =>
  new Promise<HTMLImageElement>((resolve, reject) => {
    const objectUrl = URL.createObjectURL(blob);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(image);
    };

    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(
        new Error(
          `Failed to decode image blob of type ${blob.type || 'unknown'}`,
        ),
      );
    };

    image.src = objectUrl;
  });

if (nativeCreateImageBitmap) {
  globalThis.createImageBitmap = (async (
    image: ImageBitmapSource,
    optionsOrSx?: number | ImageBitmapOptions,
    sy?: number,
    sw?: number,
    sh?: number,
    options?: ImageBitmapOptions,
  ) => {
    try {
      return await nativeCreateImageBitmap(
        image as never,
        optionsOrSx as never,
        sy as never,
        sw as never,
        sh as never,
        options as never,
      );
    } catch (error) {
      if (!(image instanceof Blob) || !image.type.startsWith('image/')) {
        throw error;
      }

      const decodedImage = await loadImageElementFromBlob(image);

      if (typeof optionsOrSx === 'number') {
        return nativeCreateImageBitmap(
          decodedImage,
          optionsOrSx,
          sy ?? 0,
          sw ?? 0,
          sh ?? 0,
        );
      }

      return nativeCreateImageBitmap(decodedImage);
    }
  }) as typeof globalThis.createImageBitmap;
}
