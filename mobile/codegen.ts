import "dotenv/config";

import type { CodegenConfig } from "@graphql-codegen/cli";

// Introspects the live GraphQL schema, so the backend (app/graphql, Phase 1)
// must be running locally when you run `npm run codegen`. Uses the same
// EXPO_PUBLIC_API_URL as the app itself (see .env.example) so there's one
// source of truth for "where's the backend."
const apiUrl = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

const config: CodegenConfig = {
  schema: `${apiUrl}/graphql`,
  documents: ["src/**/*.graphql"],
  generates: {
    "src/generated/graphql.tsx": {
      plugins: ["typescript", "typescript-operations", "typescript-react-apollo"],
      config: {
        withHooks: true,
      },
    },
  },
};

export default config;
