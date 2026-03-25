const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const kill = require("tree-kill");
const waitOn = require("wait-on");

const rootDir = path.resolve(__dirname, "..");
const frontendDir = path.join(rootDir, "frontend");
const backendDir = path.join(rootDir, "backend");

let backendProcess = null;
let frontendProcess = null;
let backendStartedByDesktop = false;
let frontendStartedByDesktop = false;

function npmCommand() {
  return process.platform === "win32" ? "npm.cmd" : "npm";
}

function backendPythonCommand() {
  const venvPython =
    process.platform === "win32"
      ? path.join(backendDir, ".venv", "Scripts", "python.exe")
      : path.join(backendDir, ".venv", "bin", "python");

  if (fs.existsSync(venvPython)) {
    return venvPython;
  }
  return process.platform === "win32" ? "python" : "python3";
}

function spawnService(name, command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1"
    },
    stdio: ["ignore", "pipe", "pipe"]
  });

  child.stdout.on("data", (data) => {
    process.stdout.write(`[${name}] ${data}`);
  });
  child.stderr.on("data", (data) => {
    process.stderr.write(`[${name}] ${data}`);
  });
  child.on("exit", (code) => {
    process.stdout.write(`[${name}] exited with code ${code}\n`);
  });

  return child;
}

function runCommand(name, command, args, cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1"
      },
      stdio: ["ignore", "pipe", "pipe"]
    });

    child.stdout.on("data", (data) => {
      process.stdout.write(`[${name}] ${data}`);
    });
    child.stderr.on("data", (data) => {
      process.stderr.write(`[${name}] ${data}`);
    });

    child.on("error", (error) => reject(error));
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${name} exited with code ${code}`));
      }
    });
  });
}

async function waitForServices() {
  await waitOn({
    resources: [
      "http-get://127.0.0.1:8000/health",
      "http-get://127.0.0.1:3001/dashboard"
    ],
    timeout: 120000,
    interval: 300,
    validateStatus: (status) => status >= 200 && status < 500
  });
}

async function isServiceUp(resource) {
  try {
    await waitOn({
      resources: [resource],
      timeout: 1500,
      interval: 200,
      validateStatus: (status) => status >= 200 && status < 500
    });
    return true;
  } catch {
    return false;
  }
}

async function startServices() {
  const backendRunning = await isServiceUp("http-get://127.0.0.1:8000/health");
  const frontendRunning = await isServiceUp("http-get://127.0.0.1:3001/dashboard");

  if (!backendRunning) {
    backendProcess = spawnService(
      "backend",
      backendPythonCommand(),
      ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
      backendDir
    );
    backendStartedByDesktop = true;
  }

  if (!frontendRunning) {
    await runCommand("frontend-build", npmCommand(), ["run", "build"], frontendDir);
    frontendProcess = spawnService(
      "frontend",
      npmCommand(),
      ["run", "start", "--", "--hostname", "127.0.0.1", "--port", "3001"],
      frontendDir
    );
    frontendStartedByDesktop = true;
  }

  await waitForServices();
}

function killProcess(child) {
  return new Promise((resolve) => {
    if (!child || !child.pid) {
      resolve();
      return;
    }
    kill(child.pid, "SIGTERM", () => resolve());
  });
}

async function stopServices() {
  const kills = [];
  if (frontendStartedByDesktop) kills.push(killProcess(frontendProcess));
  if (backendStartedByDesktop) kills.push(killProcess(backendProcess));
  await Promise.all(kills);
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1120,
    minHeight: 760,
    title: "ledgerlyftHQ",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js")
    }
  });

  win.loadURL("http://127.0.0.1:3001/dashboard");
}

app.whenReady().then(async () => {
  try {
    await startServices();
    createWindow();
  } catch (error) {
    await dialog.showMessageBox({
      type: "error",
      title: "ledgerlyftHQ Startup Error",
      message: "Could not start ledgerlyftHQ services.",
      detail: error instanceof Error ? error.message : String(error)
    });
    await stopServices();
    app.quit();
  }
});

app.on("before-quit", async () => {
  await stopServices();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
