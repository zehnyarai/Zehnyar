const { withSettingsGradle, withProjectBuildGradle, withAppBuildGradle } = require('@expo/config-plugins');

// Gradle resolves Android dependencies from settings.gradle's repository list.
// Adding Maven only to an app/module build.gradle does not make it available
// when dependencyResolutionManagement controls repository resolution.
function matchingBrace(source, open) {
  let depth = 0;
  for (let i = open; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1;
    if (source[i] === '}') {
      depth -= 1;
      if (depth === 0) return i;
    }
  }
  throw new Error('Cannot locate closing brace in settings.gradle');
}

const withSettingsRepository = (config) => withSettingsGradle(config, (mod) => {
  const source = mod.modResults.contents;
  if (source.includes('maven.myket.ir')) return mod;
  const management = /dependencyResolutionManagement\s*\{/.exec(source);
  if (!management) {
    mod.modResults.contents = `${source.trimEnd()}\n\ndependencyResolutionManagement {\n  repositories {\n    google()\n    mavenCentral()\n    maven { url 'https://maven.myket.ir' }\n  }\n}\n`;
    return mod;
  }
  const start = management.index + management[0].length - 1;
  const end = matchingBrace(source, start);
  const section = source.slice(start + 1, end);
  const repositories = /repositories\s*\{/.exec(section);
  if (!repositories) {
    mod.modResults.contents = `${source.slice(0, end)}\n  repositories {\n    google()\n    mavenCentral()\n    maven { url 'https://maven.myket.ir' }\n  }\n${source.slice(end)}`;
    return mod;
  }
  const insert = start + 1 + repositories.index + repositories[0].length;
  mod.modResults.contents = `${source.slice(0, insert)}\n    maven { url 'https://maven.myket.ir' }${source.slice(insert)}`;
  return mod;
});

// Expo/React Native versions that use project repositories also need the root
// project repository list. Module-local repositories are not inherited by :app.
const withMyketRepositories = (config) => withProjectBuildGradle(withSettingsRepository(config), (mod) => {
  if (!mod.modResults.contents.includes('maven.myket.ir')) {
    mod.modResults.contents += `\nallprojects {\n  repositories {\n    maven { url 'https://maven.myket.ir' }\n  }\n}\n`;
  }
  return mod;
});

// Placeholders from the Myket SDK's AAR manifest must be supplied by the app;
// setting them in the library module does not satisfy the app's manifest merge.
const withMyketManifestPlaceholders = (config) => withAppBuildGradle(config, (mod) => {
  // logging-interceptor and jspecify both ship this OSGi metadata file.
  // It is not an Android runtime resource; exclude only this exact path.
  const osgiMetadata = 'META-INF/versions/9/OSGI-INF/MANIFEST.MF';
  if (!mod.modResults.contents.includes("excludes += '" + osgiMetadata + "'")) {
    const packaging = /packagingOptions\s*\{/;
    if (!packaging.test(mod.modResults.contents)) throw new Error('Cannot find Android app packagingOptions for Myket');
    mod.modResults.contents = mod.modResults.contents.replace(packaging, `packagingOptions {
        resources { excludes += '${osgiMetadata}' }`);
  }
  const contents = mod.modResults.contents;
  if (contents.includes("marketApplicationId: 'ir.mservices.market'")) return mod;
  const defaultConfig = /defaultConfig\s*\{/;
  if (!defaultConfig.test(contents)) throw new Error('Cannot find Android app defaultConfig for Myket manifest placeholders');
  mod.modResults.contents = contents.replace(defaultConfig, `defaultConfig {
        manifestPlaceholders = [
          marketApplicationId: 'ir.mservices.market',
          marketBindAddress: 'ir.mservices.market.InAppBillingService.BIND',
          marketPermission: 'ir.mservices.market.BILLING'
        ]`);
  return mod;
});

module.exports = (config) => withMyketManifestPlaceholders(withMyketRepositories(config));
