import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input:
    'http://127.0.0.1:8000/openapi.json',
  output: {
    format: 'prettier',
    lint: 'eslint',
    path: './src/lib/client',
  },
  plugins: [
    '@hey-api/schemas',
    '@hey-api/client-fetch',
    {
      dates: true,
      name: '@hey-api/transformers',
    },
    {
      enums: 'javascript',
      name: '@hey-api/typescript',
    },
    {
      name: '@hey-api/sdk',
      transformer: true,
    },
    '@tanstack/react-query',
  ],
});
