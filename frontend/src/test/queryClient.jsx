import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";

/**
 * Render a component with an isolated QueryClient so tests don't share cache.
 * Returns whatever `render` returns, plus the `queryClient` for assertions.
 *
 * @param {import("react").ReactElement} ui
 * @param {object} [renderOptions]
 * @returns {ReturnType<typeof render> & { queryClient: QueryClient }}
 */
export function renderWithQueryClient(ui, renderOptions) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  const utils = render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
    renderOptions
  );
  return { ...utils, queryClient };
}