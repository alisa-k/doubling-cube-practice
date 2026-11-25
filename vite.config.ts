import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig, type Plugin } from "vite";

function puzzleData(): Plugin {
  const entry = "virtual:puzzle-data";
  const batchPrefix = `${entry}/`;
  const source = fileURLToPath(new URL("./public/puzzles.json", import.meta.url));
  const firstBatchSize = 12;
  const batchSize = 100;
  let puzzles: unknown[] | undefined;

  return {
    name: "puzzle-data",
    resolveId(id) {
      if (id === entry || id.startsWith(batchPrefix)) return `\0${id}`;
    },
    load(id) {
      if (id !== `\0${entry}` && !id.startsWith(`\0${batchPrefix}`)) return;

      this.addWatchFile(source);
      puzzles ??= JSON.parse(readFileSync(source, "utf8"));
      if (!Array.isArray(puzzles) || puzzles.length === 0) {
        throw new Error("The puzzle dataset must be a non-empty array.");
      }

      if (id === `\0${entry}`) {
        const loaders = [];
        for (let start = firstBatchSize; start < puzzles.length; start += batchSize) {
          loaders.push(`() => import(${JSON.stringify(`${batchPrefix}${start}`)})`);
        }
        return `
          export const firstBatch = ${JSON.stringify(puzzles.slice(0, firstBatchSize))};
          export const laterBatches = [${loaders.join(",\n")}];
          export const batchSize = ${batchSize};
          export const puzzleCount = ${puzzles.length};
        `;
      }

      const start = Number(id.slice(batchPrefix.length + 1));
      return `export default ${JSON.stringify(puzzles.slice(start, start + batchSize))};`;
    },
    watchChange(id) {
      if (id === source) puzzles = undefined;
    },
  };
}

export default defineConfig({
  // Relative asset paths work both at localhost and under a GitHub Pages
  // project path such as /doubling-cube-practice/.
  base: "./",
  // The source JSON is bundled by puzzleData rather than copied to the site.
  publicDir: false,
  plugins: [puzzleData()],
});
