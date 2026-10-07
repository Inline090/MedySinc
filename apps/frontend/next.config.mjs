/** @type {import('next').NextConfig} */
const nextConfig = {
  // Produces a self-contained server with only the files it needs, so the runtime
  // image does not carry node_modules (see apps/frontend/Dockerfile).
  output: "standalone",
};

export default nextConfig;
