const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Fonts and local JSON ship inside the bundle so the app is fully offline.
config.resolver.assetExts = Array.from(new Set([...config.resolver.assetExts, 'ttf', 'otf']));

module.exports = config;
