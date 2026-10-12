import { test, expect, apps, sitemapPaths, hasHorizontalScroll } from './fixtures'

const paths = sitemapPaths()

test('sitemap is not empty and lists every app and the blog', () => {
  expect(paths).toContain('/')
  expect(paths).toContain('/blog/')
  for (const app of apps) expect(paths, app.slug).toContain(`/${app.slug}/`)
})

for (const p of paths) {
  test.describe(p, () => {
    test('renders cleanly', async ({ page, health }) => {
      const response = await page.goto(p)
      expect(response?.status()).toBe(200)
      await page.waitForLoadState('load')

      await expect(page).toHaveTitle(/\S/)
      await expect(page.locator('h1')).toHaveCount(1)
      await expect(page.locator('header.bar a.mark')).toHaveAttribute('href', '/')
      await expect(page.locator('footer a[href="/privacy-policy.html"]')).toBeVisible()

      expect(health.errors, 'JS errors').toEqual([])
      expect(health.badResponses, 'failed local requests').toEqual([])
    })

    test('every image loads and nothing scrolls sideways', async ({ page, request }) => {
      await page.goto(p)
      const srcs = await page.$$eval('img[src^="/"]', (imgs) => [...new Set(imgs.map((i) => i.getAttribute('src')!))])
      for (const src of srcs) {
        const res = await request.get(src)
        expect(res.status(), src).toBe(200)
        expect(res.headers()['content-type'], src).toMatch(/^image\//)
      }
      expect(await hasHorizontalScroll(page), 'horizontal scroll').toBe(false)
    })
  })
}
