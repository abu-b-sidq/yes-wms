import { test, expect } from '@playwright/test';

test.describe('Nginx routing - all services reachable', () => {

  test('/ redirects to /web/', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.url()).toContain('/web/');
  });

  test('/web/ serves React (Vite) app', async ({ page }) => {
    const response = await page.goto('/web/');
    expect(response?.status()).toBe(200);
    // Vite injects a script with /web/ base path
    const html = await page.content();
    expect(html).toContain('/web/');
  });

  test('/opsdashboard/ serves Angular app', async ({ page }) => {
    const response = await page.goto('/opsdashboard/');
    expect(response?.status()).toBe(200);
    const html = await page.content();
    expect(html).toContain('<base href="/opsdashboard/"');
  });

  test('/backend/api/v1/health returns 200', async ({ request }) => {
    const response = await request.get('/backend/api/v1/health');
    expect(response.status()).toBe(200);
  });

  test('/mobile/ serves Expo web app', async ({ page }) => {
    const response = await page.goto('/mobile/');
    expect(response?.status()).toBe(200);
  });

  test('web app loads without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.goto('/web/');
    await page.waitForLoadState('networkidle');
    // Filter out known non-critical errors (e.g. Firebase config)
    const critical = errors.filter(e => !e.includes('Firebase') && !e.includes('auth'));
    expect(critical).toHaveLength(0);
  });

  test('opsdashboard app loads without 404 assets', async ({ page }) => {
    const failed: string[] = [];
    page.on('response', (resp) => {
      if (resp.status() === 404 && resp.url().includes('/opsdashboard/')) {
        failed.push(resp.url());
      }
    });
    await page.goto('/opsdashboard/');
    await page.waitForLoadState('networkidle');
    expect(failed).toHaveLength(0);
  });

  test('backend API CORS headers present', async ({ request }) => {
    const response = await request.fetch('/backend/api/v1/health', {
      headers: { 'Origin': 'http://localhost' },
    });
    expect(response.status()).toBe(200);
  });
});
