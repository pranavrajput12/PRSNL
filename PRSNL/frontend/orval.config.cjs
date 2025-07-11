module.exports = {
  prsnl: {
    input: {
      target: '../backend/openapi.json',
    },
    output: {
      mode: 'split',
      target: 'src/lib/api/generated.ts',
      schemas: 'src/lib/types/generated',
      client: 'svelte-query',
      prettier: true,
      override: {
        mutator: {
          path: 'src/lib/api/mutator.ts',
          name: 'customInstance',
        },
      },
    },
  },
};