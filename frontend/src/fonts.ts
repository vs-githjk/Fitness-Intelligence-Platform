// Iron Editorial typography faces (Experience Cycle 2, C2.0).
//
// Self-hosted SIL-OFL faces bundled via @fontsource (no CDN, CSP-safe, offline).
// Importing these registers their @font-face rules and includes the woff2 in the
// production build, but it does NOT change any rendered surface: no live
// font-family references these families yet. C2.1 repoints the display, coach-voice,
// and numeral role tokens (--mb-font-display / --mb-font-coach / --mb-font-numeral)
// onto them as each surface migrates.
//
// Inter (the Structure/UI role) is intentionally NOT bundled here. 'Inter' is the
// first family in the app-wide sans stack, so bundling it would change every legacy
// screen's rendering; that audited activation is deferred to the shell migration.
import '@fontsource/archivo-black/400.css' // Athletic display (single display weight)
import '@fontsource/source-serif-4/400.css' // Coach voice
import '@fontsource/source-serif-4/400-italic.css'
import '@fontsource/ibm-plex-mono/400.css' // Engineered numerals
import '@fontsource/ibm-plex-mono/500.css'
