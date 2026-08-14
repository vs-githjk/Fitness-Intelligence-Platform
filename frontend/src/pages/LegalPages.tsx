import { ArrowLeft } from 'lucide-react'
import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Wordmark } from '../components/iron/Wordmark'
import { StatusNotice } from '../components/ui'
import { COMPANY, COMPANY_LEGAL_COMPLETE, orPending } from '../config/company'

const LEGAL_LINKS = [
  { to: '/privacy', label: 'Privacy' },
  { to: '/consumer-health-data', label: 'Consumer Health Data' },
  { to: '/terms', label: 'Terms' },
  { to: '/health-disclaimer', label: 'Health Disclaimer' },
  { to: '/security', label: 'Security' },
]

// Public legal footer — reused on the auth front door and at the foot of each legal page.
export function LegalFooter({ className = '' }: { className?: string }) {
  return (
    <nav aria-label="Legal" className={`flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-mb-secondary ${className}`}>
      {LEGAL_LINKS.map(link => <Link key={link.to} to={link.to} className="hover:text-mb-ink hover:underline">{link.label}</Link>)}
    </nav>
  )
}

function LegalLayout({ title, updated, children }: { title: string; updated?: string; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-mb-page font-structure text-mb-ink">
      <header className="border-b border-mb-ink/10">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-5">
          <Link to="/" className="rounded-mb-control"><Wordmark size="sm" /></Link>
          <Link to="/login" className="inline-flex items-center gap-1.5 text-sm font-semibold text-mb-secondary hover:text-mb-ink"><ArrowLeft aria-hidden="true" className="size-4" />Back to sign in</Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-mb-secondary">Vytal · Legal</p>
        <h1 className="mt-2 font-display text-4xl uppercase leading-[0.95] tracking-tight">{title}</h1>
        {updated && <p className="mt-3 text-sm text-mb-secondary">Effective {orPending(COMPANY.effectiveDate, 'date')}</p>}
        {!COMPANY_LEGAL_COMPLETE && (
          <div className="mt-6">
            <StatusNotice tone="info" title="Pending final details">
              These policies are prepared and awaiting the company's final legal details and counsel review before they are presented as final. The substance reflects how Vytal actually works.
            </StatusNotice>
          </div>
        )}
        <div className="legal-prose mt-8 space-y-6 text-mb-body leading-7 text-mb-ink">{children}</div>
        <hr className="my-10 border-mb-ink/10" />
        <LegalFooter />
      </main>
    </div>
  )
}

function H2({ children }: { children: ReactNode }) { return <h2 className="mt-8 font-display text-xl uppercase tracking-tight text-mb-ink">{children}</h2> }
function P({ children }: { children: ReactNode }) { return <p>{children}</p> }
function UL({ children }: { children: ReactNode }) { return <ul className="ml-5 list-disc space-y-1.5">{children}</ul> }
const entity = () => orPending(COMPANY.legalEntity, 'company legal name')
const privacyEmail = () => orPending(COMPANY.privacyEmail, 'privacy email')

export function PrivacyPage() {
  return (
    <LegalLayout title="Privacy Policy" updated>
      <P>This policy explains what {COMPANY.product} collects, how we use it, and your choices. {COMPANY.product} is operated by {entity()} and is fitness/coaching software — <strong>not</strong> a medical service (see the <Link className="underline" to="/health-disclaimer">Health &amp; Fitness Disclaimer</Link>). If you are in Washington or another state with a consumer-health-data law, also read the <Link className="underline" to="/consumer-health-data">Consumer Health Data Notice</Link>.</P>
      <H2>Who this applies to</H2>
      <P><strong>Coaches</strong> create exercises and programs and invite trainees. <strong>Trainees</strong> are invited by a coach to receive, perform, and record training. Some data is deliberately shared within that coaching relationship.</P>
      <H2>What we collect</H2>
      <UL>
        <li>Account information (name, email, password stored only as a hash, role)</li>
        <li>Coach and trainee profile fields you enter</li>
        <li>Fitness assessments and baseline inputs, and daily readiness check-ins (trainees)</li>
        <li>Workout content you author or import, and workout performance and history you record</li>
        <li>Safety reports, media you upload, and invitation records</li>
        <li>Technical and security logs (request IDs, timestamps, IP address, coarse device info)</li>
      </UL>
      <P>We do not collect precise geolocation, we do not sell personal information, and we do not run third-party advertising trackers on health screens.</P>
      <H2>How we use it</H2>
      <P>To provide the service, keep it safe and reliable, and send service-essential messages (invitations, security notices). We do not use your training or health inputs for advertising or to train machine-learning models.</P>
      <H2>Coaching relationships</H2>
      <P>When a trainee accepts a coach's invitation, they consent to share training and health inputs with that coach. A coach sees this only for their own trainees. A trainee can withdraw consent, which ends the sharing going forward. These boundaries are enforced in the software.</P>
      <H2>Sharing</H2>
      <P>We use infrastructure providers (hosting, database, media) that process data only to provide those services to us under contract. We may disclose information where required by law. We do not sell your data or share it for cross-context behavioral advertising.</P>
      <H2>Retention &amp; your rights</H2>
      <P>We keep your data while your account is active and as needed to provide the service; published training content is retained as immutable history. You can request access, export, correction, deletion, or (trainees) withdrawal of consent by emailing {privacyEmail()}. We honor verified requests free within 45 days.</P>
      <H2>Children</H2>
      <P>{COMPANY.product} requires users to be at least {COMPANY.minAge} and is not directed to children under 13.</P>
      <H2>Contact</H2>
      <P>{privacyEmail()} · {entity()}, {orPending(COMPANY.address, 'address')}.</P>
    </LegalLayout>
  )
}

export function ConsumerHealthDataPage() {
  return (
    <LegalLayout title="Consumer Health Data" updated>
      <P>This notice supplements the <Link className="underline" to="/privacy">Privacy Policy</Link> and addresses consumer health data under laws such as the Washington My Health My Data Act.</P>
      <H2>What we collect</H2>
      <P>Data a reasonable person could link to your health: fitness assessments and baseline measurements, readiness check-ins, and workout performance and history you record.</P>
      <H2>Why, and consent</H2>
      <P>Solely to provide coaching: to let your coach program your training and to let you record it. At invitation acceptance, a trainee gives specific, revocable consent to collect this data and share it with the coach who invited them.</P>
      <H2>Sharing &amp; your rights</H2>
      <P>Shared only with your coach and with providers that host it on our behalf. We do not sell consumer health data or share it for cross-context advertising. You may withdraw consent, access, or delete this data, and request a list of who it has been shared with, by emailing {privacyEmail()}.</P>
    </LegalLayout>
  )
}

export function TermsPage() {
  return (
    <LegalLayout title="Terms of Service" updated>
      <P>These Terms govern your use of {COMPANY.product}, operated by {entity()}. By using {COMPANY.product} you agree to these Terms, the <Link className="underline" to="/privacy">Privacy Policy</Link>, and the <Link className="underline" to="/health-disclaimer">Health &amp; Fitness Disclaimer</Link>.</P>
      <H2>Accounts</H2>
      <P>You must be at least {COMPANY.minAge}. You are responsible for your account, its security, and the accuracy of your information.</P>
      <H2>Coaches and trainees</H2>
      <P><strong>Coaches are solely responsible for the training they design and assign</strong>, including its appropriateness for each trainee. {COMPANY.product} is a tool; it does not author, review, or endorse a coach's programming, and it is not a marketplace. Training is undertaken at your own risk.</P>
      <H2>Not medical advice</H2>
      <P>{COMPANY.product} does not provide medical advice, diagnosis, or treatment. See the <Link className="underline" to="/health-disclaimer">Disclaimer</Link>.</P>
      <H2>Your content</H2>
      <P>You keep ownership of content you create or import, and grant {COMPANY.product} a limited license to host and display it to operate the service for you and your coaching relationships. You are responsible for having the rights to what you upload and for not uploading anything unlawful or harmful.</P>
      <H2>Acceptable use</H2>
      <P>Do not misuse or disrupt the service, access data that is not yours, scrape or bulk-extract data, upload malware, or use {COMPANY.product} to provide medical services or make medical claims. Imported files are parsed as data only; macros and formulas are never executed.</P>
      <H2>Availability, termination &amp; liability</H2>
      <P>The service is provided "as is" and "as available"; we may modify or discontinue features. You may delete your account at any time; we may suspend access for violations. Liability is limited to the maximum extent permitted by law. These Terms are governed by the laws of {orPending(COMPANY.jurisdiction, 'jurisdiction')}.</P>
      <H2>Contact</H2>
      <P>{orPending(COMPANY.supportEmail, 'support email')} · {entity()}.</P>
    </LegalLayout>
  )
}

export function HealthDisclaimerPage() {
  return (
    <LegalLayout title="Health & Fitness Disclaimer" updated>
      <P>{COMPANY.product} is fitness and coaching software. It helps coaches plan training and helps trainees follow and record it. <strong>{COMPANY.product} is not a medical device and does not provide medical advice, diagnosis, or treatment.</strong></P>
      <UL>
        <li><strong>Not medical care.</strong> Nothing in {COMPANY.product} — exercises, plans, check-ins, scores, or coach guidance — is a substitute for professional medical advice.</li>
        <li><strong>Consult a professional</strong> before beginning any exercise program, especially with an injury, medical condition, pregnancy, or any concern about training safely.</li>
        <li><strong>Stop and seek help</strong> if you feel pain, dizziness, chest discomfort, or any concerning symptom. In an emergency, contact your local emergency services.</li>
        <li><strong>Coaches, not clinicians.</strong> Coaches are fitness professionals responsible for their own programming; {COMPANY.product} does not endorse it as medically appropriate for anyone.</li>
        <li><strong>You accept training risk.</strong> Physical training carries inherent risks; train within your limits with appropriate technique and equipment.</li>
      </UL>
      <P>This disclaimer is part of the <Link className="underline" to="/terms">Terms of Service</Link>.</P>
    </LegalLayout>
  )
}

export function SecurityPage() {
  return (
    <LegalLayout title="Security & Trust">
      <P>We describe only controls that are actually in place. We do not claim certifications or protections we have not implemented and verified.</P>
      <H2>What we do</H2>
      <UL>
        <li><strong>Encryption in transit</strong> — served over HTTPS/TLS in staging and production; HSTS is enforced in production.</li>
        <li><strong>Password protection</strong> — passwords stored only as salted bcrypt hashes.</li>
        <li><strong>Authenticated, role-scoped access</strong> — every request is authenticated and authorized on the server; requests for another account's data return "not found".</li>
        <li><strong>Tenant boundaries</strong> — a coach's private content is visible only to that coach; a trainee reads only the narrow fields needed to train.</li>
        <li><strong>Hardened responses</strong> — nosniff, frame-deny, a strict Content-Security-Policy, and a no-referrer policy.</li>
        <li><strong>Abuse throttling</strong> — authentication, registration, and import endpoints are rate-limited in deployed environments.</li>
        <li><strong>Access-controlled media</strong> — served only through an authenticated endpoint, with type and size limits on upload.</li>
        <li><strong>Configuration safety</strong> — deployed environments fail to start without required security configuration.</li>
      </UL>
      <H2>Reporting a vulnerability</H2>
      <P>Email {orPending(COMPANY.securityEmail, 'security email')} with details and steps to reproduce, and allow reasonable time to remediate before disclosure.</P>
      <H2>What we do not claim</H2>
      <P>{COMPANY.product} does not currently claim HIPAA compliance, SOC 2, ISO 27001, third-party penetration testing, 24/7 monitoring, or malware scanning. When any becomes true and verifiable, it will be added here — not before.</P>
    </LegalLayout>
  )
}
