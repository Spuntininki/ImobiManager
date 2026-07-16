import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";

import { renderWithQueryClient } from "@/test/queryClient";
import { OwnerDialog } from "@/settings/components/OwnerDialog";

vi.mock("@/hooks/useOwnerDocuments", () => ({
  useOwnerDocuments: () => ({
    documents: [],
    isLoading: false,
    error: "",
  }),
}));

describe("OwnerDialog", () => {
  const mockSubmit = vi.fn<
    (
      name: string,
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
      <OwnerDialog onSubmit={mockSubmit} />,
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

  it("shows error when duplicate document types are added", async () => {
    const { user } = setup();
    await openDialog(user);
    await user.type(screen.getByLabelText("Nome"), "João Silva");
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
    await user.type(screen.getByLabelText("Nome"), "João Silva");
    await user.click(
      screen.getByRole("button", { name: /adicionar documento/i }),
    );
    await user.type(
      screen.getByPlaceholderText("00.000.000-0"),
      "1234",
    );
    await user.click(screen.getByRole("button", { name: /criar/i }));
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledTimes(1);
    });
    const [name] = mockSubmit.mock.calls[0] as unknown as [string];
    expect(name).toBe("João Silva");
  });

  it("shows inline error for 409 duplicate document", async () => {
    mockSubmit.mockRejectedValue(
      new Error(
        "Já existe um documento deste tipo para este proprietário.",
      ),
    );
    const { user } = setup();
    await openDialog(user);
    await user.type(screen.getByLabelText("Nome"), "João Silva");
    await user.click(
      screen.getByRole("button", { name: /adicionar documento/i }),
    );
    await user.type(
      screen.getByPlaceholderText("00.000.000-0"),
      "1234",
    );
    await user.click(screen.getByRole("button", { name: /criar/i }));
    expect(
      await screen.findByText(
        "Já existe um documento deste tipo para este proprietário.",
      ),
    ).toBeInTheDocument();
  });
});
