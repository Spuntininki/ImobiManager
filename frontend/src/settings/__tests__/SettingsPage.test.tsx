import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";

import { renderWithQueryClient } from "@/test/queryClient";
import { SettingsPage } from "@/settings/SettingsPage";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/services/ownerService", () => ({
  listOwners: vi.fn(),
  createOwner: vi.fn(),
  updateOwner: vi.fn(),
  deleteOwner: vi.fn(),
  createOwnerDocument: vi.fn(),
  deleteOwnerDocument: vi.fn(),
  listOwnerDocuments: vi.fn(),
}));

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no owners exist", async () => {
    const { listOwners } = await import("@/services/ownerService");
    vi.mocked(listOwners).mockResolvedValue([]);
    renderWithQueryClient(<SettingsPage />);
    expect(
      await screen.findByText(/nenhum proprietário cadastrado/i),
    ).toBeInTheDocument();
  });

  it("renders owners in the table on happy path", async () => {
    const { listOwners } = await import("@/services/ownerService");
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "João Silva" },
      { id: 2, name: "Maria Souza" },
    ]);
    renderWithQueryClient(<SettingsPage />);
    expect(await screen.findByText("João Silva")).toBeInTheDocument();
    expect(await screen.findByText("Maria Souza")).toBeInTheDocument();
  });

  it("shows success toast on delete", async () => {
    const { listOwners, deleteOwner } = await import(
      "@/services/ownerService"
    );
    vi.mocked(deleteOwner).mockResolvedValue(undefined);
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "João Silva" },
    ]);
    const user = userEvent.setup();
    renderWithQueryClient(<SettingsPage />);
    const deleteBtn = await screen.findByRole("button", {
      name: /excluir/i,
    });
    await user.click(deleteBtn);
    const { toast } = await import("sonner");
    await vi.waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        "Proprietário excluído com sucesso.",
      );
    });
  });
});
