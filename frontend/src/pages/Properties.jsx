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

// Map backend PropertyType enum to pt-BR display labels.
const PROPERTY_TYPE_LABELS = {
  HOUSE: "Casa",
  COMMERCIAL: "Comercial",
};

const EMPTY_FORM = {
  street_name: "",
  number: "",
  complement: "",
  neighborhood: "",
  city: "",
  state: "",
  zip_code: "",
  type: "HOUSE",
};

export function Properties() {
  const { owners, isLoading: ownersLoading, error: ownersError } = useOwners();
  const [selectedOwnerId, setSelectedOwnerId] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [isLoadingAddresses, setIsLoadingAddresses] = useState(false);
  const [error, setError] = useState("");

  // Default to the first owner once the list arrives.
  useEffect(() => {
    if (selectedOwnerId === null && owners.length > 0) {
      setSelectedOwnerId(String(owners[0].id));
    }
  }, [owners, selectedOwnerId]);

  // Fetch addresses whenever the selected owner changes.
  useEffect(() => {
    if (selectedOwnerId === null) return;
    let cancelled = false;
    setIsLoadingAddresses(true);
    setError("");
    api
      .get(`/owners/${selectedOwnerId}/addresses`)
      .then((resp) => {
        if (!cancelled) setAddresses(resp.data);
      })
      .catch(() => {
        if (!cancelled) setError("Não foi possível carregar os imóveis.");
      })
      .finally(() => {
        if (!cancelled) setIsLoadingAddresses(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedOwnerId]);

  async function handleCreate(payload, onClose) {
    try {
      const resp = await api.post(
        `/owners/${selectedOwnerId}/addresses`,
        payload
      );
      setAddresses((prev) => [...prev, resp.data]);
      onClose();
    } catch {
      setError("Não foi possível criar o imóvel.");
    }
  }

  async function handleDelete(addressId) {
    if (!confirm("Excluir este imóvel? Esta ação não pode ser desfeita.")) {
      return;
    }
    try {
      await api.delete(`/addresses/${addressId}`);
      setAddresses((prev) => prev.filter((a) => a.id !== addressId));
    } catch {
      setError("Não foi possível excluir o imóvel.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Imóveis</h1>
      <p className="mt-2 text-muted-foreground">
        Cadastre e gerencie os endereços das propriedades que você possui.
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
          <h2 className="text-xl font-semibold">Imóveis</h2>
          <CreateAddressDialog onCreate={handleCreate} />
        </div>
      )}

      {error && (
        <p className="mt-4 text-sm font-medium text-destructive">{error}</p>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <div className="mt-4">
          {isLoadingAddresses ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Carregando...
            </div>
          ) : addresses.length === 0 ? (
            <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground shadow-sm">
              Nenhum imóvel cadastrado para este proprietário. Clique em
              &quot;Adicionar&quot; para começar.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {addresses.map((address) => (
                <Card key={address.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <CardTitle className="text-lg">
                          {address.street_name}, {address.number}
                        </CardTitle>
                        <CardDescription>
                          {address.complement
                            ? `${address.complement} · `
                            : ""}
                          {address.neighborhood} · {address.city}/
                          {address.state} · CEP {address.zip_code}
                        </CardDescription>
                      </div>
                      <span className="shrink-0 rounded-md border bg-muted px-2 py-1 text-xs font-medium">
                        {PROPERTY_TYPE_LABELS[address.type] ?? address.type}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(address.id)}
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

function CreateAddressDialog({ onCreate }) {
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
    // Normalize empty optional fields to null and trim text.
    const payload = {
      ...form,
      street_name: form.street_name.trim(),
      number: form.number.trim(),
      complement: form.complement.trim() || null,
      neighborhood: form.neighborhood.trim(),
      city: form.city.trim(),
      state: form.state.trim(),
      zip_code: form.zip_code.trim(),
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
      <DialogContent className="max-w-xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Adicionar imóvel</DialogTitle>
            <DialogDescription>
              Cadastre o endereço de uma propriedade.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_120px]">
              <div className="grid gap-2">
                <Label htmlFor="street_name">Logradouro</Label>
                <Input
                  id="street_name"
                  placeholder="Rua das Flores"
                  value={form.street_name}
                  onChange={(e) => updateField("street_name", e.target.value)}
                  disabled={isSubmitting}
                  required
                  autoFocus
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="number">Número</Label>
                <Input
                  id="number"
                  placeholder="123"
                  value={form.number}
                  onChange={(e) => updateField("number", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="complement">Complemento (opcional)</Label>
              <Input
                id="complement"
                placeholder="Apto 45"
                value={form.complement}
                onChange={(e) => updateField("complement", e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="neighborhood">Bairro</Label>
              <Input
                id="neighborhood"
                placeholder="Centro"
                value={form.neighborhood}
                onChange={(e) => updateField("neighborhood", e.target.value)}
                disabled={isSubmitting}
                required
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_100px_140px]">
              <div className="grid gap-2">
                <Label htmlFor="city">Cidade</Label>
                <Input
                  id="city"
                  placeholder="São Paulo"
                  value={form.city}
                  onChange={(e) => updateField("city", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="state">Estado</Label>
                <Input
                  id="state"
                  placeholder="SP"
                  value={form.state}
                  onChange={(e) => updateField("state", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="zip_code">CEP</Label>
                <Input
                  id="zip_code"
                  placeholder="01000-000"
                  value={form.zip_code}
                  onChange={(e) => updateField("zip_code", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="type">Tipo</Label>
              <Select
                value={form.type}
                onValueChange={(value) => updateField("type", value)}
              >
                <SelectTrigger id="type">
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PROPERTY_TYPE_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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