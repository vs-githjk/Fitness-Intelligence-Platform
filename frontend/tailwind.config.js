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
        positive: 'rgb(var(--color-positive) / <alpha-value>)',
        info: 'rgb(var(--color-info) / <alpha-value>)',
        attention: 'rgb(var(--color-attention) / <alpha-value>)',
        risk: 'rgb(var(--color-risk) / <alpha-value>)',
        critical: 'rgb(var(--color-critical) / <alpha-value>)',
        disabled: 'rgb(var(--color-disabled) / <alpha-value>)',
        focus: 'rgb(var(--color-focus) / <alpha-value>)',
      },
      boxShadow: {
        card: '0 1px 2px rgb(15 23 42 / 0.04), 0 10px 30px rgb(15 23 42 / 0.04)',
        raised: '0 16px 45px rgb(15 23 42 / 0.09)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      maxWidth: {
        app: '90rem',
      },
    },
  },
  plugins: [],
}
