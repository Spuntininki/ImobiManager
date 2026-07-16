import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";

import { renderWithQueryClient } from "@/test/queryClient";
import { PropertiesPage } from "@/properties/PropertiesPage";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/services/ownerService", () => ({
  listOwners: vi.fn(),
}));

vi.mock("@/services/addressService", () => ({
  listAddressesByOwner: vi.fn(),
  createAddress: vi.fn(),
  updateAddress: vi.fn(),
  deleteAddress: vi.fn(),
}));

describe("PropertiesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no addresses exist", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listAddressesByOwner } = await import(
      "@/services/addressService"
    );
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "Proprietário" },
    ]);
    vi.mocked(listAddressesByOwner).mockResolvedValue([]);
    renderWithQueryClient(<PropertiesPage />);
    expect(
      await screen.findByText(/nenhum imóvel cadastrado/i),
    ).toBeInTheDocument();
  });

  it("renders addresses in the table on happy path", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listAddressesByOwner } = await import(
      "@/services/addressService"
    );
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "Proprietário" },
    ]);
    vi.mocked(listAddressesByOwner).mockResolvedValue([
      {
        id: 1,
        street_name: "Rua das Flores",
        number: "123",
        complement: null,
        neighborhood: "Centro",
        city: "São Paulo",
        state: "SP",
        zip_code: "01000-000",
        type: "HOUSE",
      },
    ]);
    renderWithQueryClient(<PropertiesPage />);
    expect(
      await screen.findByText("Rua das Flores"),
    ).toBeInTheDocument();
  });

  it("shows success toast on delete", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listAddressesByOwner, deleteAddress } = await import(
      "@/services/addressService"
    );
    vi.mocked(deleteAddress).mockResolvedValue(undefined);
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "Proprietário" },
    ]);
    vi.mocked(listAddressesByOwner).mockResolvedValue([
      {
        id: 1,
        street_name: "Rua A",
        number: "10",
        complement: null,
        neighborhood: "Centro",
        city: "São Paulo",
        state: "SP",
        zip_code: "01000-000",
        type: "HOUSE",
      },
    ]);
    const user = userEvent.setup();
    renderWithQueryClient(<PropertiesPage />);
    const deleteBtn = await screen.findByRole("button", {
      name: /excluir/i,
    });
    await user.click(deleteBtn);
    const { toast } = await import("sonner");
    await vi.waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        "Imóvel excluído com sucesso.",
      );
    });
  });
});
