function createReporter(config) {
  async function send(info, { requestPath = null, requestMethod = null, extraContext = null } = {}) {
    const payload = {
      project_api_key: config.apiKey,
      exception_type: info.exceptionType,
      file_path: info.filePath,
      line_number: info.lineNumber,
      stack_trace: info.stackTrace,
      request_path: requestPath,
      request_method: requestMethod,
      extra_context: extraContext,
    };

    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), config.timeout);

      await fetch(`${config.serverUrl}/api/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timer);
    } catch (err) {
      // CodeVAR nunca debe romper la app que instrumenta: si el
      // servidor no responde, se registra el fallo y se sigue.
      console.warn(`codevar: failed to report event to ${config.serverUrl}`, err.message);
    }
  }

  return { send };
}

module.exports = { createReporter };
