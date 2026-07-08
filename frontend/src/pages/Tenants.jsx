import { Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "@/lib/api";
import {
  formatDocument,
  formatPhone,
  getDocumentMaxLength,
  limitRawLength,
  parseDocument,
  parseEmail,
  parsePhone,
  PHONE_MAX_DIGITS,
  validateDocument,
  validateEmail,
  validateName,
  validatePhone,
} from "@/lib/formatters";
import { useOwners } from "@/lib/useOwners";
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

const EMPTY_FORM = {
  name: "",
  primary_contact: "",
  secondary_contact: "",
  email: "",
};

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

export function Tenants() {
  const { owners, isLoading: ownersLoading, error: ownersError } = useOwners();
  const [selectedOwnerId, setSelectedOwnerId] = useState(null);
  const [renters, setRenters] = useState([]);
  const [isLoadingRenters, setIsLoadingRenters] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (selectedOwnerId === null && owners.length > 0) {
      setSelectedOwnerId(String(owners[0].id));
    }
  }, [owners, selectedOwnerId]);

  useEffect(() => {
    if (selectedOwnerId === null) return;
    let cancelled = false;
    setIsLoadingRenters(true);
    setError("");
    api
      .get(`/owners/${selectedOwnerId}/renters`)
      .then((resp) => {
        if (!cancelled) setRenters(resp.data);
      })
      .catch(() => {
        if (!cancelled) setError("Não foi possível carregar os inquilinos.");
      })
      .finally(() => {
        if (!cancelled) setIsLoadingRenters(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedOwnerId]);

  async function handleCreate(payload, documents, _initialDocuments, onClose) {
    try {
      const resp = await api.post(
        `/owners/${selectedOwnerId}/renters`,
        payload
      );
      const renterId = resp.data.id;
      for (const doc of documents) {
        if (doc.isDeleted) continue;
        await api.post(`/renters/${renterId}/documents`, {
          document_type: doc.document_type,
          document: doc.document.trim(),
        });
      }
      setRenters((prev) => [...prev, resp.data]);
      onClose();
    } catch {
      setError("Não foi possível criar o inquilino.");
    }
  }

  async function handleUpdate(renterId, payload, documents, initialDocuments, onClose) {
    try {
      const resp = await api.put(`/renters/${renterId}`, payload);

      const initialById = Object.fromEntries(
        initialDocuments.map((d) => [d.id, d])
      );

      for (const doc of documents) {
        const isExisting = typeof doc.id === "number";
        if (doc.isDeleted && isExisting) {
          await api.delete(`/renters/${renterId}/documents/${doc.id}`);
        } else if (isExisting) {
          const initial = initialById[doc.id];
          if (
            initial &&
            (initial.document_type !== doc.document_type ||
              initial.document !== doc.document.trim())
          ) {
            await api.put(`/renters/${renterId}/documents/${doc.id}`, {
              document_type: doc.document_type,
              document: doc.document.trim(),
            });
          }
        } else if (!doc.isDeleted) {
          await api.post(`/renters/${renterId}/documents`, {
            document_type: doc.document_type,
            document: doc.document.trim(),
          });
        }
      }

      setRenters((prev) =>
        prev.map((renter) => (renter.id === renterId ? resp.data : renter))
      );
      onClose();
    } catch (err) {
      if (err.response?.status === 409) {
        setError("Já existe um documento deste tipo para este inquilino.");
      } else {
        setError("Não foi possível atualizar o inquilino.");
      }
    }
  }

  async function handleDelete(renterId) {
    if (!confirm("Excluir este inquilino? Esta ação não pode ser desfeita.")) {
      return;
    }
    try {
      await api.delete(`/renters/${renterId}`);
      setRenters((prev) => prev.filter((r) => r.id !== renterId));
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

      <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
        <Label htmlFor="owner-select" className="sm:w-32">
          Proprietário
        </Label>
        {ownersLoading ? (
          <div className="flex items-center text-sm text-muted-foreground">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Carregando...
          </div>
        ) : owners.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nenhum proprietário cadastrado.{" "}
            <Link to="/settings" className="underline">
              Crie um proprietário primeiro
            </Link>
            .
          </p>
        ) : (
          <Select
            value={selectedOwnerId ?? undefined}
            onValueChange={setSelectedOwnerId}
          >
            <SelectTrigger id="owner-select" className="sm:w-80">
              <SelectValue placeholder="Selecione um proprietário" />
            </SelectTrigger>
            <SelectContent>
              {owners.map((owner) => (
                <SelectItem key={owner.id} value={String(owner.id)}>
                  {owner.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {ownersError && (
        <p className="mt-4 text-sm font-medium text-destructive">{ownersError}</p>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <div className="mt-8 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Inquilinos</h2>
          <RenterDialog onSubmit={handleCreate} />
        </div>
      )}

      {error && (
        <p className="mt-4 text-sm font-medium text-destructive">{error}</p>
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

function RenterDialog({ renter, onSubmit }) {
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
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dialogError, setDialogError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({
    name: "",
    primary_contact: "",
    secondary_contact: "",
    email: "",
  });
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
      .get(`/renters/${renter.id}/documents`)
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
  }, [open, isEdit, renter?.id]);

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
      const error = validateDocument(doc.document_type, doc.document);
      if (error) {
        docErrors[doc.id ?? doc._tempId] = error;
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
      document: parseDocument(doc.document),
    }));

    setIsSubmitting(true);
    try {
      await onSubmit(payload, rawDocuments, initialDocuments, handleClose);
    } finally {
      setIsSubmitting(false);
    }
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
                    const actualIndex = documents.findIndex((d) => d === doc);
                    const docError = documentErrors[doc.id ?? doc._tempId];
                    return (
                      <div
                        key={doc.id ?? doc._tempId}
                        className="space-y-1"
                      >
                        <div className="flex items-start gap-2">
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