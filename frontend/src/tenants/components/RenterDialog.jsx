import { Pencil, Plus } from "lucide-react";
import { useEffect, useState } from "react";

import {
  formatPhone,
  limitRawLength,
  parseDocument,
  parseEmail,
  parsePhone,
  PHONE_MAX_DIGITS,
} from "@/lib/formatters";
import {
  validateDocument,
  validateEmail,
  validateName,
  validatePhone,
} from "@/lib/validators";
import { useRenterDocuments } from "@/hooks/useRenterDocuments";
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

const EMPTY_FORM = {
  name: "",
  primary_contact: "",
  secondary_contact: "",
  email: "",
};

export function RenterDialog({ renter, onSubmit }) {
  const isEdit = renter !== undefined;
  const initialForm = isEdit
    ? {
        name: renter.name,
        primary_contact: renter.primary_contact,
        secondary_contact: renter.secondary_contact ?? "",
        email: renter.email ?? "",
      }
    : EMPTY_FORM;
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [documents, setDocuments] = useState([]);
  const [initialDocuments, setInitialDocuments] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dialogError, setDialogError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({
    name: "",
    primary_contact: "",
    secondary_contact: "",
    email: "",
  });
  const [documentErrors, setDocumentErrors] = useState({});

  const { documents: fetchedDocs, isLoading: isLoadingDocs } =
    useRenterDocuments(renter?.id, {
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
    setForm(initialForm);
    setDocuments([]);
    setInitialDocuments([]);
    setDialogError("");
    setFieldErrors({
      name: "",
      primary_contact: "",
      secondary_contact: "",
      email: "",
    });
    setDocumentErrors({});
  }

  function updateField(field, value) {
    setForm((prev) => {
      if (field === "primary_contact" || field === "secondary_contact") {
        return { ...prev, [field]: formatPhone(value) };
      }
      return { ...prev, [field]: value };
    });
    setFieldErrors((prev) => ({ ...prev, [field]: "" }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const errors = {
      name: validateName(form.name),
      primary_contact: validatePhone(form.primary_contact),
      secondary_contact: validatePhone(form.secondary_contact, {
        required: false,
      }),
      email: validateEmail(form.email),
    };

    const visibleDocs = documents.filter((d) => !d.isDeleted);
    const types = visibleDocs.map((d) => d.document_type);
    if (new Set(types).size !== types.length) {
      setDialogError("Não é permitido mais de um documento do mesmo tipo.");
      setFieldErrors(errors);
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

    const hasFieldErrors = Object.values(errors).some(Boolean);
    if (hasFieldErrors || Object.keys(docErrors).length > 0) {
      setDialogError("Corrija os campos destacados antes de salvar.");
      setFieldErrors(errors);
      setDocumentErrors(docErrors);
      return;
    }

    setDialogError("");
    setFieldErrors(errors);
    setDocumentErrors({});

    const payload = {
      name: form.name.trim(),
      primary_contact: parsePhone(form.primary_contact),
      secondary_contact: form.secondary_contact
        ? parsePhone(form.secondary_contact)
        : null,
      email: parseEmail(form.email) || null,
    };

    const rawDocuments = documents.map((doc) => ({
      ...doc,
      // Existing docs are read-only — keep the original value; only parse new inputs.
      document: typeof doc.id === "number" ? doc.document : parseDocument(doc.document),
    }));

    setIsSubmitting(true);
    try {
      await onSubmit(payload, rawDocuments, initialDocuments, handleClose);
    } catch (err) {
      setDialogError(err.message);
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
              {isEdit ? "Editar inquilino" : "Adicionar inquilino"}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? "Altere os dados e documentos do morador."
                : "Cadastre um novo morador e seus documentos."}
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
                placeholder="Maria Souza"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                disabled={isSubmitting}
                maxLength={100}
                aria-invalid={!!fieldErrors.name}
                autoFocus
              />
              {fieldErrors.name && (
                <p className="text-xs text-destructive">{fieldErrors.name}</p>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="primary_contact">Contato principal</Label>
              <Input
                id="primary_contact"
                placeholder="(11) 99999-9999"
                value={form.primary_contact}
                onChange={(e) => updateField("primary_contact", e.target.value)}
                onBeforeInput={limitRawLength(parsePhone, PHONE_MAX_DIGITS)}
                disabled={isSubmitting}
                inputMode="tel"
                aria-invalid={!!fieldErrors.primary_contact}
              />
              {fieldErrors.primary_contact && (
                <p className="text-xs text-destructive">
                  {fieldErrors.primary_contact}
                </p>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="secondary_contact">
                Contato secundário (opcional)
              </Label>
              <Input
                id="secondary_contact"
                placeholder="(11) 98888-8888"
                value={form.secondary_contact}
                onChange={(e) => updateField("secondary_contact", e.target.value)}
                onBeforeInput={limitRawLength(parsePhone, PHONE_MAX_DIGITS)}
                disabled={isSubmitting}
                inputMode="tel"
                aria-invalid={!!fieldErrors.secondary_contact}
              />
              {fieldErrors.secondary_contact && (
                <p className="text-xs text-destructive">
                  {fieldErrors.secondary_contact}
                </p>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="email">E-mail (opcional)</Label>
              <Input
                id="email"
                type="email"
                placeholder="maria@email.com"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                disabled={isSubmitting}
                maxLength={254}
                aria-invalid={!!fieldErrors.email}
              />
              {fieldErrors.email && (
                <p className="text-xs text-destructive">{fieldErrors.email}</p>
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