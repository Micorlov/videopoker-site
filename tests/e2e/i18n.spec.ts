import { test, expect, builtLanguages, excluded, sitemapPaths, type Language } from './fixtures'

// Resolved per test, after the build: see builtLanguages() in fixtures.
const published = () => builtLanguages()
const first = (dir?: 'rtl') => published().find((l) => !dir || l.dir === dir)

// ---------------------------------------------------------------- Hebrew

// The site is published in every supported language except Hebrew. The build
// refuses to produce it, but that is the thing worth checking against what was
// actually served rather than against the code that decided it.

test('no Hebrew page is served', async ({ page }) => {
  for (const code of excluded) {
    const response = await page.goto(`/${code}/`)
    expect(response?.status(), `/${code}/ must not exist`).toBe(404)
  }
})

test('no Hebrew URL is in the sitemap', () => {
  const hebrew = sitemapPaths().filter((p) => /^\/(he|iw)(-|\/)/i.test(p))
  expect(hebrew).toEqual([])
})

test('no page offers Hebrew as an alternate', async ({ page }) => {
  for (const path of ['/', '/blog/', '/VideoPoker/']) {
    await page.goto(path)
    await expect(page.locator('link[hreflang="he"], link[hreflang="iw"]'), path).toHaveCount(0)
    await expect(page.locator('.langpicker a[hreflang="he"], .langpicker a[hreflang="iw"]'), path).toHaveCount(0)
  }
})

// ---------------------------------------------------------------- English

test('English keeps its own URLs', async ({ page }) => {
  const response = await page.goto('/blog/')
  expect(response?.status()).toBe(200)
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', /\/blog\/$/)
})

// ---------------------------------------------------------------- languages

test.describe('a published language', () => {
  // A language is skipped rather than failed when its translations are not
  // committed yet: an English-only build is a valid state of this site.
  let sample: Language

  test.beforeEach(() => {
    const found = first()
    test.skip(!found, 'no language has translations committed yet')
    sample = found!
  })

  test('declares its language and direction', async ({ page }) => {
    await page.goto(`/${sample.code}/`)
    await expect(page.locator('html')).toHaveAttribute('lang', sample.code)
    await expect(page.locator('html')).toHaveAttribute('dir', sample.dir)
  })

  test('is canonical to itself and defers to English', async ({ page }) => {
    await page.goto(`/${sample.code}/blog/`)
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      'href', new RegExp(`/${sample.code}/blog/$`))
    await expect(page.locator('link[hreflang="x-default"]')).toHaveAttribute('href', /\/blog\/$/)
    await expect(page.locator(`link[hreflang="${sample.code}"]`)).toHaveAttribute(
      'href', new RegExp(`/${sample.code}/blog/$`))
  })

  test('keeps its links inside its own tree', async ({ page }) => {
    await page.goto(`/${sample.code}/blog/`)
    const hrefs = await page.locator('main a[href^="/"]').evaluateAll(
      (as) => as.map((a) => a.getAttribute('href') ?? ''))
    expect(hrefs.length).toBeGreaterThan(0)
    for (const href of hrefs) expect(href, href).toMatch(new RegExp(`^/${sample.code}/`))
  })

  test('shares the stylesheet and images with every other language', async ({ page }) => {
    const asked: string[] = []
    page.on('request', (r) => {
      const path = new URL(r.url()).pathname
      if (/\.(css|woff2|svg|png|jpg)$/.test(path)) asked.push(path)
    })
    await page.goto(`/${sample.code}/`)
    expect(asked.length).toBeGreaterThan(0)
    for (const path of asked) expect(path, path).not.toMatch(new RegExp(`^/${sample.code}/`))
  })

  test('reaches the English page and back through the picker', async ({ page }) => {
    await page.goto(`/${sample.code}/blog/`)
    await page.locator('.langpicker summary').click()
    await page.locator('.langpicker a[hreflang="en"]').click()
    await expect(page).toHaveURL(/\/blog\/$/)
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await page.locator('.langpicker summary').click()
    await page.locator(`.langpicker a[hreflang="${sample.code}"]`).click()
    await expect(page).toHaveURL(new RegExp(`/${sample.code}/blog/$`))
  })

  test('sends a wrong-case URL to the right page in the same language', async ({ page }) => {
    await page.goto(`/${sample.code}/videopoker/`)
    await expect(page).toHaveURL(new RegExp(`/${sample.code}/VideoPoker/$`))
    await expect(page.locator('html')).toHaveAttribute('lang', sample.code)
  })

  test('lists every published language, and only those', async ({ page }) => {
    await page.goto(`/${sample.code}/`)
    await expect(page.locator('.langpicker a')).toHaveCount(published().length + 1)
  })
})

test.describe('right to left', () => {
  test('lays out without a horizontal scrollbar', async ({ page }) => {
    const rtl = first('rtl')
    test.skip(!rtl, 'no right-to-left language has translations committed yet')
    await page.setViewportSize({ width: 390, height: 844 })
    for (const path of ['/', '/blog/', '/VideoPoker/']) {
      await page.goto(`/${rtl!.code}${path}`)
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)
      expect(overflow, `${rtl!.code}${path}`).toBe(false)
    }
  })
})
