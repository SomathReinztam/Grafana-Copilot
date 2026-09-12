import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Hackathon: no bloquear el build de producción por lint/tipos.
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
};

export default nextConfig;
