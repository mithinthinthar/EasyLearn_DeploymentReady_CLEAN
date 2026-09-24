function backend(name) {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`${name} is required in Vercel Environment Variables before deployment.`);
  }
  return value.replace(/\/$/, "");
}

const platform = backend("PLATFORM_BACKEND_URL");
const history = backend("HISTORY_BACKEND_URL");
const mathematics = backend("MATH_BACKEND_URL");
const bm = backend("BM_BACKEND_URL");

export const config = {
  outputDirectory: "dist",
  rewrites: [
    { source: "/platform-api/:path*", destination: `${platform}/:path*` },
    { source: "/history-api/:path*", destination: `${history}/:path*` },
    { source: "/math-api/:path*", destination: `${mathematics}/:path*` },
    { source: "/bm-api/:path*", destination: `${bm}/:path*` },
    { source: "/history", destination: "/history/index.html" },
    { source: "/mathematics", destination: "/mathematics/index.html" },
    { source: "/bahasa-melayu", destination: "/bahasa-melayu/index.html" }
  ],
  headers: [
    ...["/platform-api/:path*", "/history-api/:path*", "/math-api/:path*", "/bm-api/:path*"].map((source) => ({
      source,
      headers: [
        { key: "Cache-Control", value: "no-store, max-age=0" },
        { key: "CDN-Cache-Control", value: "no-store" },
        { key: "Vercel-CDN-Cache-Control", value: "no-store" }
      ]
    }))
  ]};
