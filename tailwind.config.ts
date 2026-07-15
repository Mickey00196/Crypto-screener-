import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        base: {
          50: '#f5f7fa',
          100: '#e9edf3',
          200: '#0e1116',
          background: '#0a0c10',
          surface: '#12151b',
          raised: '#161a22',
          border: '#1f2430',
          borderLight: '#2a3040',
        },
        accent: {
          DEFAULT: '#5b8cff',
          dim: '#3d5fc4',
          glow: '#7ea3ff',
        },
        gain: {
          DEFAULT: '#2fd47a',
          dim: '#1c9a58',
          bg: 'rgba(47,212,122,0.12)',
        },
        loss: {
          DEFAULT: '#ff5c72',
          dim: '#c23b4f',
          bg: 'rgba(255,92,114,0.12)',
        },
        neutral: {
          DEFAULT: '#8a92a3',
        },
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 1px 3px rgba(0,0,0,0.4)',
        glow: '0 0 0 1px rgba(91,140,255,0.4), 0 0 24px rgba(91,140,255,0.15)',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
      keyframes: {
        'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } },
        'slide-up': { from: { opacity: '0', transform: 'translateY(6px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        shimmer: { '0%': { backgroundPosition: '-400px 0' }, '100%': { backgroundPosition: '400px 0' } },
        'pulse-soft': { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.55' } },
      },
      animation: {
        'fade-in': 'fade-in 0.25s ease-out',
        'slide-up': 'slide-up 0.3s cubic-bezier(0.16,1,0.3,1)',
        shimmer: 'shimmer 1.6s infinite linear',
        'pulse-soft': 'pulse-soft 1.8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
