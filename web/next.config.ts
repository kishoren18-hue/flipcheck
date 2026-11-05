import type { NextConfig } from "next";

// In development the FastAPI server runs separately on :8000 (see `npm run dev`).
// On Vercel, api/index.py is deployed as a Python function and serves /api/py/*.
const nextConfig: NextConfig = {
  rewrites: async () => [
    {
      source: "/api/py/:path*",
      destination: process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000/api/py/:path*" : "/api/",
    },
  ],
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
