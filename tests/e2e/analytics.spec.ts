import { test, expect } from './fixtures'

const LOG = '__gtagLog'

// What Analytics is told, per document. gtag() pushes its arguments onto
// window.dataLayer, so patching push catches every call — including the ones on a
// page that is about to navigate away, which is the whole point here.
//
// The log goes to sessionStorage, not to a Playwright binding: a binding is a
// round trip to Node, and a redirecting document is gone before the message
// lands, so the test would pass for the wrong reason. sessionStorage is
// synchronous and survives the navigation.
async function recordGtag(page: import('@playwright/test').Page) {
  await page.addInitScript(
    ([key]) => {
      const layer: any[] = []
      const push = layer.push.bind(layer)
      ;(layer as any).push = (...args: any[]) => {
        const entry = `${args[0] && args[0][0]} ${location.pathname}`
        sessionStorage.setItem(key, (sessionStorage.getItem(key) ?? '') + entry + '\n')
        return push(...args)
      }
      ;(window as any).dataLayer = layer
    },
    [LOG],
  )
}

// The paths that reported themselves to Analytics, in order.
async function reportedPaths(page: import('@playwright/test').Page): Promise<string[]> {
  const log = await page.evaluate((key) => sessionStorage.getItem(key) ?? '', LOG)
  return log
    .split('\n')
    .filter((l) => l.startsWith('config '))
    .map((l) => l.slice('config '.length))
}

// A stale lower-case URL is a hop: 404.html decides to redirect before the GA tag
// runs, so only the page that is actually read reports itself. Chromium happens to
// abandon the hop's remaining scripts the moment location.replace lands, so the
// guard in base.html is belt and braces for engines that do not; what this test
// pins is the contract either way. tools/check.py enforces the ordering itself.
test('a redirect sends no pageview, only the page it lands on', async ({ page }) => {
  await recordGtag(page)
  await page.goto('/videopoker/')
  await expect(page).toHaveURL(/\/VideoPoker\/$/)
  await page.waitForFunction(() => (window as any).dataLayer?.length > 0)

  expect(await reportedPaths(page), 'the hop must not report itself').toEqual(['/VideoPoker/'])
})

// The other half: a real miss still has to show up, or broken links go unnoticed.
test('a genuine 404 still sends its pageview', async ({ page }) => {
  await recordGtag(page)
  await page.goto('/definitely-not-here/')
  await page.waitForFunction(() => (window as any).dataLayer?.length > 0)

  expect(await reportedPaths(page)).toEqual(['/definitely-not-here/'])
  const group = await page.evaluate(
    () => (window as any).dataLayer.find((a: any) => a[0] === 'config')?.[2]?.content_group,
  )
  expect(group).toBe('404')
})

// A test run is not an audience. This fails if the hermetic fixture stops covering
// a test that takes only `page`, which is how test traffic reached the property.
test('a test run never reaches real Analytics', async ({ page }) => {
  await page.goto('/')
  await page.waitForLoadState('domcontentloaded')
  expect(await page.evaluate(() => 'google_tag_manager' in window)).toBe(false)
})
