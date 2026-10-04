import path from 'node:path';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Monorepo: trace files from the repository root, not from a stray lockfile.
  outputFileTracingRoot: path.join(__dirname, '..'),
};

export default nextConfig;
