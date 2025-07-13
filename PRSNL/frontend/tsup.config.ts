import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/**/*.ts'],
  format: ['esm'],
  dts: true,
  clean: true,
  sourcemap: true,
  skipNodeModulesBundle: true,
  treeshake: true,
  minify: false,
  target: 'es2022',
  external: ['svelte', '@sveltejs/kit', 'fs', 'path'],
  splitting: false,
  shims: false,
  onSuccess: 'echo "✅ TypeScript build completed successfully!"',
});
