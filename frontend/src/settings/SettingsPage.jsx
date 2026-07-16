import { Loader2, Trash2 } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useOwners } from "@/hooks/useOwners";
import {
  useCreateOwner,
  useDeleteOwner,
  useUpdateOwner,
} from "@/hooks/useOwnerMutations";
import {
  createOwnerDocument,
  deleteOwnerDocument,
} from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { OwnerDialog } from "@/settings/components/OwnerDialog";

export function SettingsPage() {
  const { owners, isLoading, error: ownersError } = useOwners();
  const createOwner = useCreateOwner();
  const updateOwner = useUpdateOwner();
  const deleteOwnerM = useDeleteOwner();
  const queryClient = useQueryClient();
  const pageError = ownersError;

  async function handleCreate(name, documents, _initialDocuments, onClose) {
    try {
      const owner = await createOwner.mutateAsync({ name });
      for (const doc of documents) {
        if (doc.isDeleted) continue;
        await createOwnerDocument(owner.id, {
          document_type: doc.document_type,
          document: doc.document,
        });
      }
      queryClient.invalidateQueries({
        queryKey: queryKeys.ownerDocuments(owner.id),
      });
      onClose();
    } catch {
      throw new Error("Não foi possível criar o proprietário.");
    }
  }

  async function handleUpdate(ownerId, name, documents, initialDocuments, onClose) {
    try {
      await updateOwner.mutateAsync({ ownerId, name });

      for (const doc of documents) {
        const isExisting = typeof doc.id === "number";
        if (doc.isDeleted && isExisting) {
          await deleteOwnerDocument(ownerId, doc.id);
        } else if (!isExisting && !doc.isDeleted) {
          await createOwnerDocument(ownerId, {
            document_type: doc.document_type,
            document: doc.document,
          });
        }
      }

      queryClient.invalidateQueries({
        queryKey: queryKeys.ownerDocuments(ownerId),
      });
      onClose();
    } catch (err) {
      if (err.response?.status === 409) {
        throw new Error("Já existe um documento deste tipo para este proprietário.");
      }
      throw new Error("Não foi possível atualizar o proprietário.");
    }
  }

  async function handleDelete(ownerId) {
    try {
      await deleteOwnerM.mutateAsync({ ownerId });
      toast.success("Proprietário excluído com sucesso.");
    } catch {
      toast.error("Não foi possível excluir o proprietário.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Configurações</h1>
      <p className="mt-2 text-muted-foreground">
        Gerencie os proprietários vinculados à sua conta.
      </p>

      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Proprietários</h2>
        <OwnerDialog onSubmit={handleCreate} />
      </div>

      {pageError && (
        <p className="mt-4 text-sm font-medium text-destructive">{pageError}</p>
      )}

      <div className="mt-4 overflow-x-auto rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead className="w-24 text-right"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={2}>
                  <div className="flex items-center justify-center py-12 text-muted-foreground">
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Carregando...
                  </div>
                </TableCell>
              </TableRow>
            ) : owners.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={2}
                  className="py-8 text-center text-muted-foreground"
                >
                  Nenhum proprietário cadastrado. Clique em
                  &quot;Adicionar&quot; para começar.
                </TableCell>
              </TableRow>
            ) : (
              owners.map((owner) => (
                <TableRow key={owner.id}>
                  <TableCell className="font-medium">{owner.name}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <OwnerDialog
                        owner={owner}
                        onSubmit={(name, documents, initialDocuments, onClose) =>
                          handleUpdate(owner.id, name, documents, initialDocuments, onClose)
                        }
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                        onClick={() => handleDelete(owner.id)}
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
    </div>
  );
}