import { Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";
import {
  formatDocument,
  getDocumentMaxLength,
  limitRawLength,
  parseDocument,
} from "@/lib/formatters";
import { validateDocument, validateName } from "@/lib/validators";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const DOCUMENT_TYPE_LABELS = {
  RG: "RG",
  CPF: "CPF",
  CNPJ: "CNPJ",
};

let documentTempId = 0;

const EMPTY_DOCUMENT = {
  document_type: "RG",
  document: "",
};

export function Settings() {
  const { owners, isLoading, error: ownersError } = useOwners();
  const [error, setError] = useState("");

  const createOwner = useCreateOwner();
  const updateOwner = useUpdateOwner();
  const deleteOwner = useDeleteOwner();
  const queryClient = useQueryClient();
  const pageError = error || ownersError;

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
    if (!confirm("Excluir este proprietário? Esta ação não pode ser desfeita.")) {
      return;
    }
    try {
      await deleteOwner.mutateAsync({ ownerId });
    } catch {
      setError("Não foi possível excluir o proprietário.");
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

function OwnerDialog({ owner, onSubmit }) {
  const isEdit = owner !== undefined;
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(isEdit ? owner.name : "");
  const [documents, setDocuments] = useState([]);
  const [initialDocuments, setInitialDocuments] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dialogError, setDialogError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({ name: "" });
  const [documentErrors, setDocumentErrors] = useState({});

  useEffect(() => {
    if (!open || !isEdit) {
      setDocuments([]);
      setInitialDocuments([]);
      return;
    }
    let cancelled = false;
    setIsLoadingDocs(true);
    setDialogError("");
    api
      .get(`/owners/${owner.id}/documents`)
      .then((resp) => {
        if (!cancelled) {
          const docs = resp.data.map((d) => ({ ...d, isDeleted: false }));
          setDocuments(docs);
          setInitialDocuments(docs);
        }
      })
      .catch(() => {
        if (!cancelled) setDialogError("Não foi possível carregar os documentos.");
      })
      .finally(() => {
        if (!cancelled) setIsLoadingDocs(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, isEdit, owner?.id]);

  function handleClose() {
    setOpen(false);
    setName(isEdit ? owner.name : "");
    setDocuments([]);
    setInitialDocuments([]);
    setDialogError("");
    setFieldErrors({ name: "" });
    setDocumentErrors({});
  }

  function addDocument(event) {
    event.preventDefault();
    event.stopPropagation();
    documentTempId += 1;
    setDocuments((prev) => [
      ...prev,
      { ...EMPTY_DOCUMENT, _tempId: `temp-${documentTempId}`, isDeleted: false },
    ]);
  }

  function updateDocument(index, field, value) {
    setDocuments((prev) =>
      prev.map((doc, i) => {
        if (i !== index) return doc;
        if (field === "document") {
          return { ...doc, document: formatDocument(doc.document_type, value) };
        }
        if (field === "document_type") {
          return {
            ...doc,
            document_type: value,
            document: formatDocument(value, doc.document),
          };
        }
        return { ...doc, [field]: value };
      })
    );
    setDocumentErrors((prev) => {
      const doc = documents[index];
      if (!doc) return prev;
      const key = doc.id ?? doc._tempId;
      return { ...prev, [key]: "" };
    });
  }

  function removeDocument(index) {
    setDocuments((prev) =>
      prev.map((doc, i) => (i === index ? { ...doc, isDeleted: true } : doc))
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const nameError = validateName(name);
    const visibleDocs = documents.filter((d) => !d.isDeleted);
    const types = visibleDocs.map((d) => d.document_type);
    if (new Set(types).size !== types.length) {
      setDialogError("Não é permitido mais de um documento do mesmo tipo.");
      setFieldErrors({ name: nameError });
      return;
    }

    const docErrors = {};
    for (const doc of visibleDocs) {
      // Existing docs are read-only; newly added docs must be validated.
      if (typeof doc.id === "number") continue;
      const error = validateDocument(doc.document_type, doc.document);
      if (error) {
        docErrors[doc._tempId] = error;
      }
    }

    if (nameError || Object.keys(docErrors).length > 0) {
      setDialogError("Corrija os campos destacados antes de salvar.");
      setFieldErrors({ name: nameError });
      setDocumentErrors(docErrors);
      return;
    }

    setDialogError("");
    setFieldErrors({ name: "" });
    setDocumentErrors({});

    const rawDocuments = documents.map((doc) => ({
      ...doc,
      // Existing docs are read-only — keep the original value; only parse new inputs.
      document: typeof doc.id === "number" ? doc.document : parseDocument(doc.document),
    }));

    setIsSubmitting(true);
    try {
      await onSubmit(name.trim(), rawDocuments, initialDocuments, handleClose);
    } catch (err) {
      setDialogError(err.message);
      setIsSubmitting(false);
      return;
    }
    setIsSubmitting(false);
  }

  const visibleDocuments = documents.filter((d) => !d.isDeleted);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {isEdit ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 hover:bg-muted"
          >
            <Pencil className="h-4 w-4" />
            <span className="sr-only">Editar</span>
          </Button>
        ) : (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Adicionar
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Editar proprietário" : "Adicionar proprietário"}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? "Altere os dados e documentos do proprietário."
                : "Cadastre um novo proprietário e seus documentos."}
            </DialogDescription>
          </DialogHeader>

          {dialogError && (
            <p className="mt-4 text-sm font-medium text-destructive">
              {dialogError}
            </p>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                placeholder="João Silva"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (fieldErrors.name) {
                    setFieldErrors((prev) => ({ ...prev, name: "" }));
                  }
                }}
                disabled={isSubmitting}
                maxLength={100}
                aria-invalid={!!fieldErrors.name}
                autoFocus
              />
              {fieldErrors.name && (
                <p className="text-xs text-destructive">{fieldErrors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Documentos</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addDocument}
                  disabled={isSubmitting || isLoadingDocs}
                >
                  <Plus className="mr-1 h-4 w-4" />
                  Adicionar documento
                </Button>
              </div>

              {isLoadingDocs ? (
                <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Carregando documentos...
                </div>
              ) : visibleDocuments.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Nenhum documento cadastrado.
                </p>
              ) : (
                <div className="space-y-2">
                  {visibleDocuments.map((doc) => {
                    const actualIndex = documents.findIndex(
                      (d) => d === doc
                    );
                    const docError = documentErrors[doc.id ?? doc._tempId];
                    const isExisting = typeof doc.id === "number";
                    return (
                      <div
                        key={doc.id ?? doc._tempId}
                        className="space-y-1"
                      >
                        <div className="flex items-start gap-2">
                          {isExisting ? (
                            <>
                              <div className="flex h-10 w-28 items-center rounded-md border bg-muted px-3 text-sm font-medium text-muted-foreground">
                                {DOCUMENT_TYPE_LABELS[doc.document_type]}
                              </div>
                              <div className="flex h-10 flex-1 items-center rounded-md border bg-muted px-3 text-sm text-muted-foreground">
                                {doc.document || (
                                  <span className="italic">—</span>
                                )}
                              </div>
                            </>
                          ) : (
                            <>
                              <Select
                                value={doc.document_type}
                                onValueChange={(value) =>
                                  updateDocument(actualIndex, "document_type", value)
                                }
                                disabled={isSubmitting}
                              >
                                <SelectTrigger className="w-28">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {Object.entries(DOCUMENT_TYPE_LABELS).map(
                                    ([value, label]) => (
                                      <SelectItem key={value} value={value}>
                                        {label}
                                      </SelectItem>
                                    )
                                  )}
                                </SelectContent>
                              </Select>
                              <Input
                                placeholder={
                                  doc.document_type === "CNPJ"
                                    ? "00.000.000/0000-00"
                                    : doc.document_type === "CPF"
                                      ? "000.000.000-00"
                                      : "00.000.000-0"
                                }
                                value={doc.document}
                                onChange={(e) =>
                                  updateDocument(actualIndex, "document", e.target.value)
                                }
                                onBeforeInput={limitRawLength(
                                  parseDocument,
                                  getDocumentMaxLength(doc.document_type)
                                )}
                                disabled={isSubmitting}
                                aria-invalid={!!docError}
                              />
                            </>
                          )}
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-10 w-10 shrink-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => removeDocument(actualIndex)}
                            disabled={isSubmitting}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Remover</span>
                          </Button>
                        </div>
                        {docError && (
                          <p className="text-xs text-destructive">{docError}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button type="submit" disabled={isSubmitting || isLoadingDocs}>
              {isSubmitting ? "Salvando..." : isEdit ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}