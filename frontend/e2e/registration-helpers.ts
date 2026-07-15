import { expect, request } from '@playwright/test'
import { apiUrl } from './config'

export async function createTraineeInvite(intendedEmail?: string): Promise<string> {
  const context = await request.newContext()
  const login = await context.post(`${apiUrl}/auth/login`, {
    data: { email: 'coach@fitness.example.com', password: 'DemoPass123!' },
  })
  expect(login.ok()).toBeTruthy()
  const auth = await login.json()
  const created = await context.post(`${apiUrl}/coach/invites`, {
    headers: { Authorization: `Bearer ${auth.access_token}` },
    data: { intended_email: intendedEmail ?? null, expires_in_days: 1 },
  })
  expect(created.ok()).toBeTruthy()
  const invite = await created.json()
  await context.dispose()
  return invite.token
}
