import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const serverDirectory = join(process.cwd(), "dist", "server");
mkdirSync(serverDirectory, { recursive: true });
writeFileSync(join(serverDirectory, "index.js"), `export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  }
};
`, "utf8");
