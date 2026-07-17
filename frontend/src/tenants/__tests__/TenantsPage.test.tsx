import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

import { renderWithQueryClient } from "@/test/queryClient";
import { TenantsPage } from "@/tenants/TenantsPage";

vi.mock("@/services/ownerService", () => ({
  listOwners: vi.fn(),
}));

vi.mock("@/services/renterService", () => ({
  listRentersByOwner: vi.fn(),
  createRenter: vi.fn(),
  updateRenter: vi.fn(),
  deleteRenter: vi.fn(),
  createRenterDocument: vi.fn(),
  deleteRenterDocument: vi.fn(),
}));

describe("TenantsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no renters exist", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listRentersByOwner } = await import("@/services/renterService");
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "Proprietário Teste" },
    ]);
    vi.mocked(listRentersByOwner).mockResolvedValue([]);
    renderWithQueryClient(<TenantsPage />);
    expect(
      await screen.findByText(/nenhum inquilino cadastrado/i),
    ).toBeInTheDocument();
  });

  it("renders renters in the table on happy path", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listRentersByOwner } = await import("@/services/renterService");
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "Proprietário Teste" },
    ]);
    vi.mocked(listRentersByOwner).mockResolvedValue([
      {
        id: 1,
        name: "Maria Souza",
        primary_contact: "11999999999",
        secondary_contact: null,
        email: null,
      },
      {
        id: 2,
        name: "João Silva",
        primary_contact: "11988888888",
        secondary_contact: null,
        email: null,
      },
    ]);
    renderWithQueryClient(<TenantsPage />);
    expect(await screen.findByText("Maria Souza")).toBeInTheDocument();
    expect(await screen.findByText("João Silva")).toBeInTheDocument();
  });

  it("shows loading state while renters are loading", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listRentersByOwner } = await import("@/services/renterService");
    vi.mocked(listOwners).mockResolvedValue([
      { id: 1, name: "Proprietário Teste" },
    ]);
    vi.mocked(listRentersByOwner).mockReturnValue(new Promise(() => {}));
    renderWithQueryClient(<TenantsPage />);
    expect(await screen.findByText("Carregando...")).toBeInTheDocument();
  });
});
