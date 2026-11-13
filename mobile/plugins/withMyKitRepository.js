const { withSettingsGradle, withProjectBuildGradle } = require('@expo/config-plugins');

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
module.exports = (config) => withProjectBuildGradle(withSettingsRepository(config), (mod) => {
  if (!mod.modResults.contents.includes('maven.myket.ir')) {
    mod.modResults.contents += `\nallprojects {\n  repositories {\n    maven { url 'https://maven.myket.ir' }\n  }\n}\n`;
  }
  return mod;
});
