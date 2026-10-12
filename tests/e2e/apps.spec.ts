import { test, expect, apps } from './fixtures'

test('home lists every app once, linking to its page', async ({ page }) => {
  await page.goto('/')
  for (const app of apps) {
    await expect(page.locator(`#apps a.card[href="/${app.slug}/"], #testing a.card[href="/${app.slug}/"]`), app.slug).toHaveCount(1)
  }
  await expect(page.locator('#apps a.card')).toHaveCount(apps.filter((a) => a.status === 'live').length)
  await expect(page.locator('#testing a.card')).toHaveCount(apps.filter((a) => a.status === 'testing').length)
  await expect(page.locator('#testing .state.soon')).toHaveCount(apps.filter((a) => a.status === 'testing').length)
})

test('home "See all apps" and card navigation work', async ({ page }) => {
  await page.goto('/')
  await page.locator('.cta-row a[href="#apps"]').click()
  await expect(page).toHaveURL(/#apps$/)
  const first = apps.find((a) => a.status === 'live')!
  await page.locator(`#apps a.card[href="/${first.slug}/"]`).click()
  await expect(page).toHaveURL(new RegExp(`/${first.slug}/$`))
  await expect(page.locator('h1')).toBeVisible()
})

for (const app of apps) {
  test(`${app.slug} page matches its status (${app.status})`, async ({ page }) => {
    await page.goto(`/${app.slug}/`)
    const play = page.locator(`a[data-app="${app.slug}"][href*="play.google.com"]:visible`)
    if (app.status === 'live') {
      await expect(play.first(), 'Play button').toBeVisible()
      await expect(play.first()).toHaveAttribute('href', new RegExp(`id=${app.package.replace(/\./g, '\\.')}`))
    } else {
      await expect(play, 'testing apps must not link to a store listing').toHaveCount(0)
      await expect(page.getByText('Coming soon').first()).toBeVisible()
    }
  })
}

for (const app of apps.filter((a) => a.status === 'live')) {
  test(`${app.slug}: every Google Play link is tracked (data-app)`, async ({ page }) => {
    await page.goto(`/${app.slug}/`)
    const untracked = await page.$$eval('a[href*="play.google.com"]:not([data-app])', (els) => els.map((e) => e.outerHTML.slice(0, 80)))
    expect(untracked, 'Play links missing data-app never send play_store_click').toEqual([])
  })
}

test('a Google Play click sends a play_store_click analytics event', async ({ page }) => {
  await page.goto('/VideoPoker/')
  await page.evaluate(() => {
    window.dataLayer = []
    // Stop the navigation to Google Play; we only care about the event.
    document.addEventListener('click', (e) => { if ((e.target as Element).closest('a[data-app]')) e.preventDefault() }, true)
    ;(window as any).gtag = function () { window.dataLayer.push(arguments) }
  })
  await page.locator('a[data-app="VideoPoker"]:visible').first().click()
  const events = await page.evaluate(() => window.dataLayer.map((a: any) => Array.from(a)))
  expect(events).toContainEqual(['event', 'play_store_click', expect.objectContaining({ app: 'VideoPoker' })])
})

declare global { interface Window { dataLayer: any[] } }
