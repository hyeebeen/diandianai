import { test, expect } from '@playwright/test';

test.describe('API Performance Tests', () => {
  const API_BASE_URL = 'http://localhost:8000';
  const PERFORMANCE_THRESHOLDS = {
    LOGIN: 2000,           // 2 seconds for login
    SHIPMENT_LIST: 1500,   // 1.5 seconds for shipment list
    SHIPMENT_DETAIL: 1000, // 1 second for single shipment
    GPS_DATA: 800,         // 800ms for GPS data
    AI_RESPONSE: 5000,     // 5 seconds for AI response
    SEARCH: 1000,          // 1 second for search
  };

  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // Authenticate once for all tests
    const loginResponse = await request.post(`${API_BASE_URL}/api/auth/login`, {
      data: {
        username: 'test@example.com',
        password: 'testpassword'
      }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    authToken = loginData.access_token;
  });

  test('should authenticate within acceptable time', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.post(`${API_BASE_URL}/api/auth/login`, {
      data: {
        username: 'test@example.com',
        password: 'testpassword'
      }
    });

    const responseTime = Date.now() - startTime;

    expect(response.ok()).toBeTruthy();
    expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.LOGIN);

    console.log(`Login API response time: ${responseTime}ms`);
  });

  test('should load shipment list within acceptable time', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.get(`${API_BASE_URL}/api/shipments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      params: {
        page: '1',
        page_size: '20'
      }
    });

    const responseTime = Date.now() - startTime;

    expect(response.ok()).toBeTruthy();
    expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.SHIPMENT_LIST);

    const data = await response.json();
    expect(data.items).toBeDefined();
    expect(Array.isArray(data.items)).toBeTruthy();

    console.log(`Shipment list API response time: ${responseTime}ms`);
  });

  test('should load shipment details within acceptable time', async ({ request }) => {
    // First get a shipment ID
    const listResponse = await request.get(`${API_BASE_URL}/api/shipments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      params: { page: '1', page_size: '1' }
    });

    const listData = await listResponse.json();
    if (listData.items && listData.items.length > 0) {
      const shipmentId = listData.items[0].id;

      const startTime = Date.now();

      const response = await request.get(`${API_BASE_URL}/api/shipments/${shipmentId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      const responseTime = Date.now() - startTime;

      expect(response.ok()).toBeTruthy();
      expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.SHIPMENT_DETAIL);

      console.log(`Shipment detail API response time: ${responseTime}ms`);
    } else {
      test.skip('No shipments available for detail test');
    }
  });

  test('should load GPS data within acceptable time', async ({ request }) => {
    // Get active shipments first
    const listResponse = await request.get(`${API_BASE_URL}/api/gps/active-shipments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (listResponse.ok()) {
      const shipments = await listResponse.json();

      if (shipments.length > 0) {
        const shipmentId = shipments[0].id;

        const startTime = Date.now();

        const response = await request.get(`${API_BASE_URL}/api/gps/realtime/${shipmentId}`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });

        const responseTime = Date.now() - startTime;

        // GPS data might not exist, but API should respond quickly
        expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.GPS_DATA);

        console.log(`GPS data API response time: ${responseTime}ms`);
      }
    }
  });

  test('should perform search within acceptable time', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.get(`${API_BASE_URL}/api/shipments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      params: {
        search: 'SHIP',
        page: '1',
        page_size: '10'
      }
    });

    const responseTime = Date.now() - startTime;

    expect(response.ok()).toBeTruthy();
    expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.SEARCH);

    console.log(`Search API response time: ${responseTime}ms`);
  });

  test('should handle AI conversation creation within acceptable time', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.post(`${API_BASE_URL}/api/ai/conversations`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        context_type: 'shipment',
        context_id: 'test-shipment',
        metadata: {
          user_id: 'test-user'
        }
      }
    });

    const responseTime = Date.now() - startTime;

    expect(response.ok()).toBeTruthy();
    expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.AI_RESPONSE);

    console.log(`AI conversation creation response time: ${responseTime}ms`);
  });

  test('should handle multiple concurrent requests efficiently', async ({ request }) => {
    const concurrentRequests = 5;
    const promises = [];

    const startTime = Date.now();

    // Create multiple concurrent requests
    for (let i = 0; i < concurrentRequests; i++) {
      const promise = request.get(`${API_BASE_URL}/api/shipments`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        params: {
          page: String(i + 1),
          page_size: '5'
        }
      });
      promises.push(promise);
    }

    // Wait for all requests to complete
    const responses = await Promise.all(promises);
    const totalTime = Date.now() - startTime;

    // All requests should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });

    // Average response time should be reasonable
    const averageTime = totalTime / concurrentRequests;
    expect(averageTime).toBeLessThan(PERFORMANCE_THRESHOLDS.SHIPMENT_LIST * 2);

    console.log(`Concurrent requests total time: ${totalTime}ms, average: ${averageTime}ms`);
  });

  test('should handle pagination efficiently', async ({ request }) => {
    const pages = [1, 2, 3];
    const times: number[] = [];

    for (const page of pages) {
      const startTime = Date.now();

      const response = await request.get(`${API_BASE_URL}/api/shipments`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        params: {
          page: String(page),
          page_size: '10'
        }
      });

      const responseTime = Date.now() - startTime;
      times.push(responseTime);

      expect(response.ok()).toBeTruthy();
      expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.SHIPMENT_LIST);
    }

    const averageTime = times.reduce((a, b) => a + b, 0) / times.length;
    console.log(`Pagination average response time: ${averageTime}ms`);

    // Response times should be consistent across pages
    const maxTime = Math.max(...times);
    const minTime = Math.min(...times);
    const variation = maxTime - minTime;

    // Variation should not be too large (within 500ms)
    expect(variation).toBeLessThan(500);
  });

  test('should handle filtering efficiently', async ({ request }) => {
    const filters = [
      { status: 'pending' },
      { status: 'in-transit' },
      { status: 'delivered' }
    ];

    for (const filter of filters) {
      const startTime = Date.now();

      const response = await request.get(`${API_BASE_URL}/api/shipments`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        params: {
          ...filter,
          page: '1',
          page_size: '10'
        }
      });

      const responseTime = Date.now() - startTime;

      expect(response.ok()).toBeTruthy();
      expect(responseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.SHIPMENT_LIST);

      console.log(`Filter ${JSON.stringify(filter)} response time: ${responseTime}ms`);
    }
  });

  test('should validate response sizes are reasonable', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/shipments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      params: {
        page: '1',
        page_size: '20'
      }
    });

    expect(response.ok()).toBeTruthy();

    const responseText = await response.text();
    const responseSize = new Blob([responseText]).size;

    // Response should not be excessively large (under 1MB for 20 items)
    expect(responseSize).toBeLessThan(1024 * 1024);

    console.log(`Response size for 20 shipments: ${responseSize} bytes`);

    // JSON should be valid and properly structured
    const data = JSON.parse(responseText);
    expect(data.items).toBeDefined();
    expect(data.total).toBeDefined();
    expect(data.page).toBeDefined();
    expect(data.page_size).toBeDefined();
  });
});