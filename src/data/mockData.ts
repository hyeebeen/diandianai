import { Load, ChatMessage } from '@/types/logistics';

export const mockLoads: Load[] = [
  {
    id: 'AUG-2930487',
    origin: '上海市',
    destination: '广州市',
    status: 'unassigned',
    date: '3月12日',
    customer: '晨光食品有限公司',
    mode: '整车运输',
    equipment: '冷藏车 -2°C 13米',
    weight: '20,000公斤',
    commodity: '冷冻食品、面粉、干货',
    packingType: '托盘',
    notes: '食品级运输要求。装卸过程中如有任何问题或延误请立即联系调度员小李（24小时）。请勿在未经调度员确认的情况下离开发货方/收货方。进出时间必须准确记录。',
    pickupCoords: [31.2304, 121.4737],
    deliveryCoords: [23.1291, 113.2644],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '浦东新区张江高科技园区祖冲之路899号',
        city: '上海',
        state: '上海市',
        zipCode: '201203',
        date: '3月12日',
        timeWindow: '上午9点 - 下午5点',
        coordinates: [31.2304, 121.4737]
      },
      {
        id: '2',
        type: 'delivery',
        address: '天河区珠江新城花城大道68号',
        city: '广州',
        state: '广东省',
        zipCode: '510623',
        date: '3月15日',
        timeWindow: '上午9点 - 下午5点',
        coordinates: [23.1291, 113.2644]
      }
    ]
  },
  {
    id: 'AUG-2930488',
    origin: '北京市',
    destination: '深圳市',
    status: 'assigned',
    date: '3月12日',
    customer: '华辰汽配有限公司',
    mode: '整车运输',
    equipment: '厢式货车 13米',
    weight: '19,000公斤',
    commodity: '汽车零配件',
    packingType: '托盘',
    notes: '标准干货运输。如有延误请及时通知调度中心。',
    pickupCoords: [39.9042, 116.4074],
    deliveryCoords: [22.5431, 114.0579],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '朝阳区望京街10号望京SOHO塔3',
        city: '北京',
        state: '北京市',
        zipCode: '100102',
        date: '3月13日',
        timeWindow: '上午8点 - 下午4点',
        coordinates: [39.9042, 116.4074]
      },
      {
        id: '2',
        type: 'delivery',
        address: '南山区科技园南区深圳湾科技生态园',
        city: '深圳',
        state: '广东省',
        zipCode: '518057',
        date: '3月16日',
        timeWindow: '上午9点 - 下午5点',
        coordinates: [22.5431, 114.0579]
      }
    ]
  },
  {
    id: 'AUG-2930489',
    origin: '杭州市',
    destination: '成都市',
    status: 'in-transit',
    date: '3月12日',
    badges: ['追踪监控'],
    customer: '科技数码有限公司',
    mode: '整车运输',
    equipment: '厢式货车 13米',
    weight: '17,000公斤',
    commodity: '电子产品',
    packingType: '木箱',
    notes: '高价值货物。需要GPS全程跟踪。',
    pickupCoords: [30.2741, 120.1551],
    deliveryCoords: [30.5728, 104.0668],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '西湖区文三路269号',
        city: '杭州',
        state: '浙江省',
        zipCode: '310012',
        date: '3月12日',
        timeWindow: '上午9点 - 下午5点',
        coordinates: [30.2741, 120.1551]
      },
      {
        id: '2',
        type: 'delivery',
        address: '高新区天府大道中段666号',
        city: '成都',
        state: '四川省',
        zipCode: '610041',
        date: '3月15日',
        timeWindow: '上午9点 - 下午5点',
        coordinates: [30.5728, 104.0668]
      }
    ]
  },
  {
    id: 'AUG-2930490',
    origin: '南京市',
    destination: '南京市',
    status: 'dispatched',
    date: '3月12日',
    badges: ['美食城'],
    customer: '餐饮供应链公司',
    mode: '零担运输',
    equipment: '小型货车',
    weight: '6,800公斤',
    commodity: '餐饮用品',
    packingType: '纸箱',
    notes: '市内多点配送。请与调度员确认最优配送路线。',
    pickupCoords: [32.0603, 118.7969],
    deliveryCoords: [32.0603, 118.7969],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '建邺区江东中路369号',
        city: '南京',
        state: '江苏省',
        zipCode: '210019',
        date: '3月13日',
        timeWindow: '上午6点 - 下午2点',
        coordinates: [32.0603, 118.7969]
      },
      {
        id: '2',
        type: 'delivery',
        address: '鼓楼区中山路18号',
        city: '南京',
        state: '江苏省',
        zipCode: '210008',
        date: '3月13日',
        timeWindow: '上午10点 - 下午6点',
        coordinates: [32.0603, 118.7969]
      }
    ]
  },
  {
    id: 'AUG-2930491',
    origin: '武汉市',
    destination: '长沙市',
    status: 'dispatched',
    date: '3月12日',
    customer: '百货连锁集团',
    mode: '整车运输',
    equipment: '厢式货车 12米',
    weight: '18,000公斤',
    commodity: '百货商品',
    packingType: '混装',
    notes: '需要周末配送。请提前24小时通知收货方。',
    pickupCoords: [30.5928, 114.3055],
    deliveryCoords: [28.2282, 112.9388],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '武昌区中南路99号',
        city: '武汉',
        state: '湖北省',
        zipCode: '430071',
        date: '3月14日',
        timeWindow: '上午7点 - 下午3点',
        coordinates: [30.5928, 114.3055]
      },
      {
        id: '2',
        type: 'delivery',
        address: '开福区湘江大道188号',
        city: '长沙',
        state: '湖南省',
        zipCode: '410005',
        date: '3月15日',
        timeWindow: '上午8点 - 下午4点',
        coordinates: [28.2282, 112.9388]
      }
    ]
  },
  {
    id: 'AUG-2930492',
    origin: '天津市',
    destination: '青岛市',
    status: 'at-pickup',
    date: '3月12日',
    badges: ['宜家家居'],
    customer: '家具生活有限公司',
    mode: '整车运输',
    equipment: '搬家专用车 8米',
    weight: '11,300公斤',
    commodity: '家用家具',
    packingType: '包装膜',
    notes: '需要提供白手套服务。请小心搬运。',
    pickupCoords: [39.1042, 117.2009],
    deliveryCoords: [36.0671, 120.3826],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '和平区南京路128号',
        city: '天津',
        state: '天津市',
        zipCode: '300041',
        date: '3月12日',
        timeWindow: '上午8点 - 下午6点',
        coordinates: [39.1042, 117.2009]
      },
      {
        id: '2',
        type: 'delivery',
        address: '市南区香港中路76号',
        city: '青岛',
        state: '山东省',
        zipCode: '266071',
        date: '3月14日',
        timeWindow: '上午9点 - 下午5点',
        coordinates: [36.0671, 120.3826]
      }
    ]
  },
  {
    id: 'AUG-2930493',
    origin: '大连市',
    destination: '沈阳市',
    status: 'loaded',
    date: '3月12日',
    customer: '中石化能源集团',
    mode: '平板运输',
    equipment: '平板车 12米',
    weight: '21,700公斤',  
    commodity: '钢管',
    packingType: '绳索固定',
    notes: '超限货物。高速公路行驶需要护送车辆。',
    pickupCoords: [38.9140, 121.6147],
    deliveryCoords: [41.8057, 123.4315],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '甘井子区华南广场1号',
        city: '大连',
        state: '辽宁省',
        zipCode: '116033',
        date: '3月13日',
        timeWindow: '上午6点 - 下午2点',
        coordinates: [38.9140, 121.6147]
      },
      {
        id: '2',
        type: 'delivery',
        address: '沈河区青年大街185号',
        city: '沈阳',
        state: '辽宁省',
        zipCode: '110013',
        date: '3月15日',
        timeWindow: '上午8点 - 下午4点',
        coordinates: [41.8057, 123.4315]
      }
    ]
  }
];

export const mockChatMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'system',
    content: '早上好！点点精灵正在处理过去30天的货物追踪与跟踪工作。',
    timestamp: '3月11日 上午9:51'
  },
  {
    id: '2',
    role: 'human',
    content: '查看记录',
    timestamp: '3月11日 上午9:51'
  },
  {
    id: '3',
    role: 'human',
    content: '很好！',
    timestamp: '3月11日 上午9:51'
  },
  {
    id: '4',
    role: 'agent',
    content: '我已经尝试联系小李两次，但都没能接通。我将联系调度员。请提供他们的联系方式？',
    timestamp: '3月12日 上午9:00'
  },
  {
    id: '5',
    role: 'human',
    content: '138-0013-2037',
    timestamp: '3月11日 上午9:51'
  },
  {
    id: '6',
    role: 'agent',
    content: '调度员叫小王。请直接打电话，不要发短信。',
    timestamp: '2月18日 上午9:51'
  },
  {
    id: '7',
    role: 'system',
    content: '知识库已更新',
    timestamp: '2月18日 上午9:51'
  },
  {
    id: '8',
    role: 'agent',
    content: '正在联系小王...',
    timestamp: '2月18日 上午9:51'
  },
  {
    id: '9',
    role: 'system',
    content: '',
    timestamp: '',
    attachments: [{
      id: 'call-1',
      type: 'call',
      name: '点点精灵 <> 小王，调度员',
      duration: '0:10',
      participants: ['点点精灵', '小王']
    }]
  }
];