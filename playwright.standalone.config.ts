import { defineConfig, devices } from '@playwright/test'
export default defineConfig({
  testDir: './tests/standalone',
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: 'http://127.0.0.1:4173/Zehnyar/',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    launchOptions: { args: ['--no-sandbox', '--disable-dev-shm-usage'] },
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'iphone-webkit', use: { ...devices['iPhone 13'], browserName: 'webkit' } },
  ],
  webServer: {
    command: 'npm run preview -- --port 4173',
    env: { VITE_BASE_PATH: '/Zehnyar/' },
    url: 'http://127.0.0.1:4173/Zehnyar/',
    reuseExistingServer: false,
  },
})
