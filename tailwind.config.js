/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-page': 'var(--bg-page)',
        'bg-surface': 'var(--bg-surface)',
        'bg-subtle': 'var(--bg-subtle)',
        'bg-hover': 'var(--bg-hover)',
        'accent': {
          DEFAULT: 'var(--accent)',
          dark: 'var(--accent-dark)',
          light: 'var(--accent-light)',
        },
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',
        'border': 'var(--border)',
        'border-strong': 'var(--border-strong)',
        'success': {
          text: 'var(--success-text)',
          bg: 'var(--success-bg)',
          border: 'var(--success-border)',
        },
        'warning': {
          text: 'var(--warning-text)',
          bg: 'var(--warning-bg)',
          border: 'var(--warning-border)',
        },
        'error': {
          text: 'var(--error-text)',
          bg: 'var(--error-bg)',
          border: 'var(--error-border)',
        },
        'info': {
          text: 'var(--info-text)',
          bg: 'var(--info-bg)',
          border: 'var(--info-border)',
        },
        'partial': {
          text: 'var(--partial-text)',
          bg: 'var(--partial-bg)',
          border: 'var(--partial-border)',
        },
        'completed': {
          text: 'var(--completed-text)',
          bg: 'var(--completed-bg)',
          border: 'var(--completed-border)',
        },
      },
    },
  },
  plugins: [],
}