import { test, expect } from '@playwright/test';

test.describe('Load Testing', () => {
  const API_BASE_URL = 'http://localhost:8000';
  const CONCURRENT_USERS = {
    LOW: 10,      // 10 concurrent users
    MEDIUM: 50,   // 50 concurrent users
    HIGH: 100,    // 100 concurrent users
    STRESS: 200,  // 200 concurrent users for stress testing
  };

  const LOAD_TEST_DURATION = 30000; // 30 seconds
  const REQUEST_INTERVAL = 1000;    // 1 second between requests

  let authTokens: string[] = [];

  test.beforeAll(async ({ request }) => {
    // Create multiple auth tokens for load testing
    console.log('Creating auth tokens for load testing...');

    for (let i = 0; i < CONCURRENT_USERS.STRESS; i++) {
      try {
        const response = await request.post(`${API_BASE_URL}/api/auth/login`, {
          data: {
            username: 'test@example.com',
            password: 'testpassword'
          }
        });

        if (response.ok()) {
          const data = await response.json();
          authTokens.push(data.access_token);
        }
      } catch (error) {
        console.warn(`Failed to create auth token ${i}:`, error);
      }
    }

    console.log(`Created ${authTokens.length} auth tokens`);
  });

  test('should handle low concurrent load (10 users)', async ({ request }) => {
    const concurrentUsers = CONCURRENT_USERS.LOW;
    const userTokens = authTokens.slice(0, concurrentUsers);

    console.log(`Starting load test with ${concurrentUsers} concurrent users...`);

    const results = await runLoadTest(request, userTokens, 10000); // 10 seconds

    // Analysis
    const successRate = (results.successful / results.total) * 100;
    const averageResponseTime = results.totalResponseTime / results.successful;

    console.log(`Load Test Results (${concurrentUsers} users):`);
    console.log(`- Total requests: ${results.total}`);
    console.log(`- Successful: ${results.successful}`);
    console.log(`- Failed: ${results.failed}`);
    console.log(`- Success rate: ${successRate.toFixed(2)}%`);
    console.log(`- Average response time: ${averageResponseTime.toFixed(2)}ms`);

    // Assertions
    expect(successRate).toBeGreaterThan(95); // At least 95% success rate
    expect(averageResponseTime).toBeLessThan(2000); // Under 2 seconds average
  });

  test('should handle medium concurrent load (50 users)', async ({ request }) => {
    const concurrentUsers = CONCURRENT_USERS.MEDIUM;
    const userTokens = authTokens.slice(0, concurrentUsers);

    console.log(`Starting load test with ${concurrentUsers} concurrent users...`);

    const results = await runLoadTest(request, userTokens, 20000); // 20 seconds

    const successRate = (results.successful / results.total) * 100;
    const averageResponseTime = results.totalResponseTime / results.successful;

    console.log(`Load Test Results (${concurrentUsers} users):`);
    console.log(`- Total requests: ${results.total}`);
    console.log(`- Successful: ${results.successful}`);
    console.log(`- Failed: ${results.failed}`);
    console.log(`- Success rate: ${successRate.toFixed(2)}%`);
    console.log(`- Average response time: ${averageResponseTime.toFixed(2)}ms`);

    expect(successRate).toBeGreaterThan(90); // At least 90% success rate
    expect(averageResponseTime).toBeLessThan(3000); // Under 3 seconds average
  });

  test('should handle high concurrent load (100 users)', async ({ request }) => {
    const concurrentUsers = CONCURRENT_USERS.HIGH;
    const userTokens = authTokens.slice(0, concurrentUsers);

    console.log(`Starting load test with ${concurrentUsers} concurrent users...`);

    const results = await runLoadTest(request, userTokens, LOAD_TEST_DURATION);

    const successRate = (results.successful / results.total) * 100;
    const averageResponseTime = results.totalResponseTime / results.successful;

    console.log(`Load Test Results (${concurrentUsers} users):`);
    console.log(`- Total requests: ${results.total}`);
    console.log(`- Successful: ${results.successful}`);
    console.log(`- Failed: ${results.failed}`);
    console.log(`- Success rate: ${successRate.toFixed(2)}%`);
    console.log(`- Average response time: ${averageResponseTime.toFixed(2)}ms`);

    expect(successRate).toBeGreaterThan(85); // At least 85% success rate
    expect(averageResponseTime).toBeLessThan(5000); // Under 5 seconds average
  });

  test('should survive stress testing (200 users)', async ({ request }) => {
    const concurrentUsers = CONCURRENT_USERS.STRESS;
    const userTokens = authTokens.slice(0, concurrentUsers);

    console.log(`Starting stress test with ${concurrentUsers} concurrent users...`);

    const results = await runLoadTest(request, userTokens, LOAD_TEST_DURATION);

    const successRate = (results.successful / results.total) * 100;
    const averageResponseTime = results.totalResponseTime / results.successful;

    console.log(`Stress Test Results (${concurrentUsers} users):`);
    console.log(`- Total requests: ${results.total}`);
    console.log(`- Successful: ${results.successful}`);
    console.log(`- Failed: ${results.failed}`);
    console.log(`- Success rate: ${successRate.toFixed(2)}%`);
    console.log(`- Average response time: ${averageResponseTime.toFixed(2)}ms`);

    // Stress test allows for more failures but system should not crash
    expect(successRate).toBeGreaterThan(70); // At least 70% success rate
    expect(results.successful).toBeGreaterThan(0); // Some requests should succeed
  });

  test('should handle concurrent SSE connections', async ({ page }) => {
    const concurrentConnections = 20;
    const pages: any[] = [];

    console.log(`Testing ${concurrentConnections} concurrent SSE connections...`);

    try {
      // Create multiple browser contexts for concurrent connections
      for (let i = 0; i < concurrentConnections; i++) {
        const newPage = await page.context().newPage();

        // Login each page
        await newPage.goto('/login');
        await newPage.locator('input[name="username"]').fill('test@example.com');
        await newPage.locator('input[name="password"]').fill('testpassword');
        await newPage.locator('button[type="submit"]').click();

        // Wait for dashboard to load
        await newPage.waitForURL('/');

        pages.push(newPage);
      }

      // Wait for all connections to establish
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Verify connections are working
      let workingConnections = 0;
      for (const testPage of pages) {
        try {
          const connectionStatus = testPage.locator('[data-testid="connection-status"]');
          if (await connectionStatus.isVisible()) {
            const statusText = await connectionStatus.textContent();
            if (statusText?.includes('连接') || statusText?.includes('正常')) {
              workingConnections++;
            }
          }
        } catch (error) {
          // Connection might have failed
        }
      }

      console.log(`Working SSE connections: ${workingConnections}/${concurrentConnections}`);

      // At least 80% of connections should work
      expect(workingConnections).toBeGreaterThan(concurrentConnections * 0.8);

    } finally {
      // Cleanup
      for (const testPage of pages) {
        try {
          await testPage.close();
        } catch (error) {
          // Ignore cleanup errors
        }
      }
    }
  });

  test('should maintain performance under sustained load', async ({ request }) => {
    const concurrentUsers = 25;
    const userTokens = authTokens.slice(0, concurrentUsers);
    const sustainedDuration = 60000; // 1 minute

    console.log(`Starting sustained load test for ${sustainedDuration/1000} seconds...`);

    const phaseResults: any[] = [];
    const phaseLength = 15000; // 15 second phases
    const phases = Math.ceil(sustainedDuration / phaseLength);

    for (let phase = 0; phase < phases; phase++) {
      console.log(`Phase ${phase + 1}/${phases}`);

      const results = await runLoadTest(request, userTokens, phaseLength);
      phaseResults.push(results);

      // Brief pause between phases
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Analyze performance degradation
    const successRates = phaseResults.map(r => (r.successful / r.total) * 100);
    const avgResponseTimes = phaseResults.map(r => r.totalResponseTime / r.successful);

    console.log('Sustained Load Test Results:');
    phaseResults.forEach((result, index) => {
      console.log(`Phase ${index + 1}: ${successRates[index].toFixed(2)}% success, ${avgResponseTimes[index].toFixed(2)}ms avg`);
    });

    // Performance should not degrade significantly over time
    const firstPhaseSuccess = successRates[0];
    const lastPhaseSuccess = successRates[successRates.length - 1];
    const performanceDrop = firstPhaseSuccess - lastPhaseSuccess;

    expect(performanceDrop).toBeLessThan(20); // Less than 20% performance drop
    expect(lastPhaseSuccess).toBeGreaterThan(70); // At least 70% success in final phase
  });

  // Helper function to run load test
  async function runLoadTest(request: any, tokens: string[], duration: number) {
    const endTime = Date.now() + duration;
    const promises: Promise<any>[] = [];
    let requestCount = 0;

    const results = {
      total: 0,
      successful: 0,
      failed: 0,
      totalResponseTime: 0
    };

    // Start concurrent user sessions
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];

      const userSession = async () => {
        while (Date.now() < endTime) {
          const startTime = Date.now();

          try {
            const response = await request.get(`${API_BASE_URL}/api/shipments`, {
              headers: {
                'Authorization': `Bearer ${token}`
              },
              params: {
                page: String(Math.floor(Math.random() * 5) + 1),
                page_size: '10'
              }
            });

            const responseTime = Date.now() - startTime;
            results.total++;

            if (response.ok()) {
              results.successful++;
              results.totalResponseTime += responseTime;
            } else {
              results.failed++;
            }

          } catch (error) {
            results.total++;
            results.failed++;
          }

          // Wait before next request
          await new Promise(resolve => setTimeout(resolve, REQUEST_INTERVAL + Math.random() * 500));
        }
      };

      promises.push(userSession());
    }

    // Wait for all user sessions to complete
    await Promise.allSettled(promises);

    return results;
  }
});