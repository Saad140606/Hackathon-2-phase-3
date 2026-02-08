const path = require('path');

/** @type {import('next').NextConfig} */
module.exports = {
  turbopack: {},
  webpack(config) {
    config.resolve = config.resolve || {};
    config.resolve.alias = Object.assign({}, config.resolve.alias, {
      '@': path.resolve(__dirname, 'src'),
    });
    return config;
  },
};
