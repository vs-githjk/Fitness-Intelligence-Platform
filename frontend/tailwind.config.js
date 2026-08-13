/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        page: 'rgb(var(--color-page) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        elevated: 'rgb(var(--color-elevated) / <alpha-value>)',
        foreground: 'rgb(var(--color-foreground) / <alpha-value>)',
        secondary: 'rgb(var(--color-secondary) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        'primary-hover': 'rgb(var(--color-primary-hover) / <alpha-value>)',
        'on-primary': 'rgb(var(--color-on-primary) / <alpha-value>)',
        positive: 'rgb(var(--color-positive) / <alpha-value>)',
        info: 'rgb(var(--color-info) / <alpha-value>)',
        attention: 'rgb(var(--color-attention) / <alpha-value>)',
        risk: 'rgb(var(--color-risk) / <alpha-value>)',
        critical: 'rgb(var(--color-critical) / <alpha-value>)',
        disabled: 'rgb(var(--color-disabled) / <alpha-value>)',
        focus: 'rgb(var(--color-focus) / <alpha-value>)',
        // Morning Brief design system (Experience Cycle 1). Namespaced `mb-*`
        // so no existing utility changes. Consumed by migrated surfaces only.
        mb: {
          page: 'rgb(var(--mb-page) / <alpha-value>)',
          surface: 'rgb(var(--mb-surface) / <alpha-value>)',
          inset: 'rgb(var(--mb-inset) / <alpha-value>)',
          ink: 'rgb(var(--mb-ink) / <alpha-value>)',
          secondary: 'rgb(var(--mb-secondary) / <alpha-value>)',
          muted: 'rgb(var(--mb-muted) / <alpha-value>)',
          hairline: 'var(--mb-hairline-color)',
          action: 'rgb(var(--mb-action) / <alpha-value>)',
          'action-hover': 'rgb(var(--mb-action-hover) / <alpha-value>)',
          // Iron Editorial training accent (C2.0). Training interaction/identity only.
          ember: 'rgb(var(--mb-ember) / <alpha-value>)',
          'ember-hover': 'rgb(var(--mb-ember-hover) / <alpha-value>)',
          'on-ember': 'rgb(var(--mb-on-ember) / <alpha-value>)',
          // Fixed Iron Editorial anchors — theme-INDEPENDENT (always dark ink / bone).
          // For fixed-dark surfaces that do not flip with the app theme: the login cover
          // and Gym Mode's dark instrument ground (C2.1-fidelity / C2.2).
          'ink-0': 'rgb(var(--mb-ink-0) / <alpha-value>)',
          'ink-1': 'rgb(var(--mb-ink-1) / <alpha-value>)',
          'ink-2': 'rgb(var(--mb-ink-2) / <alpha-value>)',
          bone: 'rgb(var(--mb-bone) / <alpha-value>)',
          'bone-muted': 'rgb(var(--mb-bone-muted) / <alpha-value>)',
          success: 'rgb(var(--mb-success) / <alpha-value>)',
          caution: 'rgb(var(--mb-caution) / <alpha-value>)',
          error: 'rgb(var(--mb-error) / <alpha-value>)',
          info: 'rgb(var(--mb-info) / <alpha-value>)',
          indigo: {
            50: 'rgb(var(--mb-indigo-50) / <alpha-value>)',
            100: 'rgb(var(--mb-indigo-100) / <alpha-value>)',
            300: 'rgb(var(--mb-indigo-300) / <alpha-value>)',
            500: 'rgb(var(--mb-indigo-500) / <alpha-value>)',
            600: 'rgb(var(--mb-indigo-600) / <alpha-value>)',
            700: 'rgb(var(--mb-indigo-700) / <alpha-value>)',
            900: 'rgb(var(--mb-indigo-900) / <alpha-value>)',
          },
          atm: {
            gold: 'rgb(var(--mb-atm-gold) / <alpha-value>)',
            blue: 'rgb(var(--mb-atm-blue) / <alpha-value>)',
            amber: 'rgb(var(--mb-atm-amber) / <alpha-value>)',
            violet: 'rgb(var(--mb-atm-violet) / <alpha-value>)',
          },
        },
      },
      boxShadow: {
        card: '0 1px 2px rgb(15 23 42 / 0.04), 0 10px 30px rgb(15 23 42 / 0.04)',
        raised: '0 16px 45px rgb(15 23 42 / 0.09)',
        'mb-surface': 'var(--mb-shadow-surface)',
        'mb-overlay': 'var(--mb-shadow-overlay)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        structure: 'var(--mb-font-structure)',
        voice: 'var(--mb-font-voice)',
        stat: 'var(--mb-font-stat)',
        // Iron Editorial typographic roles (C2.0). Not applied to any live surface
        // yet; C2.1 adopts them per migrated surface. Coach serif = coach voice only.
        display: 'var(--mb-font-display)',
        coach: 'var(--mb-font-coach)',
        numeral: 'var(--mb-font-numeral)',
      },
      fontSize: {
        'mb-display-xl': ['3rem', { lineHeight: '3.25rem', letterSpacing: '-0.02em', fontWeight: '700' }],
        'mb-display': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.02em', fontWeight: '700' }],
        'mb-title': ['1.75rem', { lineHeight: '2.125rem', letterSpacing: '-0.01em', fontWeight: '600' }],
        'mb-heading': ['1.375rem', { lineHeight: '1.75rem', letterSpacing: '-0.01em', fontWeight: '600' }],
        'mb-body-lg': ['1.0625rem', { lineHeight: '1.625rem' }],
        'mb-body': ['0.9375rem', { lineHeight: '1.375rem' }],
        'mb-label': ['0.8125rem', { lineHeight: '1.125rem', fontWeight: '500' }],
        'mb-micro': ['0.75rem', { lineHeight: '1rem', fontWeight: '500' }],
      },
      borderRadius: {
        'mb-surface': 'var(--mb-radius-surface)',
        'mb-inset': 'var(--mb-radius-inset)',
        'mb-control': 'var(--mb-radius-control)',
        'mb-tag': 'var(--mb-radius-tag)',
      },
      spacing: {
        'mb-gutter': 'var(--mb-gutter)',
        'mb-section': 'var(--mb-section)',
        'mb-section-tight': 'var(--mb-section-tight)',
        'mb-pad-surface': 'var(--mb-pad-surface)',
        'mb-pad-inset': 'var(--mb-pad-inset)',
      },
      transitionDuration: {
        'mb-micro': 'var(--mb-dur-micro)',
        'mb-structural': 'var(--mb-dur-structural)',
        'mb-entrance': 'var(--mb-dur-entrance)',
        'mb-completion': 'var(--mb-dur-completion)',
      },
      transitionTimingFunction: {
        'mb-standard': 'var(--mb-ease-standard)',
      },
      // The approved Morning Brief motion budget. Durations trace to the --mb-dur-*
      // tokens; all collapse to instant under prefers-reduced-motion (handled globally
      // in index.css), and no state is ever communicated by motion alone.
      keyframes: {
        // Entrance settle — one per screen: a gentle fade + small rise.
        'mb-settle': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        // Inline disclosure expansion.
        'mb-expand': {
          '0%': { opacity: '0', transform: 'translateY(-4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        // Loading — a calm breathe (opacity only; never a shimmer sweep).
        'mb-breathe': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.55' },
        },
        // Completed acknowledgement — a quiet one-time check settle (no confetti).
        'mb-check': {
          '0%': { opacity: '0', transform: 'scale(0.7)' },
          '60%': { opacity: '1', transform: 'scale(1.06)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'mb-settle': 'mb-settle var(--mb-dur-entrance) var(--mb-ease-standard) both',
        'mb-expand': 'mb-expand var(--mb-dur-structural) var(--mb-ease-standard) both',
        'mb-breathe': 'mb-breathe 1800ms var(--mb-ease-standard) infinite',
        'mb-check': 'mb-check var(--mb-dur-completion) var(--mb-ease-standard) both',
      },
      maxWidth: {
        app: '90rem',
        'mb-guidance': '40rem',
        'mb-invite': '30rem',
        'mb-work': '75rem',
        'mb-measure': '68ch',
      },
    },
  },
  plugins: [],
}
