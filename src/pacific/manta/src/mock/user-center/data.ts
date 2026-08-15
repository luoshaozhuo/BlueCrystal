import Mock from 'mockjs';
import defaultAvatar from '@/assets/images/default-avatar.svg';

const contributors = [
  {
    name: '秦臻宇',
    email: 'qingzhenyu@arco.design',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/a8c8cdb109cb051163646151a4a5083b.png~tplv-uwbnlip3yd-webp.webp',
  },
  {
    name: '于涛',
    email: 'yuebao@arco.design',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/a8c8cdb109cb051163646151a4a5083b.png~tplv-uwbnlip3yd-webp.webp',
  },
  {
    name: '宁波',
    email: 'ningbo@arco.design',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/3ee5f13fb09879ecb5185e440cef6eb9.png~tplv-uwbnlip3yd-webp.webp',
  },
  {
    name: '郑曦月',
    email: 'zhengxiyue@arco.design',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/8361eeb82904210b4f55fab888fe8416.png~tplv-uwbnlip3yd-webp.webp',
  },
  {
    name: '宁波',
    email: 'ningbo@arco.design',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/3ee5f13fb09879ecb5185e440cef6eb9.png~tplv-uwbnlip3yd-webp.webp',
  },
];

const projectUnits = [
  {
    name: '企业级产品设计系统',
    description: 'Arco Design System',
  },
  {
    name: '火山引擎智能应用',
    description: 'The Volcano Engine',
  },
  {
    name: 'OCR文本识别',
    description: 'OCR text recognition',
  },
  {
    name: '内容资源管理',
    description: 'Content resource management ',
  },
  {
    name: '今日头条内容管理',
    description: 'Toutiao content management',
  },
  {
    name: '智能机器人',
    description: 'Intelligent Robot Project',
  },
];

export function createMyProjectListMock() {
  return new Array(6).fill(null).map((_item, index) => ({
    id: index,
    name: projectUnits[index].name,
    description: projectUnits[index].description,
    peopleNumber: Mock.Random.natural(10, 1000),
    contributors,
  }));
}

export function createLatestActivityMock() {
  return new Array(7).fill(null).map((_item, index) => ({
    id: index,
    title: '发布了项目 Arco Design System',
    description: '企业级产品设计系统',
    avatar: defaultAvatar,
  }));
}

export function createProjectAndTeamListMock() {
  return [
    { id: 1, content: '他创建的项目' },
    { id: 2, content: '他参与的项目' },
    { id: 3, content: '他创建的团队' },
    { id: 4, content: '他加入的团队' },
  ];
}

export function createMyTeamListMock() {
  return [
    {
      id: 1,
      avatar:
        '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/a8c8cdb109cb051163646151a4a5083b.png~tplv-uwbnlip3yd-webp.webp',
      name: '火山引擎智能应用团队',
      peopleNumber: Mock.Random.natural(10, 100),
    },
    {
      id: 2,
      avatar:
        '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/3ee5f13fb09879ecb5185e440cef6eb9.png~tplv-uwbnlip3yd-webp.webp',
      name: '企业级产品设计团队',
      peopleNumber: Mock.Random.natural(5000, 6000),
    },
    {
      id: 3,
      avatar:
        '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/3ee5f13fb09879ecb5185e440cef6eb9.png~tplv-uwbnlip3yd-webp.webp',
      name: '前端/UE小分队',
      peopleNumber: Mock.Random.natural(10, 5000),
    },
    {
      id: 4,
      avatar:
        '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/8361eeb82904210b4f55fab888fe8416.png~tplv-uwbnlip3yd-webp.webp',
      name: '内容识别插件小分队',
      peopleNumber: Mock.Random.natural(10, 100),
    },
  ];
}

export function createCertificationMock() {
  return {
    enterpriseInfo: {
      accountType: '企业账号',
      status: 0,
      time: '2018-10-22 14:53:12',
      legalPerson: '李**',
      certificateType: '中国身份证',
      authenticationNumber: '130************123',
      enterpriseName: '低调有实力的企业',
      enterpriseCertificateType: '企业营业执照',
      organizationCode: '7*******9',
    },
    record: [
      {
        certificationType: 1,
        certificationContent: '企业实名认证，法人姓名：李**',
        status: 0,
        time: '2021-02-28 10:30:50',
      },
      {
        certificationType: 1,
        certificationContent: '企业实名认证，法人姓名：李**',
        status: 1,
        time: '2020-05-13 08:00:00',
      },
    ],
  };
}
