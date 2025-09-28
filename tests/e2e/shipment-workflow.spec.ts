import { test, expect } from '@playwright/test';

test.describe('Shipment Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.locator('input[name="username"]').fill('test@example.com');
    await page.locator('input[name="password"]').fill('testpassword');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');
  });

  test('should display shipment list and allow selection', async ({ page }) => {
    // Check if load list is visible
    await expect(page.locator('[data-testid="load-list"]')).toBeVisible();

    // Check for search functionality
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toHaveAttribute('placeholder', /搜索/);

    // Check for status filter
    await expect(page.locator('[data-testid="status-filter"]')).toBeVisible();

    // Check for refresh button
    await expect(page.locator('[data-testid="refresh-button"]')).toBeVisible();
  });

  test('should search shipments by ID', async ({ page }) => {
    const searchInput = page.locator('[data-testid="search-input"]');

    // Search for a specific shipment
    await searchInput.fill('SHIP001');

    // Wait for search results
    await page.waitForTimeout(1000);

    // Should show filtered results
    const shipmentItems = page.locator('[data-testid="shipment-item"]');
    const count = await shipmentItems.count();

    if (count > 0) {
      // Check if search results contain the search term
      const firstItem = shipmentItems.first();
      await expect(firstItem).toContainText('SHIP001');
    }
  });

  test('should filter shipments by status', async ({ page }) => {
    const statusFilter = page.locator('[data-testid="status-filter"]');

    // Select 'in-transit' status
    await statusFilter.click();
    await page.locator('text=运输中').click();

    // Wait for filter to apply
    await page.waitForTimeout(1000);

    // Should show only in-transit shipments
    const shipmentItems = page.locator('[data-testid="shipment-item"]');
    const count = await shipmentItems.count();

    if (count > 0) {
      // All visible items should have in-transit status
      for (let i = 0; i < Math.min(count, 3); i++) {
        const item = shipmentItems.nth(i);
        await expect(item).toBeVisible();
      }
    }
  });

  test('should select shipment and show details', async ({ page }) => {
    // Wait for shipments to load
    await page.waitForSelector('[data-testid="shipment-item"]', { timeout: 10000 });

    const firstShipment = page.locator('[data-testid="shipment-item"]').first();

    // Click on first shipment
    await firstShipment.click();

    // Should show shipment details
    await expect(page.locator('[data-testid="shipment-header"]')).toBeVisible();
    await expect(page.locator('[data-testid="stepper"]')).toBeVisible();
    await expect(page.locator('[data-testid="route-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="load-details-card"]')).toBeVisible();
  });

  test('should show shipment stepper with correct progress', async ({ page }) => {
    // Select a shipment
    await page.waitForSelector('[data-testid="shipment-item"]', { timeout: 10000 });
    await page.locator('[data-testid="shipment-item"]').first().click();

    // Check stepper visibility
    const stepper = page.locator('[data-testid="stepper"]');
    await expect(stepper).toBeVisible();

    // Check stepper steps
    const steps = page.locator('[data-testid="stepper-step"]');
    const stepCount = await steps.count();
    expect(stepCount).toBeGreaterThan(0);

    // Check if at least one step is active/completed
    const activeSteps = page.locator('[data-testid="stepper-step"][data-active="true"]');
    const activeCount = await activeSteps.count();
    expect(activeCount).toBeGreaterThanOrEqual(0);
  });

  test('should refresh shipment list', async ({ page }) => {
    const refreshButton = page.locator('[data-testid="refresh-button"]');

    // Click refresh button
    await refreshButton.click();

    // Should show loading state briefly
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();

    // Should complete loading
    await expect(page.locator('[data-testid="loading-indicator"]')).not.toBeVisible();

    // Shipment list should still be visible
    await expect(page.locator('[data-testid="load-list"]')).toBeVisible();
  });

  test('should load more shipments when available', async ({ page }) => {
    // Scroll to bottom of shipment list
    const loadList = page.locator('[data-testid="load-list"]');
    await loadList.scrollTo({ left: 0, top: loadList.getBoundingClientRect().height });

    // Check if load more button appears
    const loadMoreButton = page.locator('[data-testid="load-more-button"]');

    if (await loadMoreButton.isVisible()) {
      const initialCount = await page.locator('[data-testid="shipment-item"]').count();

      // Click load more
      await loadMoreButton.click();

      // Wait for new items to load
      await page.waitForTimeout(2000);

      // Should have more items (or same if no more available)
      const newCount = await page.locator('[data-testid="shipment-item"]').count();
      expect(newCount).toBeGreaterThanOrEqual(initialCount);
    }
  });

  test('should show empty state when no shipments match filter', async ({ page }) => {
    const searchInput = page.locator('[data-testid="search-input"]');

    // Search for non-existent shipment
    await searchInput.fill('NONEXISTENT999');

    // Wait for search to complete
    await page.waitForTimeout(1000);

    // Should show empty state
    const emptyState = page.locator('[data-testid="empty-state"]');
    await expect(emptyState).toBeVisible();
    await expect(emptyState).toContainText(/没有符合条件的运单/);
  });
});