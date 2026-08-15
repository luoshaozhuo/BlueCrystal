import type {
  AxiosError,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { Message, Modal } from '@arco-design/web-vue';
import { client } from '@/api/generated/openapi/client.gen';
import type { Client } from '@/api/generated/openapi/client';
import { useUserStore } from '@/store';
import { getToken } from '@/utils/auth';

export interface HttpResponse<T = unknown> {
  status: string;
  msg: string;
  code: number;
  data: T;
}

const apiClient = client as Client;

apiClient.setConfig({
  baseURL: import.meta.env.VITE_API_BASE_URL || undefined,
  throwOnError: true,
});

apiClient.instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: unknown) => {
    // do something
    return Promise.reject(error);
  },
);

apiClient.instance.interceptors.response.use(
  (response: AxiosResponse<HttpResponse>) => {
    const res = response.data;
    if (res.code !== 20000) {
      Message.error({
        content: res.msg || 'Error',
        duration: 5 * 1000,
      });
      if (
        [50008, 50012, 50014].includes(res.code) &&
        response.config.url !== '/api/user/info'
      ) {
        Modal.error({
          title: 'Confirm logout',
          content:
            'You have been logged out, you can cancel to stay on this page, or log in again',
          okText: 'Re-Login',
          async onOk() {
            const userStore = useUserStore();

            await userStore.logout();
            window.location.reload();
          },
        });
      }
      return Promise.reject(new Error(res.msg || 'Error'));
    }
    return response;
  },
  (error: AxiosError<{ msg?: string }>) => {
    Message.error({
      content: error.response?.data?.msg || error.message || 'Request Error',
      duration: 5 * 1000,
    });
    return Promise.reject(error);
  },
);
