/**
 * React hooks for Server-Sent Events (SSE) integration
 * Provides easy-to-use hooks for real-time data subscriptions
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

// 开发环境：定义基本的类型接口，避免导入错误
export interface GPSLocationUpdate {
  vehicle_id: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  speed?: number;
  heading?: number;
}

export interface NotificationUpdate {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  timestamp: string;
  read: boolean;
}

export interface ShipmentStatusUpdate {
  shipment_id: string;
  status: string;
  timestamp: string;
  location?: string;
  notes?: string;
}

export interface AIMessageUpdate {
  message_id: string;
  conversation_id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  typing?: boolean;
}

// 开发环境：简化的SSE服务模拟
const createMockSSEService = () => ({
  setAuthToken: (token: string | null) => {
    console.log('Development mode: Mock SSE service - setting auth token:', !!token);
  },
  subscribeToGPSUpdates: (onUpdate: (update: GPSLocationUpdate) => void, onError: (error: Event) => void) => {
    console.log('Development mode: Mock GPS SSE subscription');
    return () => console.log('Development mode: Unsubscribed from GPS updates');
  },
  subscribeToShipmentUpdates: (onUpdate: (update: ShipmentStatusUpdate) => void, onError: (error: Event) => void) => {
    console.log('Development mode: Mock Shipment SSE subscription');
    return () => console.log('Development mode: Unsubscribed from shipment updates');
  },
  subscribeToNotifications: (onUpdate: (update: NotificationUpdate) => void, onError: (error: Event) => void) => {
    console.log('Development mode: Mock Notifications SSE subscription');
    return () => console.log('Development mode: Unsubscribed from notifications');
  },
  subscribeToAIMessages: (conversationId: string, onUpdate: (update: AIMessageUpdate) => void, onError: (error: Event) => void) => {
    console.log('Development mode: Mock AI Messages SSE subscription for conversation:', conversationId);
    return () => console.log('Development mode: Unsubscribed from AI messages');
  },
  getConnectionStatus: () => ({}),
  disconnectAll: () => {
    console.log('Development mode: Mock SSE disconnectAll');
  }
});

const sseService = createMockSSEService();

/**
 * Hook for subscribing to GPS location updates
 */
export function useGPSUpdates() {
  const { user } = useAuth();
  const [lastUpdate, setLastUpdate] = useState<GPSLocationUpdate | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const handleUpdate = useCallback((update: GPSLocationUpdate) => {
    setLastUpdate(update);
  }, []);

  const handleError = useCallback((error: Event) => {
    console.error('GPS SSE connection error:', error);
    setConnectionStatus('disconnected');
  }, []);

  useEffect(() => {
    if (!user) {
      setConnectionStatus('disconnected');
      return;
    }

    setConnectionStatus('connecting');

    // Update SSE service with current auth token
    sseService.setAuthToken(localStorage.getItem('authToken'));

    // Subscribe to GPS updates
    unsubscribeRef.current = sseService.subscribeToGPSUpdates(
      handleUpdate,
      handleError
    );

    setConnectionStatus('connected');

    // Cleanup on unmount
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
      setConnectionStatus('disconnected');
    };
  }, [user, handleUpdate, handleError]);

  return {
    lastUpdate,
    connectionStatus,
    isConnected: connectionStatus === 'connected'
  };
}

/**
 * Hook for subscribing to shipment status updates
 */
export function useShipmentUpdates() {
  const { user } = useAuth();
  const [lastUpdate, setLastUpdate] = useState<ShipmentStatusUpdate | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const handleUpdate = useCallback((update: ShipmentStatusUpdate) => {
    setLastUpdate(update);
  }, []);

  const handleError = useCallback((error: Event) => {
    console.error('Shipment SSE connection error:', error);
    setConnectionStatus('disconnected');
  }, []);

  useEffect(() => {
    if (!user) {
      setConnectionStatus('disconnected');
      return;
    }

    setConnectionStatus('connecting');
    sseService.setAuthToken(localStorage.getItem('authToken'));

    unsubscribeRef.current = sseService.subscribeToShipmentUpdates(
      handleUpdate,
      handleError
    );

    setConnectionStatus('connected');

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
      setConnectionStatus('disconnected');
    };
  }, [user, handleUpdate, handleError]);

  return {
    lastUpdate,
    connectionStatus,
    isConnected: connectionStatus === 'connected'
  };
}

/**
 * Hook for subscribing to real-time notifications
 */
export function useNotifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<NotificationUpdate[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [unreadCount, setUnreadCount] = useState(0);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const handleNotification = useCallback((notification: NotificationUpdate) => {
    setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep last 50 notifications
    setUnreadCount(prev => prev + 1);
  }, []);

  const markAsRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  const handleError = useCallback((error: Event) => {
    console.error('Notifications SSE connection error:', error);
    setConnectionStatus('disconnected');
  }, []);

  useEffect(() => {
    if (!user) {
      setConnectionStatus('disconnected');
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    setConnectionStatus('connecting');
    sseService.setAuthToken(localStorage.getItem('authToken'));

    unsubscribeRef.current = sseService.subscribeToNotifications(
      handleNotification,
      handleError
    );

    setConnectionStatus('connected');

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
      setConnectionStatus('disconnected');
    };
  }, [user, handleNotification, handleError]);

  return {
    notifications,
    unreadCount,
    connectionStatus,
    isConnected: connectionStatus === 'connected',
    markAsRead,
    clearNotifications
  };
}

/**
 * Hook for subscribing to AI conversation updates
 */
export function useAIMessages(conversationId: string | null) {
  const { user } = useAuth();
  const [messages, setMessages] = useState<AIMessageUpdate[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [isTyping, setIsTyping] = useState(false);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const handleMessage = useCallback((message: AIMessageUpdate) => {
    if (message.typing) {
      setIsTyping(true);
      return;
    }

    setIsTyping(false);
    setMessages(prev => {
      // Check if message already exists to avoid duplicates
      const exists = prev.some(m => m.message_id === message.message_id);
      if (exists) return prev;

      // Add new message in chronological order
      return [...prev, message].sort((a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
    });
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setIsTyping(false);
  }, []);

  const handleError = useCallback((error: Event) => {
    console.error('AI messages SSE connection error:', error);
    setConnectionStatus('disconnected');
    setIsTyping(false);
  }, []);

  useEffect(() => {
    if (!user || !conversationId) {
      setConnectionStatus('disconnected');
      setMessages([]);
      setIsTyping(false);
      return;
    }

    setConnectionStatus('connecting');
    sseService.setAuthToken(localStorage.getItem('authToken'));

    unsubscribeRef.current = sseService.subscribeToAIMessages(
      conversationId,
      handleMessage,
      handleError
    );

    setConnectionStatus('connected');

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
      setConnectionStatus('disconnected');
      setIsTyping(false);
    };
  }, [user, conversationId, handleMessage, handleError]);

  return {
    messages,
    isTyping,
    connectionStatus,
    isConnected: connectionStatus === 'connected',
    clearMessages
  };
}

/**
 * Hook for monitoring overall SSE connection health
 */
export function useSSEStatus() {
  const { user } = useAuth();
  const [connectionStatuses, setConnectionStatuses] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!user) {
      setConnectionStatuses({});
      return;
    }

    const updateStatuses = () => {
      setConnectionStatuses(sseService.getConnectionStatus());
    };

    // Update statuses every 5 seconds
    const interval = setInterval(updateStatuses, 5000);
    updateStatuses(); // Initial update

    return () => {
      clearInterval(interval);
    };
  }, [user]);

  const totalConnections = Object.keys(connectionStatuses).length;
  const openConnections = Object.values(connectionStatuses).filter(status => status === 'open').length;
  const overallHealthy = totalConnections > 0 && openConnections === totalConnections;

  return {
    connectionStatuses,
    totalConnections,
    openConnections,
    overallHealthy
  };
}

/**
 * Custom hook for automatic SSE cleanup on component unmount
 */
export function useSSECleanup() {
  useEffect(() => {
    return () => {
      // Cleanup all SSE connections when the app unmounts
      sseService.disconnectAll();
    };
  }, []);
}