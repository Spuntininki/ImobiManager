import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";

import { renderWithQueryClient } from "@/test/queryClient";
import { RenterDialog } from "@/tenants/components/RenterDialog";

vi.mock("@/hooks/useRenterDocuments", () => ({
  useRenterDocuments: () => ({
    documents: [],
    isLoading: false,
    error: "",
  }),
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

describe("RenterDialog", () => {
  const mockSubmit = vi.fn<
    (
      payload: Record<string, unknown>,
      documents: unknown[],
      initialDocuments: unknown[],
      onClose: () => void,
    ) => Promise<void>
  >();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  function setup() {
    const user = userEvent.setup();
    const utils = renderWithQueryClient(
      <RenterDialog onSubmit={mockSubmit} />,
    );
    return { user, ...utils };
  }

  async function openDialog(
    user: ReturnType<typeof userEvent.setup>,
  ) {
    await user.click(screen.getByRole("button", { name: /adicionar/i }));
  }

  it("shows validation error when name is empty", async () => {
    const { user } = setup();
    await openDialog(user);
    await user.click(screen.getByRole("button", { name: /criar/i }));
    expect(
      await screen.findByText("Nome é obrigatório."),
    ).toBeInTheDocument();
  });

  it("shows validation error when phone is too short", async () => {
    const { user } = setup();
    await openDialog(user);
    await user.type(screen.getByLabelText("Nome"), "Maria Souza");
    await user.type(screen.getByLabelText("Contato principal"), "1");
    await user.click(screen.getByRole("button", { name: /criar/i }));
    expect(
      await screen.findByText("Telefone deve ter 10 ou 11 dígitos."),
    ).toBeInTheDocument();
  });

  it("shows error when duplicate document types are added", async () => {
    const { user } = setup();
    await openDialog(user);
    await user.type(screen.getByLabelText("Nome"), "Maria Souza");
    await user.click(
      screen.getByRole("button", { name: /adicionar documento/i }),
    );
    await user.click(
      screen.getByRole("button", { name: /adicionar documento/i }),
    );
    await user.click(screen.getByRole("button", { name: /criar/i }));
    expect(
      await screen.findByText(
        "Não é permitido mais de um documento do mesmo tipo.",
      ),
    ).toBeInTheDocument();
  });

  it("calls onSubmit with the correct payload on happy path", async () => {
    mockSubmit.mockResolvedValue(undefined);
    const { user } = setup();
    await openDialog(user);
    await user.type(screen.getByLabelText("Nome"), "Maria Souza");
    await user.type(
      screen.getByLabelText("Contato principal"),
      "11999999999",
    );
    await user.click(screen.getByRole("button", { name: /criar/i }));
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledTimes(1);
    });
    const [payload, documents] = mockSubmit.mock.calls[0] as unknown as [
      Record<string, unknown>,
      unknown[],
    ];
    expect(payload).toEqual({
      name: "Maria Souza",
      primary_contact: "11999999999",
      secondary_contact: null,
      email: null,
    });
    expect(documents).toEqual([]);
  });

  it("shows toast error on non-409 submit failure", async () => {
    mockSubmit.mockRejectedValue(
      new Error("Não foi possível criar o inquilino."),
    );
    const { user } = setup();
    await openDialog(user);
    await user.type(screen.getByLabelText("Nome"), "Maria Souza");
    await user.type(
      screen.getByLabelText("Contato principal"),
      "11999999999",
    );
    await user.click(screen.getByRole("button", { name: /criar/i }));
    const { toast } = await import("sonner");
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Não foi possível criar o inquilino.",
      );
    });
  });
});
