import { expect } from '@playwright/test'
import { test } from './fixtures'

// Takes only `page` — exactly the case the old fixture missed, because the route
// lived inside `health` and Playwright builds a fixture only for tests that name it.
test('a test that never names health still reaches no third party', async ({ page }) => {
  const reached: string[] = []
  // A response means the request actually completed; an aborted one never gets here.
  page.on('response', (r) => {
    if (!/^https?:\/\/localhost/.test(r.url())) reached.push(r.url())
  })
  for (const path of ['/', '/blog/', '/VideoPoker/', '/blog/why-a-kicker-never-helps.html', '/nope']) {
    await page.goto(path)
  }
  expect(reached, 'third-party responses received').toEqual([])
})

test('the Analytics script is blocked, so no pageview is sent', async ({ page }) => {
  const attempted: string[] = []
  page.on('request', (r) => {
    if (/googletagmanager|google-analytics/.test(r.url())) attempted.push(r.url())
  })
  const failed: string[] = []
  page.on('requestfailed', (r) => {
    if (/googletagmanager|google-analytics/.test(r.url())) failed.push(r.url())
  })
  await page.goto('/')
  await page.waitForTimeout(500)
  // gtag.js is referenced by the page, so it is attempted — and must never complete.
  expect(attempted.length, 'page should still reference gtag.js').toBeGreaterThan(0)
  expect(failed.sort()).toEqual(attempted.sort())
})
