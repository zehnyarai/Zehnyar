import { defineConfig } from 'vitest/config'

export default defineConfig({
  // Node tests stay fast; DOM tests opt in with a @vitest-environment jsdom docblock.
  test: { include: ['src/**/*.test.ts', 'src/**/*.test.tsx'], environment: 'node' },
})
