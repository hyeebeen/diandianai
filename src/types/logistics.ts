export type LoadStatus = 'unassigned' | 'assigned' | 'dispatched' | 'in-transit' | 'at-pickup' | 'loaded' | 'delivered';

export interface Load {
  id: string;
  origin: string;
  destination: string;
  status: LoadStatus;
  date: string;
  badges?: string[];
  stops: Stop[];
  notes: string;
  customer: string;
  mode: string;
  equipment: string;
  weight: string;
  commodity: string;
  packingType: string;
  pickupCoords: [number, number];
  deliveryCoords: [number, number];
}

export interface Stop {
  id: string;
  type: 'pickup' | 'delivery';
  address: string;
  city: string;
  state: string;
  zipCode: string;
  date: string;
  timeWindow: string;
  coordinates: [number, number];
}

export type MessageRole = 'agent' | 'human' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  attachments?: Attachment[];
}

export interface Attachment {
  id: string;
  type: 'call' | 'document' | 'image';
  name: string;
  duration?: string;
  participants?: string[];
}

export type StepperStep = 'Assignment' | 'Pickup' | 'In transit' | 'Delivery';