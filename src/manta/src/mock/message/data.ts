export interface MessageItem {
  id: number;
  type: 'message' | 'notice' | 'todo';
  title: string;
  subTitle: string;
  avatar: string;
  content: string;
  time: string;
  messageType?: number;
  status: 0 | 1;
}

const readMessageIds: number[] = [];

const rawMessages = [
  {
    id: 1,
    type: 'message' as const,
    title: '郑曦月',
    subTitle: '的私信',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/8361eeb82904210b4f55fab888fe8416.png~tplv-uwbnlip3yd-webp.webp',
    content: '审批请求已发送，请查收',
    time: '今天 12:30:01',
  },
  {
    id: 2,
    type: 'message' as const,
    title: '宁波',
    subTitle: '的回复',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/3ee5f13fb09879ecb5185e440cef6eb9.png~tplv-uwbnlip3yd-webp.webp',
    content: '此处 bug 已经修复',
    time: '今天 12:30:01',
  },
  {
    id: 3,
    type: 'message' as const,
    title: '宁波',
    subTitle: '的回复',
    avatar:
      '//p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/3ee5f13fb09879ecb5185e440cef6eb9.png~tplv-uwbnlip3yd-webp.webp',
    content: '此处 bug 已经修复',
    time: '今天 12:20:01',
  },
  {
    id: 4,
    type: 'notice' as const,
    title: '续费通知',
    subTitle: '',
    avatar: '',
    content: '您的产品使用期限即将截止，如需继续使用产品请前往购…',
    time: '今天 12:20:01',
    messageType: 3,
  },
  {
    id: 5,
    type: 'notice' as const,
    title: '规则开通成功',
    subTitle: '',
    avatar: '',
    content: '内容屏蔽规则于 2021-12-01 开通成功并生效',
    time: '今天 12:20:01',
    messageType: 1,
  },
  {
    id: 6,
    type: 'todo' as const,
    title: '质检队列变更',
    subTitle: '',
    avatar: '',
    content: '内容质检队列于 2021-12-01 19:50:23 进行变更，请重新…',
    time: '今天 12:20:01',
    messageType: 0,
  },
];

export function getMessageListMock(): MessageItem[] {
  return rawMessages.map((item) => ({
    ...item,
    status: readMessageIds.includes(item.id) ? 1 : 0,
  }));
}

export function markMessagesRead(ids: number[] = []) {
  readMessageIds.push(...ids);
  return true;
}
