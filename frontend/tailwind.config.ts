import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        wa: {
          bg: '#f0f2f5',
          panel: '#ffffff',
          chatbg: '#efeae2',
          bubbleOut: '#d9fdd3',
          bubbleIn: '#ffffff',
          bubbleHuman: '#fff3c4',
          green: '#00a884',
          greenDark: '#008069',
          text: '#111b21',
          subtext: '#667781',
          border: '#e9edef',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
