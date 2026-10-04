import type { NextConfig } from "next";

// The API container, reached over the compose network. Browsers only ever talk to this app.
const api = process.env.API_URL ?? "http://app:8000";

const config: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    return [
      { source: "/v1/:path*", destination: `${api}/v1/:path*` },
      { source: "/health", destination: `${api}/health` },
      { source: "/health/ready", destination: `${api}/health/ready` },
      { source: "/docs", destination: `${api}/docs` },
      { source: "/openapi.json", destination: `${api}/openapi.json` },
    ];
  },
};

export default config;
