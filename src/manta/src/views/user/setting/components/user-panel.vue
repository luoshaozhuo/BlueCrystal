<template>
  <a-card :bordered="false">
    <a-space :size="54">
      <a-upload
        :custom-request="customRequest"
        list-type="picture-card"
        :file-list="fileList"
        :show-upload-button="true"
        :show-file-list="false"
        @change="uploadChange"
      >
        <template #upload-button>
          <a-avatar :size="100" class="info-avatar">
            <template #trigger-icon>
              <icon-camera />
            </template>
            <img v-if="fileList.length" :src="fileList[0].url" />
          </a-avatar>
        </template>
      </a-upload>
      <a-descriptions
        :data="renderData"
        :column="2"
        align="right"
        layout="inline-horizontal"
        :label-style="{
          width: '140px',
          fontWeight: 'normal',
          color: 'rgb(var(--gray-8))',
        }"
        :value-style="{
          width: '200px',
          paddingLeft: '8px',
          textAlign: 'left',
        }"
      >
        <template #label="{ label }">{{ $t(label) }} :</template>
        <template #value="{ value, data }">
          <a-tag
            v-if="data.label === 'userSetting.label.certification'"
            color="green"
            size="small"
          >
            已认证
          </a-tag>
          <span v-else>{{ value }}</span>
        </template>
      </a-descriptions>
    </a-space>
  </a-card>
</template>

<script lang="ts" setup>
  import { ref } from 'vue';
  import type { AxiosProgressEvent } from 'axios';
  import type {
    FileItem,
    RequestOption,
  } from '@arco-design/web-vue/es/upload/interfaces';
  import { useUserStore } from '@/store';
  import { userUploadApi } from '@/api/generated/openapi';
  import type { UserUploadResponse } from '@/api/generated/openapi';
  import type { DescData } from '@arco-design/web-vue/es/descriptions/interface';

  const userStore = useUserStore();
  const file = {
    uid: '-2',
    name: 'avatar.png',
    url: userStore.avatar,
  };
  const renderData = [
    {
      label: 'userSetting.label.name',
      value: userStore.name,
    },
    {
      label: 'userSetting.label.certification',
      value: userStore.certification,
    },
    {
      label: 'userSetting.label.accountId',
      value: userStore.accountId,
    },
    {
      label: 'userSetting.label.phone',
      value: userStore.phone,
    },
    {
      label: 'userSetting.label.registrationDate',
      value: userStore.registrationDate,
    },
  ] as DescData[];
  const fileList = ref<FileItem[]>([file]);
  const uploadChange = (fileItemList: FileItem[], fileItem: FileItem) => {
    fileList.value = [fileItem];
  };
  const customRequest = (options: RequestOption) => {
    // docs: https://axios-http.com/docs/cancellation
    const controller = new AbortController();

    (async function requestWrap() {
      const { onProgress, onError, onSuccess, fileItem } = options;
      onProgress(20);
      const onUploadProgress = (event: AxiosProgressEvent) => {
        const total = event.total ?? 0;
        let percent;
        if (total > 0) {
          percent = (event.loaded / total) * 100;
        }
        onProgress(
          parseInt(String(percent ?? 0), 10),
          event.event as ProgressEvent,
        );
      };

      try {
        const res = await userUploadApi({
          body: {
            file: fileItem.file as Blob,
          },
          signal: controller.signal,
          onUploadProgress,
        });
        onSuccess(res.data as UserUploadResponse);
      } catch (error) {
        onError(error);
      }
    })();
    return {
      abort() {
        controller.abort();
      },
    };
  };
</script>

<style scoped lang="less">
  .arco-card {
    padding: 14px 0 4px 4px;
    border-radius: 4px;
  }
  :deep(.arco-avatar-trigger-icon-button) {
    width: 32px;
    height: 32px;
    line-height: 32px;
    background-color: #e8f3ff;
    .arco-icon-camera {
      margin-top: 8px;
      color: rgb(var(--arcoblue-6));
      font-size: 14px;
    }
  }
</style>
