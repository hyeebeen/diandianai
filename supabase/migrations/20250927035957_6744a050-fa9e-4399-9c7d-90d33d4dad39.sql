-- Create loads table for logistics management
CREATE TABLE public.loads (
  id TEXT PRIMARY KEY,
  origin_city TEXT NOT NULL,
  destination_city TEXT NOT NULL,
  status TEXT NOT NULL,
  date TEXT NOT NULL,
  customer TEXT NOT NULL,
  vehicle TEXT NOT NULL,
  driver TEXT NOT NULL,
  weight TEXT NOT NULL,
  cargo_type TEXT NOT NULL,
  temperature_control TEXT,
  loading_notes TEXT,
  pickup_address TEXT NOT NULL,
  pickup_lat DOUBLE PRECISION NOT NULL,
  pickup_lng DOUBLE PRECISION NOT NULL,
  delivery_address TEXT NOT NULL,
  delivery_lat DOUBLE PRECISION NOT NULL,
  delivery_lng DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chat_messages table for AI chat functionality
CREATE TABLE public.chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  load_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('human', 'agent', 'system')),
  content TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.loads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policies (allowing all operations for now)
CREATE POLICY "Allow all operations on loads" ON public.loads FOR ALL USING (true);
CREATE POLICY "Allow all operations on chat_messages" ON public.chat_messages FOR ALL USING (true);

-- Insert sample data
INSERT INTO public.loads (id, origin_city, destination_city, status, date, customer, vehicle, driver, weight, cargo_type, temperature_control, loading_notes, pickup_address, pickup_lat, pickup_lng, delivery_address, delivery_lat, delivery_lng) VALUES
('LD-2024-001', '上海', '北京', 'in-transit', '2024-01-15', '顺丰速运', '解放J6P', '张师傅', '15.5吨', '电子产品', '常温', '注意防潮防震', '上海市浦东新区张江高科技园区', 31.2047, 121.5986, '北京市朝阳区CBD核心区', 39.9075, 116.3972),
('LD-2024-002', '广州', '深圳', 'delivered', '2024-01-14', '中通快递', '欧曼GTL', '李师傅', '8.2吨', '服装纺织', '常温', '轻拿轻放', '广州市天河区珠江新城', 23.1291, 113.3241, '深圳市南山区科技园', 22.5431, 113.9351),
('LD-2024-003', '成都', '重庆', 'at-pickup', '2024-01-16', '韵达快递', '陕汽德龙X3000', '王师傅', '12.8吨', '食品饮料', '冷藏', '保持2-8℃', '成都市高新区天府大道', 30.5728, 104.0665, '重庆市渝北区两路', 29.7186, 106.6417),
('LD-2024-004', '杭州', '南京', 'dispatched', '2024-01-17', '申通快递', '福田欧曼EST', '赵师傅', '6.5吨', '医药用品', '常温', '医药专运', '杭州市西湖区文三路', 30.2741, 120.1551, '南京市鼓楼区中山路', 32.0603, 118.7969),
('LD-2024-005', '武汉', '长沙', 'assigned', '2024-01-18', '圆通速递', '一汽解放J7', '孙师傅', '18.3吨', '建材钢铁', '常温', '重货小心', '武汉市洪山区光谷大道', 30.5578, 114.3094, '长沙市岳麓区麓谷大道', 28.2358, 112.8906);

-- Insert sample chat messages
INSERT INTO public.chat_messages (load_id, role, content, timestamp) VALUES
('LD-2024-002', 'system', '运单已送达，客户已签收', '09:30'),
('LD-2024-002', 'agent', '您好！运单LD-2024-002已成功送达深圳科技园，客户已确认签收。如有任何问题请随时联系我。', '09:31');

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_loads_updated_at
  BEFORE UPDATE ON public.loads
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();