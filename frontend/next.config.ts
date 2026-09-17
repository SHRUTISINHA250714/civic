import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  turbopack: {
    root: typeof __dirname !== "undefined" ? __dirname : process.cwd(),
  },
};

export default nextConfig;
