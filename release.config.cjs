const config = require("@nicxe/semantic-release-config")({
  componentDir: "custom_components/met_rain_risk",
  manifestPath: "custom_components/met_rain_risk/manifest.json",
  projectName: "MET Rain Risk",
  repoSlug: "Nicxe/met_rain_risk"
}
);

const githubPlugin = config.plugins.find(
  (plugin) => Array.isArray(plugin) && plugin[0] === "@semantic-release/github"
);

if (githubPlugin?.[1]) {
  githubPlugin[1].successCommentCondition = false;
}

module.exports = config;
