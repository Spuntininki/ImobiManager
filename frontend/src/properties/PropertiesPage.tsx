import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { useOwnerSelect } from "@/hooks/useOwnerSelect";
import { useAddresses } from "@/hooks/useAddresses";
import {
  useCreateAddress,
  useDeleteAddress,
  useUpdateAddress,
} from "@/hooks/useAddressMutations";
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
import { AddressDialog } from "@/properties/components/AddressDialog";

const PROPERTY_TYPE_LABELS: Record<string, string> = {
  HOUSE: "Casa",
  COMMERCIAL: "Comercial",
};

export function PropertiesPage() {
  const {
    owners,
    isLoading: ownersLoading,
    error: ownersError,
    selectedOwnerId,
    setSelectedOwnerId,
  } = useOwnerSelect();
  const ownerIdNum = selectedOwnerId ? Number(selectedOwnerId) : undefined;
  const {
    addresses,
    isLoading: isLoadingAddresses,
    error: addressesError,
  } = useAddresses(ownerIdNum);
  const createAddress = useCreateAddress();
  const updateAddress = useUpdateAddress();
  const deleteAddress = useDeleteAddress();
  const pageError = addressesError;

  async function handleCreate(payload: Record<string, unknown>, onClose: () => void) {
    try {
      await createAddress.mutateAsync({ ownerId: Number(selectedOwnerId), payload });
      toast.success("Imóvel criado com sucesso.");
      onClose();
    } catch {
      toast.error("Não foi possível criar o imóvel.");
    }
  }

  async function handleUpdate(addressId: number, payload: Record<string, unknown>, onClose: () => void) {
    try {
      await updateAddress.mutateAsync({
        addressId,
        payload,
        ownerId: Number(selectedOwnerId),
      });
      toast.success("Imóvel atualizado com sucesso.");
      onClose();
    } catch {
      toast.error("Não foi possível atualizar o imóvel.");
    }
  }

  async function handleDelete(addressId: number) {
    try {
      await deleteAddress.mutateAsync({
        addressId,
        ownerId: Number(selectedOwnerId),
      });
      toast.success("Imóvel excluído com sucesso.");
    } catch {
      toast.error("Não foi possível excluir o imóvel.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Imóveis</h1>
      <p className="mt-2 text-muted-foreground">
        Cadastre e gerencie os endereços das propriedades que você possui.
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
          <h2 className="text-xl font-semibold">Imóveis</h2>
          <AddressDialog onSubmit={handleCreate} />
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
                <TableHead>Logradouro</TableHead>
                <TableHead>Nº</TableHead>
                <TableHead>Complemento</TableHead>
                <TableHead>Bairro</TableHead>
                <TableHead>Cidade/UF</TableHead>
                <TableHead>CEP</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead className="w-24 text-right"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoadingAddresses ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    <div className="flex items-center justify-center py-12 text-muted-foreground">
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Carregando...
                    </div>
                  </TableCell>
                </TableRow>
              ) : addresses.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="py-8 text-center text-muted-foreground"
                  >
                    Nenhum imóvel cadastrado para este proprietário. Clique em
                    &quot;Adicionar&quot; para começar.
                  </TableCell>
                </TableRow>
              ) : (
                addresses.map((address) => (
                  <TableRow key={address.id}>
                    <TableCell className="font-medium">
                      {address.street_name}
                    </TableCell>
                    <TableCell>{address.number}</TableCell>
                    <TableCell>{address.complement ?? "—"}</TableCell>
                    <TableCell>{address.neighborhood}</TableCell>
                    <TableCell>
                      {address.city}/{address.state}
                    </TableCell>
                    <TableCell>{address.zip_code}</TableCell>
                    <TableCell>
                      {PROPERTY_TYPE_LABELS[address.type] ?? address.type}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <AddressDialog
                          address={address}
                          onSubmit={(payload, onClose) =>
                            handleUpdate(address.id, payload, onClose)
                          }
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => handleDelete(address.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                          <span className="sr-only">Excluir</span>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
