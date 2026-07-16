import { Pencil, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { parseDocument } from "@/lib/formatters";
import { validateDocument, validateName } from "@/lib/validators";
import { useOwnerDocuments } from "@/hooks/useOwnerDocuments";
import { DocumentFieldEditor } from "@/components/documents/DocumentFieldEditor";
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

export function OwnerDialog({ owner, onSubmit }) {
  const isEdit = owner !== undefined;
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(isEdit ? owner.name : "");
  const [documents, setDocuments] = useState([]);
  const [initialDocuments, setInitialDocuments] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dialogError, setDialogError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({ name: "" });
  const [documentErrors, setDocumentErrors] = useState({});

  const { documents: fetchedDocs, isLoading: isLoadingDocs } =
    useOwnerDocuments(owner?.id, {
      enabled: open && isEdit,
    });

  // Sync fetched documents into local state when they arrive.
  useEffect(() => {
    if (!open || !isEdit) return;
    if (fetchedDocs.length === 0 && isLoadingDocs) return;
    const withFlag = fetchedDocs.map((d) => ({ ...d, isDeleted: false }));
    setDocuments(withFlag);
    setInitialDocuments(withFlag);
  }, [open, isEdit, fetchedDocs, isLoadingDocs]);

  function handleClose() {
    setOpen(false);
    setName(isEdit ? owner.name : "");
    setDocuments([]);
    setInitialDocuments([]);
    setDialogError("");
    setFieldErrors({ name: "" });
    setDocumentErrors({});
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
      if (err.message?.includes("Já existe um documento")) {
        setDialogError(err.message);
      } else {
        toast.error(err.message || "Não foi possível salvar.");
      }
      setIsSubmitting(false);
      return;
    }
    setIsSubmitting(false);
  }

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

            <DocumentFieldEditor
              documents={documents}
              setDocuments={setDocuments}
              documentErrors={documentErrors}
              setDocumentErrors={setDocumentErrors}
              isLoadingDocs={isLoadingDocs}
              isSubmitting={isSubmitting}
            />
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