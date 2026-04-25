export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        panel: "#f0efe8",
        brand: "#1b7f6b",
        ink: "#16241f",
        bubble: "#dcf8c6",
        bubbleDark: "#ffffff"
      },
      boxShadow: {
        soft: "0 18px 40px rgba(12, 37, 30, 0.10)"
      }
    }
  },
  plugins: []
};

