import { test, expect, apps } from './fixtures'

test('unknown URL serves the 404 page with a 404 status', async ({ page }) => {
  const res = await page.goto('/definitely-not-here/')
  expect(res?.status()).toBe(404)
  await expect(page.locator('h1')).toHaveText('Page not found')
  await expect(page.locator('main a[href="/"]')).toBeVisible()
})

// GitHub Pages is case-sensitive; 404.html maps wrong-case app URLs to the real ones.
for (const app of apps) {
  test(`wrong-case /${app.slug.toLowerCase()}/ redirects to /${app.slug}/`, async ({ page }) => {
    await page.goto(`/${app.slug.toLowerCase()}/`)
    await expect(page).toHaveURL(new RegExp(`/${app.slug}/$`))
    await expect(page.locator('h1')).not.toHaveText('Page not found')
  })
}

test('wrong-case blog filter URL redirects and keeps query and hash', async ({ page }) => {
  await page.goto('/blog/videopoker/?x=1#top')
  await expect(page).toHaveURL(/\/blog\/VideoPoker\/\?x=1#top$/)
})

test('/terms.html still lands on the Video Poker terms', async ({ page }) => {
  await page.goto('/terms.html')
  await expect(page).toHaveURL(/\/VideoPoker\/terms\.html$/)
  await expect(page.locator('h1')).toBeVisible()
})

test('legal pages: site policy links to every app that has a privacy URL', async ({ page }) => {
  await page.goto('/privacy-policy.html')
  for (const app of apps.filter((a) => (a as any).privacy_url)) {
    await expect(page.getByText(app.name.split(':')[0], { exact: false }).first(), app.slug).toBeVisible()
  }
  for (const p of ['/VideoPoker/privacy-policy.html', '/VideoPoker/terms.html']) {
    const res = await page.goto(p)
    expect(res?.status(), p).toBe(200)
    await expect(page.locator('h1')).toBeVisible()
  }
})
