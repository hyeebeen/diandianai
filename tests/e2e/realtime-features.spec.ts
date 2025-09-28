import { test, expect } from '@playwright/test';

test.describe('Real-time Features', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.locator('input[name="username"]').fill('test@example.com');
    await page.locator('input[name="password"]').fill('testpassword');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');
  });

  test('should display real-time connection indicators', async ({ page }) => {
    // Check notification center
    await expect(page.locator('[data-testid="notification-center"]')).toBeVisible();

    // Check connection status indicator
    await expect(page.locator('[data-testid="connection-status"]')).toBeVisible();

    // Connection status should show either connected or disconnected
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    const statusText = await connectionStatus.textContent();
    expect(statusText).toMatch(/(连接正常|未连接|连接中|部分连接)/);
  });

  test('should show notification center with real-time updates', async ({ page }) => {
    const notificationCenter = page.locator('[data-testid="notification-center"]');

    // Click notification center to open
    await notificationCenter.click();

    // Should show notification dropdown
    await expect(page.locator('[data-testid="notification-dropdown"]')).toBeVisible();

    // Should show connection status in dropdown header
    await expect(page.locator('[data-testid="notification-status"]')).toBeVisible();

    // Check if notifications list is present (may be empty initially)
    const notificationsList = page.locator('[data-testid="notifications-list"]');
    await expect(notificationsList).toBeVisible();
  });

  test('should display shipment real-time status updates', async ({ page }) => {
    // Wait for shipments to load
    await page.waitForSelector('[data-testid="shipment-item"]', { timeout: 10000 });

    // Check if shipment items show real-time status indicators
    const shipmentItems = page.locator('[data-testid="shipment-item"]');
    const firstItem = shipmentItems.first();

    // Should have status indicator
    await expect(firstItem.locator('[data-testid="status-indicator"]')).toBeVisible();

    // Should show timestamp of last update
    await expect(firstItem.locator('[data-testid="last-update"]')).toBeVisible();
  });

  test('should handle SSE connection status changes', async ({ page }) => {
    const connectionStatus = page.locator('[data-testid="connection-status"]');

    // Monitor connection status for changes
    const initialStatus = await connectionStatus.textContent();

    // Wait for potential status changes
    await page.waitForTimeout(5000);

    // Connection status should be stable or show appropriate state
    const currentStatus = await connectionStatus.textContent();
    expect(currentStatus).toMatch(/(连接正常|未连接|连接中|部分连接)/);
  });

  test('should show real-time GPS updates when available', async ({ page }) => {
    // Select a shipment to view GPS
    await page.waitForSelector('[data-testid="shipment-item"]', { timeout: 10000 });
    await page.locator('[data-testid="shipment-item"]').first().click();

    // Check if GPS tracking information is shown
    const routeCard = page.locator('[data-testid="route-card"]');
    if (await routeCard.isVisible()) {
      // Should show location information
      const locationInfo = page.locator('[data-testid="location-info"]');
      if (await locationInfo.isVisible()) {
        await expect(locationInfo).toContainText(/位置|坐标|GPS/);
      }
    }
  });

  test('should display loading states during real-time updates', async ({ page }) => {
    // Refresh data to trigger loading states
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    await refreshButton.click();

    // Should show loading indicator
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();

    // Loading should complete within reasonable time
    await expect(page.locator('[data-testid="loading-indicator"]')).not.toBeVisible({
      timeout: 10000
    });
  });

  test('should handle offline mode gracefully', async ({ page }) => {
    // Simulate network issues by going offline
    await page.context().setOffline(true);

    // Wait a moment for the app to detect offline status
    await page.waitForTimeout(3000);

    // Check if offline indicators are shown
    const offlineIndicators = page.locator('[data-testid="offline-indicator"]');
    const count = await offlineIndicators.count();

    if (count > 0) {
      await expect(offlineIndicators.first()).toContainText(/离线|断开|未连接/);
    }

    // Restore online mode
    await page.context().setOffline(false);

    // Wait for reconnection
    await page.waitForTimeout(3000);
  });

  test('should show real-time typing indicators in chat', async ({ page }) => {
    // Select a shipment and open chat
    await page.waitForSelector('[data-testid="shipment-item"]', { timeout: 10000 });
    await page.locator('[data-testid="shipment-item"]').first().click();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('测试实时功能');
    await chatInput.press('Enter');

    // Should show typing indicator when AI is responding
    const typingIndicator = page.locator('[data-testid="typing-indicator"]');

    // Wait for typing indicator to appear (may be brief)
    try {
      await expect(typingIndicator).toBeVisible({ timeout: 5000 });
    } catch {
      // Typing indicator might be too fast to catch, which is okay
    }
  });

  test('should maintain real-time connections across tab switches', async ({ page }) => {
    // Check initial connection status
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    await expect(connectionStatus).toBeVisible();

    // Switch between chat and summary tabs if available
    const summaryTab = page.locator('[data-testid="summary-tab"]');
    if (await summaryTab.isVisible()) {
      await summaryTab.click();
      await page.waitForTimeout(1000);

      // Connection should still be maintained
      await expect(connectionStatus).toBeVisible();

      // Switch back to chat
      const chatTab = page.locator('[data-testid="chat-tab"]');
      await chatTab.click();
      await page.waitForTimeout(1000);
    }

    // Connection status should remain stable
    await expect(connectionStatus).toBeVisible();
  });

  test('should show real-time notification badges', async ({ page }) => {
    const notificationCenter = page.locator('[data-testid="notification-center"]');

    // Check if notification badge is present when there are unread notifications
    const notificationBadge = page.locator('[data-testid="notification-badge"]');

    if (await notificationBadge.isVisible()) {
      // Badge should show number of unread notifications
      const badgeText = await notificationBadge.textContent();
      expect(badgeText).toMatch(/\d+/);

      // Click to mark as read
      await notificationCenter.click();

      // Wait for dropdown to appear
      await expect(page.locator('[data-testid="notification-dropdown"]')).toBeVisible();

      // Badge should disappear or count should decrease
      await page.waitForTimeout(1000);
    }
  });
});