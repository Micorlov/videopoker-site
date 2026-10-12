import { test as base, expect } from '@playwright/test'

// Block third parties so test traffic never reaches Google Analytics or Fonts.
// This is auto: a fixture is built only for the tests that name it, so as part of
// `errors` it left every other test reporting itself to the live property as a
// visitor. These tests run against production, where that data is the real record.
const test = base.extend<{ hermetic: void; errors: string[] }>({
  hermetic: [
    async ({ page, baseURL }, use) => {
      const origin = new URL(baseURL!).origin
      await page.route((url) => url.origin !== origin, (route) => route.abort())
      await use()
    },
    { auto: true },
  ],
  errors: async ({ page, baseURL }, use) => {
    const errors: string[] = []
    const origin = new URL(baseURL!).origin
    page.on('pageerror', (e) => errors.push(e.message))
    page.on('response', (r) => { if (r.url().startsWith(origin) && r.status() >= 400) errors.push(`${r.status()} ${r.url()}`) })
    await use(errors)
  },
})

test('home page loads with the studio heading, apps and blog', async ({ page, errors }) => {
  const res = await page.goto('/')
  expect(res?.status()).toBe(200)
  await expect(page).toHaveTitle(/Orlov Games/)
  await expect(page.locator('h1')).toContainText('Orlov Games')
  expect(await page.locator('#apps a.card').count()).toBeGreaterThan(5)
  expect(await page.locator('#blog .post-item').count()).toBeGreaterThan(0)
  expect(errors).toEqual([])
})

test('an app page loads with a Play Store link', async ({ page, errors }) => {
  await page.goto('/')
  await page.locator('#apps a.card').first().click()
  await expect(page.locator('h1')).toBeVisible()
  await expect(page.locator('a[data-app][href*="play.google.com"]').first()).toHaveAttribute('href', /id=/)
  expect(errors).toEqual([])
})

test('blog index lists posts and a post opens', async ({ page, errors }) => {
  await page.goto('/blog/')
  await expect(page.locator('h1')).toHaveText('Blog')
  const first = page.locator('.post-item h3 a').first()
  await first.click()
  await expect(page.locator('h1')).toBeVisible()
  expect(errors).toEqual([])
})

test('wrong-case URL redirects and unknown URL is a real 404', async ({ page, request }) => {
  await page.goto('/videopoker/')
  await expect(page).toHaveURL(/\/VideoPoker\/$/)
  const missing = await request.get('/definitely-not-here/')
  expect(missing.status()).toBe(404)
})

test('sitemap, robots and privacy policy are served', async ({ request }) => {
  const sitemap = await request.get('/sitemap.xml')
  expect(sitemap.status()).toBe(200)
  expect(await sitemap.text()).toContain('<loc>https://michaelorlov.com/</loc>')
  expect((await request.get('/robots.txt')).status()).toBe(200)
  expect((await request.get('/privacy-policy.html')).status()).toBe(200)
})

test('home page does not scroll sideways', async ({ page }) => {
  await page.goto('/')
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)
  expect(overflow).toBe(false)
})
