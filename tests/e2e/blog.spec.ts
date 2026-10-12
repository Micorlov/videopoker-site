import { test, expect } from './fixtures'

test('blog index: chip counts match the posts each filter shows', async ({ page }) => {
  await page.goto('/blog/')
  const total = await page.locator('.post-list .post-item').count()
  expect(total).toBeGreaterThan(0)
  await expect(page.locator('.chips .chip.on')).toHaveText(new RegExp(`All\\s*${total}`))

  const chips = await page.locator('.chips a.chip').evaluateAll((els) =>
    els.map((e) => ({ href: e.getAttribute('href')!, count: Number(e.querySelector('span')!.textContent) })))
  expect(chips.length).toBeGreaterThan(1)

  for (const chip of chips.filter((c) => c.href !== '/blog/')) {
    await page.goto(chip.href)
    await expect(page.locator('.post-list .post-item'), chip.href).toHaveCount(chip.count)
    await expect(page.locator('.chips .chip.on'), chip.href).toHaveAttribute('href', chip.href)
  }
})

test('every post on the index opens and has a headline and body', async ({ page }) => {
  await page.goto('/blog/')
  const links = await page.locator('.post-item h3 a').evaluateAll((els) => els.map((e) => e.getAttribute('href')!))
  for (const href of links) {
    const res = await page.goto(href)
    expect(res?.status(), href).toBe(200)
    await expect(page.locator('h1'), href).toBeVisible()
    expect((await page.locator('main').innerText()).length, href).toBeGreaterThan(500)
  }
})

test('header Blog link reaches the blog', async ({ page }) => {
  await page.goto('/')
  await page.locator('.topnav a[href="/blog/"]').click()
  await expect(page).toHaveURL(/\/blog\/$/)
  await expect(page.locator('h1')).toHaveText('Blog')
})
