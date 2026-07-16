# Trainee invitations

Coach-created trainee invitations are private, expiring, single-use secrets. Redeeming one creates the trainee account and its active relationship with the issuing coach in one transaction. Used, expired, revoked, and email-mismatched invitations are rejected.

## Create and share an invitation

1. Sign in as a non-demo coach and open **Invitations**.
2. Optionally enter **Restrict to trainee email (optional)**. This limits redemption to an account using that email. It does not send an email. Leaving the field blank allows any eligible trainee possessing the invitation to redeem it.
3. Choose an expiry and select **Create invite**.
4. Use **Copy invitation link** or **Copy invitation code** and share it manually through a trusted external channel.

FitIntel 360 does not send, resend, or track invitation email delivery. The raw secret is returned only at creation and cannot be recovered after the page is refreshed because only its hash is stored. Create a new invitation if the secret was not copied. Invitation history shows status and metadata without revealing the secret; an active invitation may be revoked.

Demo coaches may inspect the invitation screen, but frontend controls are disabled and the backend rejects mutations. See [Getting started](getting-started.md), the [coach manual](user-manual-coach.md), and [troubleshooting](troubleshooting.md) for related workflows.
