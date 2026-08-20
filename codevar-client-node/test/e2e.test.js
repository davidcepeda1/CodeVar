const assert = require("node:assert");
const path = require("node:path");
const fs = require("node:fs");
const { spawn } = require("node:child_process");
const { buildDemoApp } = require("../examples/demo-app");

const SERVER_DIR = path.join(__dirname, "..", "..", "codevar-server");
const PYTHON = path.join(SERVER_DIR, ".venv", "bin", "python");
const DB_PATH = path.join(__dirname, "_e2e_node.db");
const CODEVAR_PORT = 8099;
const DEMO_APP_PORT = 8098;
const CODEVAR_URL = `http://127.0.0.1:${CODEVAR_PORT}`;
const DEMO_APP_URL = `http://127.0.0.1:${DEMO_APP_PORT}`;

async function waitForServer(url, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      await fetch(url);
      return; // cualquier respuesta HTTP significa que el server ya está escuchando
    } catch {
      // aún no acepta conexiones
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`servidor no respondió en ${url} a tiempo`);
}

async function main() {
  fs.rmSync(DB_PATH, { force: true });

  const codevarServer = spawn(
    PYTHON,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(CODEVAR_PORT)],
    {
      cwd: SERVER_DIR,
      env: { ...process.env, DATABASE_URL: `sqlite:///${DB_PATH}` },
      stdio: "ignore",
    }
  );

  let demoServer;

  try {
    await waitForServer(`${CODEVAR_URL}/`);

    const createRes = await fetch(`${CODEVAR_URL}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "name=node-demo-app",
      redirect: "manual",
    });
    const location = createRes.headers.get("location");
    const apiKey = new URL(location, CODEVAR_URL).searchParams.get("api_key");
    assert.ok(apiKey, "no se pudo crear el proyecto de prueba en codevar-server");

    const app = buildDemoApp({ serverUrl: CODEVAR_URL, apiKey });
    demoServer = app.listen(DEMO_APP_PORT);
    await waitForServer(`${DEMO_APP_URL}/`);

    // dispara el mismo error 3 veces -> debe agruparse en un solo error_group
    for (let i = 0; i < 3; i++) {
      await fetch(`${DEMO_APP_URL}/boom`);
    }
    // dispara el error async -> debe crear un segundo error_group
    await fetch(`${DEMO_APP_URL}/boom-async?debug=1`, {
      headers: { "user-agent": "codevar-node-e2e/1.0" },
    });

    // dar tiempo a que los POST /api/events (fire-and-forget) del reporter lleguen
    await new Promise((resolve) => setTimeout(resolve, 500));

    const groupsRes = await fetch(`${CODEVAR_URL}/api/errors?api_key=${apiKey}`);
    const groups = await groupsRes.json();

    assert.strictEqual(groups.length, 2, `se esperaban 2 error groups, hubo ${groups.length}`);

    const typeError = groups.find((g) => g.exception_type === "TypeError");
    assert.ok(typeError, "no se encontró el TypeError capturado");
    assert.strictEqual(typeError.event_count, 3, "el TypeError debía agruparse en 3 ocurrencias");

    const rangeError = groups.find((g) => g.exception_type === "RangeError");
    assert.ok(rangeError, "no se encontró el RangeError async capturado");

    const typeErrorDetailRes = await fetch(
      `${CODEVAR_URL}/api/errors/${typeError.id}?api_key=${apiKey}`
    );
    const typeErrorDetail = await typeErrorDetailRes.json();
    const typeErrorEvent = typeErrorDetail.events[0];
    assert.strictEqual(typeErrorEvent.request_path, "/boom");
    assert.strictEqual(typeErrorEvent.request_method, "GET");
    assert.ok(typeErrorEvent.stack_trace.includes("TypeError"));

    const rangeErrorDetailRes = await fetch(
      `${CODEVAR_URL}/api/errors/${rangeError.id}?api_key=${apiKey}`
    );
    const rangeErrorDetail = await rangeErrorDetailRes.json();
    const rangeErrorEvent = rangeErrorDetail.events[0];
    assert.strictEqual(rangeErrorEvent.extra_context.user_agent, "codevar-node-e2e/1.0");
    assert.deepStrictEqual(rangeErrorEvent.extra_context.query_params, { debug: "1" });

    console.log("OK: codevar-client-node reportó y agrupó errores reales end-to-end");
  } finally {
    if (demoServer) demoServer.close();
    codevarServer.kill();
    fs.rmSync(DB_PATH, { force: true });
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
