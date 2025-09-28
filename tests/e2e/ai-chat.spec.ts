import { test, expect } from '@playwright/test';

test.describe('AI Chat Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login and select a shipment
    await page.goto('/login');
    await page.locator('input[name="username"]').fill('test@example.com');
    await page.locator('input[name="password"]').fill('testpassword');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');

    // Wait for shipments and select one
    await page.waitForSelector('[data-testid="shipment-item"]', { timeout: 10000 });
    await page.locator('[data-testid="shipment-item"]').first().click();
  });

  test('should display chat panel and interface elements', async ({ page }) => {
    // Check if chat panel is visible
    await expect(page.locator('[data-testid="chat-panel"]')).toBeVisible();

    // Check chat tabs
    await expect(page.locator('[data-testid="chat-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="summary-tab"]')).toBeVisible();

    // Check chat input
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="send-button"]')).toBeVisible();

    // Check for attachment button
    await expect(page.locator('[data-testid="attachment-button"]')).toBeVisible();
  });

  test('should show welcome message when no conversation exists', async ({ page }) => {
    const chatMessages = page.locator('[data-testid="chat-messages"]');
    await expect(chatMessages).toBeVisible();

    // Should show welcome message
    await expect(chatMessages).toContainText(/您好！我是点点精灵/);
    await expect(chatMessages).toContainText(/有什么可以帮助您的吗/);
  });

  test('should send a message and receive response', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // Type a message
    await chatInput.fill('你好，请问这个运单的状态如何？');

    // Send button should be enabled
    await expect(sendButton).toBeEnabled();

    // Send the message
    await sendButton.click();

    // Input should be cleared
    await expect(chatInput).toHaveValue('');

    // Should show user message
    const userMessages = page.locator('[data-testid="user-message"]');
    await expect(userMessages.last()).toContainText('你好，请问这个运单的状态如何？');

    // Should show typing indicator
    await expect(page.locator('[data-testid="typing-indicator"]')).toBeVisible();

    // Wait for AI response (with timeout)
    await page.waitForSelector('[data-testid="ai-message"]', { timeout: 30000 });

    // Should show AI response
    const aiMessages = page.locator('[data-testid="ai-message"]');
    await expect(aiMessages.last()).toBeVisible();

    // Typing indicator should disappear
    await expect(page.locator('[data-testid="typing-indicator"]')).not.toBeVisible();
  });

  test('should handle Enter key to send message', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"]');

    await chatInput.fill('测试消息');

    // Press Enter to send
    await chatInput.press('Enter');

    // Should send the message
    await expect(page.locator('[data-testid="user-message"]')).toContainText('测试消息');
  });

  test('should handle Shift+Enter for new line', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"]');

    await chatInput.fill('第一行');

    // Press Shift+Enter for new line
    await chatInput.press('Shift+Enter');
    await chatInput.type('第二行');

    // Should contain both lines
    const inputValue = await chatInput.inputValue();
    expect(inputValue).toContain('第一行');
    expect(inputValue).toContain('第二行');
  });

  test('should disable send button when input is empty', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // Should be disabled when empty
    await expect(sendButton).toBeDisabled();

    // Type something
    await chatInput.fill('test');
    await expect(sendButton).toBeEnabled();

    // Clear input
    await chatInput.fill('');
    await expect(sendButton).toBeDisabled();
  });

  test('should show connection status indicator', async ({ page }) => {
    const chatTab = page.locator('[data-testid="chat-tab"]');

    // Should show connection status
    const connectionIndicator = page.locator('[data-testid="connection-indicator"]');

    if (await connectionIndicator.isVisible()) {
      // Should be either connected or disconnected
      const isConnected = await connectionIndicator.locator('.bg-green-500').isVisible();
      const isDisconnected = await connectionIndicator.locator('.bg-red-500').isVisible();
      expect(isConnected || isDisconnected).toBeTruthy();
    }
  });

  test('should switch to summary tab and generate summary', async ({ page }) => {
    const summaryTab = page.locator('[data-testid="summary-tab"]');

    // Click summary tab
    await summaryTab.click();

    // Should show summary interface
    await expect(page.locator('[data-testid="summary-content"]')).toBeVisible();

    // Should show generate summary button
    const generateButton = page.locator('[data-testid="generate-summary-button"]');
    await expect(generateButton).toBeVisible();
    await expect(generateButton).toContainText('生成运单摘要');

    // Click generate summary
    await generateButton.click();

    // Should show loading state
    await expect(generateButton).toContainText('生成中');

    // Wait for summary to complete (with timeout)
    await page.waitForTimeout(5000);
  });

  test('should handle chat errors gracefully', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // Send a message that might cause an error (very long message)
    const longMessage = 'A'.repeat(10000);
    await chatInput.fill(longMessage);
    await sendButton.click();

    // Should either show error message or handle gracefully
    await page.waitForTimeout(3000);

    // Check if error alert is shown
    const errorAlert = page.locator('[role="alert"]');
    if (await errorAlert.isVisible()) {
      await expect(errorAlert).toContainText(/失败|错误|Error/i);
    }
  });

  test('should scroll chat messages to bottom on new message', async ({ page }) => {
    const chatMessages = page.locator('[data-testid="chat-messages"]');
    const chatInput = page.locator('[data-testid="chat-input"]');

    // Send a message
    await chatInput.fill('测试自动滚动');
    await chatInput.press('Enter');

    // Wait a bit for message to appear
    await page.waitForTimeout(1000);

    // Chat should scroll to show the latest message
    const userMessage = page.locator('[data-testid="user-message"]').last();
    await expect(userMessage).toBeInViewport();
  });
});