const { createConfig } = require("./config");
const { createReporter } = require("./reporter");
const { extractExceptionInfo } = require("./stackUtils");

function buildExtraContext(req) {
  const context = {};

  const userAgent = req.get && req.get("user-agent");
  if (userAgent) context.user_agent = userAgent;

  if (req.query && Object.keys(req.query).length > 0) {
    context.query_params = req.query;
  }

  return context;
}

function codevarErrorHandler(configInput) {
  const config = createConfig(configInput);
  const reporter = createReporter(config);

  // eslint-disable-next-line no-unused-vars
  return async function codevarMiddleware(err, req, res, next) {
    const info = extractExceptionInfo(err);
    console.warn(`codevar captured ${info.exceptionType} at ${info.filePath}:${info.lineNumber}`);

    await reporter.send(info, {
      requestPath: req.path,
      requestMethod: req.method,
      extraContext: buildExtraContext(req),
    });

    next(err);
  };
}

module.exports = { codevarErrorHandler };
