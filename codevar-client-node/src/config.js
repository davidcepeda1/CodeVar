function createConfig({ serverUrl, apiKey, timeout = 2000 }) {
  if (!serverUrl) throw new Error("codevar: serverUrl is required");
  if (!apiKey) throw new Error("codevar: apiKey is required");

  return {
    serverUrl: serverUrl.replace(/\/$/, ""),
    apiKey,
    timeout,
  };
}

module.exports = { createConfig };
