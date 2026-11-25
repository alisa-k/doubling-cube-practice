declare module "virtual:puzzle-data" {
  export const firstBatch: unknown[];
  export const laterBatches: (() => Promise<{ default: unknown[] }>)[];
  export const batchSize: number;
  export const puzzleCount: number;
}
