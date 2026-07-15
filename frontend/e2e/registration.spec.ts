import { expect, test } from '@playwright/test'

const coachRegistrationCode = process.env.PLAYWRIGHT_COACH_REGISTRATION_CODE

test('clean account bootstrap creates coach, invite, and assigned trainee', async ({ page }) => {
  test.skip(!coachRegistrationCode, 'PLAYWRIGHT_COACH_REGISTRATION_CODE is required at runtime')
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  const coachEmail = `coach-${suffix}@example.com`
  const traineeEmail = `trainee-${suffix}@example.com`
  const password = 'RegistrationPass123!'

  await page.goto('/register')
  await page.getByRole('button', { name: /^Coach/ }).click()
  await page.getByLabel('First name').fill('Test')
  await page.getByLabel('Last name').fill('Coach')
  await page.getByLabel('Email address').fill(coachEmail)
  await page.getByLabel('Create a password').fill(password)
  await page.getByLabel('Coach registration code').fill(coachRegistrationCode!)
  await page.getByRole('button', { name: 'Create coach account' }).click()
  await expect(page).toHaveURL(/\/coach\/dashboard$/)

  await page.goto('/coach/invites')
  await page.getByLabel('Trainee email').fill(traineeEmail)
  await page.getByRole('button', { name: /Create invite/ }).click()
  await expect(page.getByText('Invitation created—copy it now')).toBeVisible()
  const inviteToken = (await page.locator('code').first().textContent())?.trim()
  expect(inviteToken).toBeTruthy()
  await page.getByRole('button', { name: 'Sign out' }).first().click()

  await page.goto(`/register?role=trainee&invite=${encodeURIComponent(inviteToken!)}`)
  await expect(page).toHaveURL(/\/register$/)
  await page.getByLabel('First name').fill('Test')
  await page.getByLabel('Last name').fill('Trainee')
  await page.getByLabel('Email address').fill(traineeEmail)
  await page.getByLabel('Create a password').fill(password)
  await page.getByRole('button', { name: 'Create trainee account' }).click()
  await expect(page).toHaveURL(/\/onboarding$/)
  await page.getByRole('button', { name: 'Sign out' }).first().click()

  await page.goto(`/register?role=trainee&invite=${encodeURIComponent(inviteToken!)}`)
  await page.getByLabel('First name').fill('Second')
  await page.getByLabel('Last name').fill('Attempt')
  await page.getByLabel('Email address').fill(`second-${suffix}@example.com`)
  await page.getByLabel('Create a password').fill(password)
  await page.getByRole('button', { name: 'Create trainee account' }).click()
  await expect(page.getByText('Registration could not be completed with the supplied details')).toBeVisible()
})
