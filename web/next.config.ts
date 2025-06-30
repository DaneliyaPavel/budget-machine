import withPWA from "next-pwa";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {};

export default withPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
  ...nextConfig,
});
