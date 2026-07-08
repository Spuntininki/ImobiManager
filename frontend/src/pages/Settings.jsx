import { FileText, Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import api from "@/lib/api";
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

export function Settings() {
  const [owners, setOwners] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  async function fetchOwners() {
    setIsLoading(true);
    setError("");
    try {
      const resp = await api.get("/owners");
      setOwners(resp.data);
    } catch {
      setError("Não foi possível carregar os proprietários.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchOwners();
  }, []);

  async function handleCreate(name, onClose) {
    try {
      const resp = await api.post("/owners", { name });
      setOwners((prev) => [...prev, resp.data]);
      onClose();
    } catch {
      setError("Não foi possível criar o proprietário.");
    }
  }

  async function handleUpdate(ownerId, name, onClose) {
    try {
      const resp = await api.put(`/owners/${ownerId}`, { name });
      setOwners((prev) =>
        prev.map((owner) => (owner.id === ownerId ? resp.data : owner))
      );
      onClose();
    } catch {
      setError("Não foi possível atualizar o proprietário.");
    }
  }

  async function handleDelete(ownerId) {
    if (!confirm("Excluir este proprietário? Esta ação não pode ser desfeita.")) {
      return;
    }
    try {
      await api.delete(`/owners/${ownerId}`);
      setOwners((prev) => prev.filter((o) => o.id !== ownerId));
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

      {error && (
        <p className="mt-4 text-sm font-medium text-destructive">{error}</p>
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
                      <OwnerDocumentsDialog owner={owner} />
                      <OwnerDialog
                        owner={owner}
                        onSubmit={(name, onClose) =>
                          handleUpdate(owner.id, name, onClose)
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

const DOCUMENT_TYPE_LABELS = {
  RG: "RG",
  CPF: "CPF",
  CNPJ: "CNPJ",
};

function OwnerDocumentsDialog({ owner }) {
  const [open, setOpen] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setIsLoading(true);
    setError("");
    api
      .get(`/owners/${owner.id}/documents`)
      .then((resp) => {
        if (!cancelled) setDocuments(resp.data);
      })
      .catch(() => {
        if (!cancelled) setError("Não foi possível carregar os documentos.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, owner.id]);

  async function handleCreate(payload, onCloseForm) {
    try {
      const resp = await api.post(`/owners/${owner.id}/documents`, payload);
      setDocuments((prev) => [...prev, resp.data]);
      onCloseForm();
    } catch (err) {
      if (err.response?.status === 409) {
        setError("Já existe um documento deste tipo para este proprietário.");
      } else {
        setError("Não foi possível criar o documento.");
      }
    }
  }

  async function handleUpdate(documentId, payload, onCloseForm) {
    try {
      const resp = await api.put(
        `/owners/${owner.id}/documents/${documentId}`,
        payload
      );
      setDocuments((prev) =>
        prev.map((doc) => (doc.id === documentId ? resp.data : doc))
      );
      onCloseForm();
    } catch (err) {
      if (err.response?.status === 409) {
        setError("Já existe um documento deste tipo para este proprietário.");
      } else {
        setError("Não foi possível atualizar o documento.");
      }
    }
  }

  async function handleDelete(documentId) {
    if (!confirm("Excluir este documento? Esta ação não pode ser desfeita.")) {
      return;
    }
    try {
      await api.delete(`/owners/${owner.id}/documents/${documentId}`);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
    } catch {
      setError("Não foi possível excluir o documento.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-muted">
          <FileText className="h-4 w-4" />
          <span className="sr-only">Documentos</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Documentos de {owner.name}</DialogTitle>
          <DialogDescription>
            Gerencie RG, CPF e CNPJ do proprietário.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <p className="mt-2 text-sm font-medium text-destructive">{error}</p>
        )}

        <div className="mt-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Documentos</h3>
          <DocumentFormDialog onSubmit={handleCreate} />
        </div>

        <div className="mt-2 overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tipo</TableHead>
                <TableHead>Número</TableHead>
                <TableHead className="w-24 text-right"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={3}>
                    <div className="flex items-center justify-center py-8 text-muted-foreground">
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Carregando...
                    </div>
                  </TableCell>
                </TableRow>
              ) : documents.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={3}
                    className="py-8 text-center text-muted-foreground"
                  >
                    Nenhum documento cadastrado.
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">
                      {DOCUMENT_TYPE_LABELS[doc.document_type] ??
                        doc.document_type}
                    </TableCell>
                    <TableCell>{doc.document}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <DocumentFormDialog
                          document={doc}
                          onSubmit={(payload, onCloseForm) =>
                            handleUpdate(doc.id, payload, onCloseForm)
                          }
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => handleDelete(doc.id)}
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
      </DialogContent>
    </Dialog>
  );
}

function DocumentFormDialog({ document: doc, onSubmit }) {
  const isEdit = doc !== undefined;
  const [open, setOpen] = useState(false);
  const [documentType, setDocumentType] = useState(
    isEdit ? doc.document_type : "RG"
  );
  const [document, setDocument] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleClose() {
    setOpen(false);
    setDocumentType(isEdit ? doc.document_type : "RG");
    setDocument("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!document.trim()) return;
    setIsSubmitting(true);
    try {
      await onSubmit(
        { document_type: documentType, document: document.trim() },
        handleClose
      );
    } finally {
      setIsSubmitting(false);
    }
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
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Adicionar
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Editar documento" : "Adicionar documento"}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? "O número atual é mascarado. Digite o novo número completo para substituí-lo."
                : "Cadastre um novo documento."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {isEdit && (
              <p className="text-sm text-muted-foreground">
                Valor atual: <span className="font-medium">{doc.document}</span>
              </p>
            )}
            <div className="grid gap-2">
              <Label htmlFor="document_type">Tipo</Label>
              <Select
                value={documentType}
                onValueChange={setDocumentType}
              >
                <SelectTrigger id="document_type">
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(DOCUMENT_TYPE_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="document">
                {isEdit ? "Novo número" : "Número"}
              </Label>
              <Input
                id="document"
                placeholder={
                  documentType === "CNPJ"
                    ? "00.000.000/0000-00"
                    : documentType === "CPF"
                      ? "000.000.000-00"
                      : "00.000.000-0"
                }
                value={document}
                onChange={(e) => setDocument(e.target.value)}
                disabled={isSubmitting}
                required
                autoFocus
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Salvando..." : isEdit ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function OwnerDialog({ owner, onSubmit }) {
  const isEdit = owner !== undefined;
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(isEdit ? owner.name : "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleClose() {
    setOpen(false);
    setName(isEdit ? owner.name : "");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await onSubmit(name.trim(), handleClose);
    } finally {
      setIsSubmitting(false);
    }
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
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Editar proprietário" : "Adicionar proprietário"}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? "Altere os dados do proprietário."
                : "Cadastre um novo proprietário para associar imóveis e contratos."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                placeholder="João Silva"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isSubmitting}
                autoFocus
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Salvando..." : isEdit ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}