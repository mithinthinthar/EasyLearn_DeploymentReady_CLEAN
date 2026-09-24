import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(import.meta.dirname, "..");
const output = resolve(root, "dist");
const npm = process.platform === "win32" ? "npm.cmd" : "npm";

function runNpm(cwd, args, extraEnv = {}) {
  console.log(`\n> ${cwd.replace(root, ".")} :: npm ${args.join(" ")}`);
  const result = spawnSync(npm, args, {
    cwd,
    stdio: "inherit",
    env: { ...process.env, ...extraEnv },
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

function installAndBuild(relativeDir, env) {
  const cwd = resolve(root, relativeDir);
  if (!existsSync(resolve(cwd, "node_modules"))) runNpm(cwd, ["ci"]);
  runNpm(cwd, ["run", "build"], env);
  return cwd;
}

rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
cpSync(resolve(root, "portal"), output, { recursive: true });

const history = installAndBuild("subjects/history/frontend", {
  CI: "false",
  PUBLIC_URL: "/history",
  REACT_APP_HISTORY_API_URL: "/history-api",
  REACT_APP_SHARED_AUTH_URL: "/platform-api",
  REACT_APP_PORTAL_URL: "/",
  REACT_APP_LOCAL_MODE: "false",
});
cpSync(resolve(history, "build"), resolve(output, "history"), { recursive: true });

const mathematics = installAndBuild("subjects/mathematics/frontend", {
  CI: "false",
  PUBLIC_URL: "/mathematics",
  REACT_APP_API_BASE_URL: "/math-api",
  REACT_APP_SHARED_AUTH_URL: "/platform-api",
  REACT_APP_PORTAL_URL: "/",
  REACT_APP_LOCAL_MODE: "false",
});
cpSync(resolve(mathematics, "build"), resolve(output, "mathematics"), { recursive: true });

const bm = installAndBuild("subjects/bahasa_melayu/frontend", {
  VITE_BASE_PATH: "/bahasa-melayu/",
  VITE_API_BASE_URL: "/bm-api",
  VITE_SHARED_AUTH_URL: "/platform-api",
  VITE_PORTAL_URL: "/",
  VITE_LOCAL_MODE: "false",
});
cpSync(resolve(bm, "dist"), resolve(output, "bahasa-melayu"), { recursive: true });

console.log("\nEasyLearn production frontend created in ./dist");
