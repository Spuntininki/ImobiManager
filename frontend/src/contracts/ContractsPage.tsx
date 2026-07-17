import { Download, Loader2, Trash2 } from "lucide-react";
import { useMemo } from "react";
import { toast } from "sonner";

import { useOwnerSelect } from "@/hooks/useOwnerSelect";
import { useContractsPageData } from "@/hooks/useContractsPageData";
import {
  useCreateContract,
  useDeleteContract,
  useUpdateContract,
} from "@/hooks/useContractMutations";
import { downloadContractPdf } from "@/services/contractService";
import { parseContractPdfError } from "@/lib/contractPdf";
import { OwnerSelect } from "@/components/layout/OwnerSelect";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ContractDialog } from "@/contracts/components/ContractDialog";
import type { Renter, Address, Contract } from "@/types/domain";

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Pendente",
  ACTIVE: "Ativo",
  EXPIRED: "Expirado",
  CANCELLED: "Cancelado",
};

const CURRENCY = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

function formatIsoDate(isoDateTime: string) {
  if (!isoDateTime) return "";
  const [date] = isoDateTime.split("T");
  if (!date) return "";
  const [year, month, day] = date.split("-");
  return `${day}/${month}/${year}`;
}

export function ContractsPage() {
  const {
    owners,
    isLoading: ownersLoading,
    error: ownersError,
    selectedOwnerId,
    setSelectedOwnerId,
  } = useOwnerSelect();
  const ownerIdNum = selectedOwnerId ? Number(selectedOwnerId) : undefined;

  const {
    contracts,
    renters,
    addresses,
    isLoading,
    error: pageDataError,
  } = useContractsPageData(ownerIdNum);
  const createContract = useCreateContract();
  const updateContract = useUpdateContract();
  const deleteContract = useDeleteContract();
  const pageError = pageDataError;

  const renterMap = useMemo(
    () => Object.fromEntries(renters.map((r: Renter) => [r.id, r])),
    [renters]
  );
  const addressMap = useMemo(
    () => Object.fromEntries(addresses.map((a: Address) => [a.id, a])),
    [addresses]
  );

  async function handleCreate(payload: Record<string, unknown>, onClose: () => void) {
    try {
      await createContract.mutateAsync({ ownerId: Number(selectedOwnerId), payload });
      toast.success("Contrato criado com sucesso.");
      onClose();
    } catch {
      toast.error("Não foi possível criar o contrato.");
    }
  }

  async function handleUpdate(contractId: number, payload: Record<string, unknown>, onClose: () => void) {
    try {
      await updateContract.mutateAsync({
        contractId,
        payload,
        ownerId: Number(selectedOwnerId),
      });
      toast.success("Contrato atualizado com sucesso.");
      onClose();
    } catch {
      toast.error("Não foi possível atualizar o contrato.");
    }
  }

  async function handleDelete(contractId: number) {
    try {
      await deleteContract.mutateAsync({ contractId, ownerId: Number(selectedOwnerId) });
      toast.success("Contrato excluído com sucesso.");
    } catch {
      toast.error("Não foi possível excluir o contrato.");
    }
  }

  async function handleDownloadPdf(contractId: number) {
    try {
      const { blob, disposition } = await downloadContractPdf(contractId);
      const url = URL.createObjectURL(new Blob([blob]));
      const link = document.createElement("a");
      link.href = url;
      const match = disposition?.match(/filename="?([^";]+)"?/i);
      const filename = match?.[1] ?? `contract-${contractId}.pdf`;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success("Contrato baixado com sucesso.");
    } catch (error) {
      const friendly = await parseContractPdfError(error);
      toast.error(
        friendly
          ? `Não foi possível baixar o contrato. ${friendly}`
          : "Não foi possível baixar o contrato.",
      );
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Contratos</h1>
      <p className="mt-2 text-muted-foreground">
        Cadastre e acompanhe os contratos de locação dos seus imóveis.
      </p>

      <OwnerSelect
        owners={owners}
        isLoading={ownersLoading}
        selectedOwnerId={selectedOwnerId}
        onSelect={setSelectedOwnerId}
      />

      {ownersError && (
        <p className="mt-4 text-sm font-medium text-destructive">{ownersError}</p>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <div className="mt-8 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Contratos</h2>
          <ContractDialog
            onSubmit={handleCreate}
            renters={renters}
            addresses={addresses}
          />
        </div>
      )}

      {pageError && (
        <p className="mt-4 text-sm font-medium text-destructive">{pageError}</p>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <div className="mt-4 overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Inquilino</TableHead>
                <TableHead>Imóvel</TableHead>
                <TableHead>Período</TableHead>
                <TableHead>Aluguel</TableHead>
                <TableHead>Depósito</TableHead>
                <TableHead>Dia de pagamento</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-24 text-right"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    <div className="flex items-center justify-center py-12 text-muted-foreground">
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Carregando...
                    </div>
                  </TableCell>
                </TableRow>
              ) : contracts.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="py-8 text-center text-muted-foreground"
                  >
                    Nenhum contrato cadastrado para este proprietário. Clique em
                    &quot;Adicionar&quot; para começar.
                  </TableCell>
                </TableRow>
              ) : (
                contracts.map((contract: Contract) => {
                  const renter = renterMap[contract.renter_id];
                  const address = addressMap[contract.address_id];
                  return (
                    <TableRow key={contract.id}>
                      <TableCell className="font-medium">
                        {renter?.name ?? `Inquilino #${contract.renter_id}`}
                      </TableCell>
                      <TableCell>
                        {address
                          ? `${address.street_name}, ${address.number}`
                          : `Imóvel #${contract.address_id}`}
                      </TableCell>
                      <TableCell>
                        {formatIsoDate(contract.start_date)} até{" "}
                        {formatIsoDate(contract.end_date)}
                      </TableCell>
                      <TableCell>
                        {CURRENCY.format(Number(contract.monthly_revenue))}
                      </TableCell>
                      <TableCell>
                        {CURRENCY.format(Number(contract.deposit_value))} (
                        {contract.deposit_months} {contract.deposit_months === 1 ? "mês" : "meses"})
                      </TableCell>
                      <TableCell>{contract.payment_day}</TableCell>
                      <TableCell>
                        <span className="rounded-md border bg-muted px-2 py-1 text-xs font-medium">
                          {STATUS_LABELS[contract.status] ?? contract.status}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <ContractDialog
                            contract={contract}
                            renters={renters}
                            addresses={addresses}
                            onSubmit={(payload, onClose) =>
                              handleUpdate(contract.id, payload, onClose)
                            }
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => handleDownloadPdf(contract.id)}
                          >
                            <Download className="h-4 w-4" />
                            <span className="sr-only">Baixar contrato</span>
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => handleDelete(contract.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Excluir</span>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
