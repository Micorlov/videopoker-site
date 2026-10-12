import { defineConfig, devices } from '@playwright/test'

// Read-only sanity check of the deployed site. No local server, no build.
//   npm run test:live                      -> https://michaelorlov.com
//   LIVE_URL=https://staging.example npm run test:live
export default defineConfig({
  testDir: './tests/live',
  fullyParallel: true,
  retries: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.LIVE_URL || 'https://michaelorlov.com',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 5'] } },
  ],
})
