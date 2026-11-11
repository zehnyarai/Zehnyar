const { withAppBuildGradle } = require('@expo/config-plugins');

const withMyKitRepository = (config) => {
  return withAppBuildGradle(config, (config) => {
    const contents = config.modResults.contents;
    if (!contents.includes('maven.myket.ir')) {
      config.modResults.contents = contents.replace(
        /repositories\s*\{/,
        `repositories {\n        maven { url 'https://maven.myket.ir' }`
      );
    }
    return config;
  });
};

module.exports = withMyKitRepository;
