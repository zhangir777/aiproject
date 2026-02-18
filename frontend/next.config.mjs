/** @type {import('next').NextConfig} */
const nextConfig = {
  // Разрешить работу с Leaflet на клиенте
  webpack: (config) => {
    config.resolve.fallback = { fs: false };
    return config;
  },
};

export default nextConfig;
