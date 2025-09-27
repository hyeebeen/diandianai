-- 物流管理系统数据库架构
-- 请在 Supabase 项目的 SQL 编辑器中运行此脚本

-- 创建运单表
CREATE TABLE IF NOT EXISTS loads (
  id TEXT PRIMARY KEY,
  origin_city TEXT NOT NULL,
  destination_city TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('unassigned', 'assigned', 'dispatched', 'in-transit', 'at-pickup', 'loaded', 'delivered')),
  date TEXT NOT NULL,
  customer TEXT NOT NULL,
  vehicle TEXT NOT NULL,
  driver TEXT NOT NULL,
  weight TEXT NOT NULL,
  cargo_type TEXT NOT NULL,
  temperature_control TEXT,
  loading_notes TEXT,
  pickup_address TEXT NOT NULL,
  pickup_lat DECIMAL NOT NULL,
  pickup_lng DECIMAL NOT NULL,
  delivery_address TEXT NOT NULL,
  delivery_lat DECIMAL NOT NULL,
  delivery_lng DECIMAL NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建聊天消息表
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  load_id TEXT REFERENCES loads(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('human', 'agent', 'system')),
  content TEXT NOT NULL,
  timestamp TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 插入初始运单数据
INSERT INTO loads (
  id, origin_city, destination_city, status, date, customer, vehicle, driver, 
  weight, cargo_type, temperature_control, loading_notes, pickup_address, 
  pickup_lat, pickup_lng, delivery_address, delivery_lat, delivery_lng
) VALUES 
('LD-2024-001', '上海', '北京', 'assigned', '2024-03-15', '顺丰速运', '解放J6P 6×4牵引车', '张师傅', '15.2吨', '电子产品', '常温运输', '轻拿轻放，防潮防震', '上海市浦东新区张江高科技园区', 31.2304, 121.5570, '北京市朝阳区望京SOHO', 39.9950, 116.4765),
('LD-2024-002', '深圳', '成都', 'in-transit', '2024-03-14', '京东物流', '欧曼EST 4×2载货车', '李师傅', '8.5吨', '服装纺织', NULL, '注意防水，分层堆放', '深圳市南山区科技园', 22.5431, 114.0579, '成都市高新区天府软件园', 30.5728, 104.0668),
('LD-2024-003', '广州', '杭州', 'delivered', '2024-03-13', '德邦快递', '福田欧马可S3', '王师傅', '5.8吨', '食品饮料', '冷链运输 (2-8°C)', '保持冷链完整，及时配送', '广州市天河区珠江新城', 23.1167, 113.3333, '杭州市滨江区网商路', 30.2084, 120.2056),
('LD-2024-004', '武汉', '西安', 'dispatched', '2024-03-16', '中通快递', '东风天龙KL重卡', '赵师傅', '12.0吨', '机械设备', '常温运输', '重型货物，注意捆绑', '武汉市东湖高新区光谷广场', 30.5872, 114.3049, '西安市高新区科技路', 34.2317, 108.9204),
('LD-2024-005', '南京', '重庆', 'unassigned', '2024-03-17', '圆通速递', '待分配', '待分配', '6.2吨', '日用百货', '常温运输', '易碎物品较多，小心装卸', '南京市建邺区河西新城', 32.0461, 118.7697, '重庆市渝北区两江新区', 29.7256, 106.6221)
ON CONFLICT (id) DO NOTHING;

-- 插入聊天消息数据
INSERT INTO chat_messages (load_id, role, content, timestamp) VALUES 
('LD-2024-002', 'system', '运单 LD-2024-002 已分配给李师傅，正在前往取货点', '09:30'),
('LD-2024-002', 'agent', '您好！我是智能助手小智。运单 LD-2024-002 目前正在运输中，预计今晚8点到达成都。有什么需要我帮您查询的吗？', '10:15'),
('LD-2024-002', 'human', '请问货物运输过程中需要注意什么？', '10:16'),
('LD-2024-002', 'agent', '根据运单信息，这批服装纺织品需要注意防水和分层堆放。李师傅已经按要求进行装载，车辆配备了防雨篷布。运输路线已优化，避开了降雨区域。', '10:17'),
('LD-2024-002', 'system', '车辆GPS信号正常，当前位置：湖北省荆州市', '11:45')
ON CONFLICT DO NOTHING;

-- 启用RLS (Row Level Security)
ALTER TABLE loads ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略 (目前允许所有操作，后续可根据需要调整)
DROP POLICY IF EXISTS "Allow all operations on loads" ON loads;
CREATE POLICY "Allow all operations on loads" ON loads FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on chat_messages" ON chat_messages;
CREATE POLICY "Allow all operations on chat_messages" ON chat_messages FOR ALL USING (true);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_loads_updated_at ON loads;
CREATE TRIGGER update_loads_updated_at BEFORE UPDATE ON loads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();