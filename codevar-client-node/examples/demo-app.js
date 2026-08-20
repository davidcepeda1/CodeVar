const express = require("express");
const { createConfig, codevarErrorHandler } = require("../src");

function buildDemoApp({ serverUrl, apiKey }) {
  const app = express();

  const config = createConfig({ serverUrl, apiKey });

  app.get("/boom", (req, res) => {
    throw new TypeError("algo salió mal");
  });

  // Express 4 no captura excepciones de handlers async automáticamente:
  // hay que atraparlas y pasarlas a next(err) para que el error middleware las vea.
  app.get("/boom-async", async (req, res, next) => {
    try {
      await Promise.reject(new RangeError("fallo asíncrono"));
    } catch (err) {
      next(err);
    }
  });

  app.use(codevarErrorHandler(config));

  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    res.status(500).json({ error: err.message });
  });

  return app;
}

module.exports = { buildDemoApp };
