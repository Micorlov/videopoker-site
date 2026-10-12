import fs from 'node:fs'
import path from 'node:path'
import { test as base, expect, type Page } from '@playwright/test'

const ROOT = path.resolve(__dirname, '../..')

export interface App { slug: string; name: string; package: string; status: 'live' | 'testing'; category: string; tagline: string }

export const apps: App[] = JSON.parse(fs.readFileSync(path.join(ROOT, 'content/apps.json'), 'utf8'))

// Pages the sitemap promises; read from the build that the webServer just made.
export function sitemapPaths(): string[] {
  const xml = fs.readFileSync(path.join(ROOT, '_site/sitemap.xml'), 'utf8')
  return [...xml.matchAll(/<loc>https?:\/\/[^/]+(\/[^<]*)<\/loc>/g)].map((m) => m[1])
}

export interface PageHealth { errors: string[]; badResponses: string[] }

// Every test gets: no network beyond localhost (GA and Google Fonts are blocked so runs are
// hermetic), plus a record of JS errors and same-origin responses that came back >= 400.
export const test = base.extend<{ hermetic: void; health: PageHealth }>({
  // auto, so it also covers a test that takes only `page`. Playwright builds a
  // fixture only for the tests that name it, so while this lived inside `health`
  // every other test loaded the real gtag.js and reported itself to Analytics —
  // the 404 tests included, which is how a redirect became a "Page not found" view.
  hermetic: [
    async ({ page }, use) => {
      await page.route(/^https?:\/\/(?!localhost)/, (route) => route.abort())
      await use()
    },
    { auto: true },
  ],
  health: async ({ page }, use) => {
    const health: PageHealth = { errors: [], badResponses: [] }
    page.on('pageerror', (e) => health.errors.push(`pageerror: ${e.message}`))
    page.on('console', (m) => {
      // Aborted third-party requests log "Failed to load resource"; those are expected here.
      if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) health.errors.push(`console: ${m.text()}`)
    })
    page.on('response', (r) => {
      if (r.url().startsWith('http://localhost') && r.status() >= 400) health.badResponses.push(`${r.status()} ${r.url()}`)
    })
    await use(health)
  },
})

export { expect }

export async function hasHorizontalScroll(page: Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)
}
