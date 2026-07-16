import { Loader2, Trash2 } from "lucide-react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { formatPhone } from "@/lib/formatters";
import { useOwnerSelect } from "@/hooks/useOwnerSelect";
import { useRenters } from "@/hooks/useRenters";
import {
  useCreateRenter,
  useDeleteRenter,
  useUpdateRenter,
} from "@/hooks/useRenterMutations";
import { queryKeys } from "@/hooks/queryKeys";
import { createRenterDocument, deleteRenterDocument } from "@/services/renterService";
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
import { RenterDialog } from "@/tenants/components/RenterDialog";

export function TenantsPage() {
  const {
    owners,
    isLoading: ownersLoading,
    error: ownersError,
    selectedOwnerId,
    setSelectedOwnerId,
  } = useOwnerSelect();
  const {
    renters,
    isLoading: isLoadingRenters,
    error: rentersError,
  } = useRenters(selectedOwnerId ?? undefined);
  const [error, setError] = useState("");

  const createRenter = useCreateRenter();
  const updateRenter = useUpdateRenter();
  const deleteRenter = useDeleteRenter();
  const queryClient = useQueryClient();
  const pageError = error || rentersError;

  async function handleCreate(payload, documents, _initialDocuments, onClose) {
    try {
      const renter = await createRenter.mutateAsync({
        ownerId: selectedOwnerId,
        payload,
      });
      for (const doc of documents) {
        if (doc.isDeleted) continue;
        await createRenterDocument(renter.id, {
          document_type: doc.document_type,
          document: doc.document,
        });
      }
      queryClient.invalidateQueries({
        queryKey: queryKeys.renterDocuments(renter.id),
      });
      onClose();
    } catch {
      throw new Error("Não foi possível criar o inquilino.");
    }
  }

  async function handleUpdate(renterId, payload, documents, initialDocuments, onClose) {
    try {
      await updateRenter.mutateAsync({
        renterId,
        payload,
        ownerId: selectedOwnerId,
      });

      for (const doc of documents) {
        const isExisting = typeof doc.id === "number";
        if (doc.isDeleted && isExisting) {
          await deleteRenterDocument(renterId, doc.id);
        } else if (!isExisting && !doc.isDeleted) {
          await createRenterDocument(renterId, {
            document_type: doc.document_type,
            document: doc.document,
          });
        }
      }

      queryClient.invalidateQueries({
        queryKey: queryKeys.renterDocuments(renterId),
      });
      onClose();
    } catch (err) {
      if (err.response?.status === 409) {
        throw new Error("Já existe um documento deste tipo para este inquilino.");
      }
      throw new Error("Não foi possível atualizar o inquilino.");
    }
  }

  async function handleDelete(renterId) {
    if (!confirm("Excluir este inquilino? Esta ação não pode ser desfeita.")) {
      return;
    }
    try {
      await deleteRenter.mutateAsync({ renterId, ownerId: selectedOwnerId });
    } catch {
      setError("Não foi possível excluir o inquilino.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Inquilinos</h1>
      <p className="mt-2 text-muted-foreground">
        Cadastre e gerencie os moradores dos seus imóveis.
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
          <h2 className="text-xl font-semibold">Inquilinos</h2>
          <RenterDialog onSubmit={handleCreate} />
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
                <TableHead>Nome</TableHead>
                <TableHead>Contato principal</TableHead>
                <TableHead>Contato secundário</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead className="w-24 text-right"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoadingRenters ? (
                <TableRow>
                  <TableCell colSpan={5}>
                    <div className="flex items-center justify-center py-12 text-muted-foreground">
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Carregando...
                    </div>
                  </TableCell>
                </TableRow>
              ) : renters.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="py-8 text-center text-muted-foreground"
                  >
                    Nenhum inquilino cadastrado para este proprietário. Clique
                    em &quot;Adicionar&quot; para começar.
                  </TableCell>
                </TableRow>
              ) : (
                renters.map((renter) => (
                  <TableRow key={renter.id}>
                    <TableCell className="font-medium">{renter.name}</TableCell>
                    <TableCell>{formatPhone(renter.primary_contact)}</TableCell>
                    <TableCell>
                      {renter.secondary_contact
                        ? formatPhone(renter.secondary_contact)
                        : "—"}
                    </TableCell>
                    <TableCell>{renter.email ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <RenterDialog
                          renter={renter}
                          onSubmit={(
                            payload,
                            documents,
                            initialDocuments,
                            onClose
                          ) =>
                            handleUpdate(
                              renter.id,
                              payload,
                              documents,
                              initialDocuments,
                              onClose
                            )
                          }
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => handleDelete(renter.id)}
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