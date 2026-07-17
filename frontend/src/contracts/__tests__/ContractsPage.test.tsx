import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";

import { renderWithQueryClient } from "@/test/queryClient";
import { ContractsPage } from "@/contracts/ContractsPage";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/services/ownerService", () => ({
  listOwners: vi.fn(),
}));

vi.mock("@/services/contractService", () => ({
  listContractsByOwner: vi.fn(),
  createContract: vi.fn(),
  updateContract: vi.fn(),
  deleteContract: vi.fn(),
  downloadContractPdf: vi.fn(),
}));

vi.mock("@/services/renterService", () => ({
  listRentersByOwner: vi.fn(),
}));

vi.mock("@/services/addressService", () => ({
  listAddressesByOwner: vi.fn(),
}));

describe("ContractsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no contracts exist", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listContractsByOwner } = await import(
      "@/services/contractService"
    );
    const { listRentersByOwner } = await import(
      "@/services/renterService"
    );
    const { listAddressesByOwner } = await import(
      "@/services/addressService"
    );
    vi.mocked(listOwners).mockResolvedValue([{ id: 1, name: "Dono" }]);
    vi.mocked(listContractsByOwner).mockResolvedValue([]);
    vi.mocked(listRentersByOwner).mockResolvedValue([]);
    vi.mocked(listAddressesByOwner).mockResolvedValue([]);
    renderWithQueryClient(<ContractsPage />);
    expect(
      await screen.findByText(/nenhum contrato cadastrado/i),
    ).toBeInTheDocument();
  });

  it("renders contracts in the table on happy path", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listContractsByOwner } = await import(
      "@/services/contractService"
    );
    const { listRentersByOwner } = await import(
      "@/services/renterService"
    );
    const { listAddressesByOwner } = await import(
      "@/services/addressService"
    );
    vi.mocked(listOwners).mockResolvedValue([{ id: 1, name: "Dono" }]);
    vi.mocked(listContractsByOwner).mockResolvedValue([
      {
        id: 1,
        renter_id: 10,
        address_id: 20,
        start_date: "2025-01-01T00:00:00",
        end_date: "2026-01-01T00:00:00",
        monthly_revenue: "1500.00",
        deposit_value: "3000.00",
        deposit_months: 2,
        payment_day: 5,
        status: "ACTIVE",
      },
    ]);
    vi.mocked(listRentersByOwner).mockResolvedValue([
      {
        id: 10,
        name: "Maria Souza",
        primary_contact: "11999999999",
        secondary_contact: null,
        email: null,
      },
    ]);
    vi.mocked(listAddressesByOwner).mockResolvedValue([
      {
        id: 20,
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
    renderWithQueryClient(<ContractsPage />);
    expect(await screen.findByText("Maria Souza")).toBeInTheDocument();
    expect(
      await screen.findByText("Rua das Flores, 123"),
    ).toBeInTheDocument();
  });

  it("shows success toast on delete", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listContractsByOwner, deleteContract } = await import(
      "@/services/contractService"
    );
    const { listRentersByOwner } = await import(
      "@/services/renterService"
    );
    const { listAddressesByOwner } = await import(
      "@/services/addressService"
    );
    vi.mocked(deleteContract).mockResolvedValue(undefined);
    vi.mocked(listOwners).mockResolvedValue([{ id: 1, name: "Dono" }]);
    vi.mocked(listContractsByOwner).mockResolvedValue([
      {
        id: 1,
        renter_id: 10,
        address_id: 20,
        start_date: "2025-01-01T00:00:00",
        end_date: "2026-01-01T00:00:00",
        monthly_revenue: "1500.00",
        deposit_value: "3000.00",
        deposit_months: 2,
        payment_day: 5,
        status: "ACTIVE",
      },
    ]);
    vi.mocked(listRentersByOwner).mockResolvedValue([
      {
        id: 10,
        name: "Maria Souza",
        primary_contact: "11999999999",
        secondary_contact: null,
        email: null,
      },
    ]);
    vi.mocked(listAddressesByOwner).mockResolvedValue([
      {
        id: 20,
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
    const user = userEvent.setup();
    renderWithQueryClient(<ContractsPage />);
    const deleteBtn = await screen.findByRole("button", {
      name: /excluir/i,
    });
    await user.click(deleteBtn);
    const { toast } = await import("sonner");
    await vi.waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        "Contrato excluído com sucesso.",
      );
    });
  });

  it("shows friendly toast when PDF download fails with missing docs", async () => {
    const { listOwners } = await import("@/services/ownerService");
    const { listContractsByOwner, downloadContractPdf } = await import(
      "@/services/contractService"
    );
    const { listRentersByOwner } = await import(
      "@/services/renterService"
    );
    const { listAddressesByOwner } = await import(
      "@/services/addressService"
    );
    vi.mocked(downloadContractPdf).mockRejectedValue({
      response: {
        status: 422,
        data: new Blob(
          [
            JSON.stringify({
              detail: "Missing required document(s): owner_cpf, renter_rg",
            }),
          ],
          { type: "application/json" },
        ),
      },
    });
    vi.mocked(listOwners).mockResolvedValue([{ id: 1, name: "Dono" }]);
    vi.mocked(listContractsByOwner).mockResolvedValue([
      {
        id: 1,
        renter_id: 10,
        address_id: 20,
        start_date: "2025-01-01T00:00:00",
        end_date: "2026-01-01T00:00:00",
        monthly_revenue: "1500.00",
        deposit_value: "3000.00",
        deposit_months: 2,
        payment_day: 5,
        status: "ACTIVE",
      },
    ]);
    vi.mocked(listRentersByOwner).mockResolvedValue([
      {
        id: 10,
        name: "Maria Souza",
        primary_contact: "11999999999",
        secondary_contact: null,
        email: null,
      },
    ]);
    vi.mocked(listAddressesByOwner).mockResolvedValue([
      {
        id: 20,
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
    const user = userEvent.setup();
    renderWithQueryClient(<ContractsPage />);
    const downloadBtn = await screen.findByRole("button", {
      name: /baixar contrato/i,
    });
    await user.click(downloadBtn);
    const { toast } = await import("sonner");
    await vi.waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Não foi possível baixar o contrato. Faltam: CPF do proprietário, RG do inquilino.",
      );
    });
  });
});
