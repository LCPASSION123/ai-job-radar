import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const distDirectory = join(process.cwd(), "dist");
const assetsDirectory = join(distDirectory, "assets");
const serverDirectory = join(distDirectory, "server");

// The public Sites runtime invokes dist/server/index.js directly.  Bundle the
// small Vite application into the returned document so the public demo does
// not depend on a host-specific static-asset binding.
const assets = readdirSync(assetsDirectory);
const scriptName = assets.find((name) => name.startsWith("index-") && name.endsWith(".js"));
const styleName = assets.find((name) => name.startsWith("index-") && name.endsWith(".css"));

if (!scriptName || !styleName) {
  throw new Error("Expected Vite JavaScript and CSS assets were not generated.");
}

const script = readFileSync(join(assetsDirectory, scriptName), "utf8");
const style = readFileSync(join(assetsDirectory, styleName), "utf8");
const document = `<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI Job Radar</title><style>${style}</style></head><body><div id="root"></div><script type="module">${script}</script></body></html>`;

mkdirSync(serverDirectory, { recursive: true });
writeFileSync(join(serverDirectory, "index.js"), `const document = ${JSON.stringify(document)};

export default {
  async fetch() {
    return new Response(document, {
      headers: {
        "content-type": "text/html; charset=UTF-8",
        "cache-control": "no-store"
      }
    });
  }
};
`, "utf8");
