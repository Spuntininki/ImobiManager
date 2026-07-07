import { Loader2, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "@/lib/api";
import { useOwners } from "@/lib/useOwners";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

const EMPTY_FORM = {
  name: "",
  primary_contact: "",
  secondary_contact: "",
  email: "",
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

  async function handleCreate(payload, onClose) {
    try {
      const resp = await api.post(
        `/owners/${selectedOwnerId}/renters`,
        payload
      );
      setRenters((prev) => [...prev, resp.data]);
      onClose();
    } catch {
      setError("Não foi possível criar o inquilino.");
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
            <Link to="/" className="underline">
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
          <CreateRenterDialog onCreate={handleCreate} />
        </div>
      )}

      {error && (
        <p className="mt-4 text-sm font-medium text-destructive">{error}</p>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <div className="mt-4">
          {isLoadingRenters ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Carregando...
            </div>
          ) : renters.length === 0 ? (
            <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground shadow-sm">
              Nenhum inquilino cadastrado para este proprietário. Clique em
              &quot;Adicionar&quot; para começar.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {renters.map((renter) => (
                <Card key={renter.id}>
                  <CardHeader>
                    <CardTitle className="text-lg">{renter.name}</CardTitle>
                    <CardDescription>
                      {renter.email ? `${renter.email} · ` : ""}
                      {renter.primary_contact}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {renter.secondary_contact && (
                      <p className="mb-4 text-sm text-muted-foreground">
                        Contato secundário: {renter.secondary_contact}
                      </p>
                    )}
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(renter.id)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Excluir
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CreateRenterDialog({ onCreate }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleClose() {
    setOpen(false);
    setForm(EMPTY_FORM);
  }

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const payload = {
      name: form.name.trim(),
      primary_contact: form.primary_contact.trim(),
      secondary_contact: form.secondary_contact.trim() || null,
      email: form.email.trim() || null,
    };
    setIsSubmitting(true);
    try {
      await onCreate(payload, handleClose);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Adicionar
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Adicionar inquilino</DialogTitle>
            <DialogDescription>
              Cadastre um morador para o proprietário selecionado.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                placeholder="Maria Souza"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                disabled={isSubmitting}
                required
                autoFocus
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="primary_contact">Contato principal</Label>
              <Input
                id="primary_contact"
                placeholder="(11) 99999-9999"
                value={form.primary_contact}
                onChange={(e) => updateField("primary_contact", e.target.value)}
                disabled={isSubmitting}
                required
              />
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
                disabled={isSubmitting}
              />
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
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Criando..." : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}