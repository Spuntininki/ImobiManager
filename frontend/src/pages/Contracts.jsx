import { Loader2, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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

const STATUS_LABELS = {
  PENDING: "Pendente",
  ACTIVE: "Ativo",
  EXPIRED: "Expirado",
  CANCELLED: "Cancelado",
};

const CURRENCY = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const EMPTY_FORM = {
  renter_id: "",
  address_id: "",
  start_date: "",
  end_date: "",
  monthly_revenue: "",
  deposit_value: "",
  deposit_months: "",
};

function formatIsoDate(isoDateTime) {
  if (!isoDateTime) return "";
  // Render only the date part in pt-BR (YYYY-MM-DDTHH:mm:ss...).
  const [date] = isoDateTime.split("T");
  if (!date) return "";
  const [year, month, day] = date.split("-");
  return `${day}/${month}/${year}`;
}

export function Contracts() {
  const { owners, isLoading: ownersLoading, error: ownersError } = useOwners();
  const [selectedOwnerId, setSelectedOwnerId] = useState(null);

  const [contracts, setContracts] = useState([]);
  const [renters, setRenters] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const renterMap = useMemo(
    () => Object.fromEntries(renters.map((r) => [r.id, r])),
    [renters]
  );
  const addressMap = useMemo(
    () => Object.fromEntries(addresses.map((a) => [a.id, a])),
    [addresses]
  );

  useEffect(() => {
    if (selectedOwnerId === null && owners.length > 0) {
      setSelectedOwnerId(String(owners[0].id));
    }
  }, [owners, selectedOwnerId]);

  // Fetch contracts, renters and addresses for the selected owner in parallel.
  // Renters/addresses are needed both for the create form and to render
  // contract cards with names instead of raw IDs.
  useEffect(() => {
    if (selectedOwnerId === null) return;
    let cancelled = false;
    setIsLoading(true);
    setError("");
    Promise.all([
      api.get(`/owners/${selectedOwnerId}/contracts`),
      api.get(`/owners/${selectedOwnerId}/renters`),
      api.get(`/owners/${selectedOwnerId}/addresses`),
    ])
      .then(([contractsResp, rentersResp, addressesResp]) => {
        if (!cancelled) {
          setContracts(contractsResp.data);
          setRenters(rentersResp.data);
          setAddresses(addressesResp.data);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Não foi possível carregar os contratos.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedOwnerId]);

  async function handleCreate(payload, onClose) {
    try {
      const resp = await api.post(
        `/owners/${selectedOwnerId}/contracts`,
        payload
      );
      setContracts((prev) => [...prev, resp.data]);
      onClose();
    } catch {
      setError("Não foi possível criar o contrato.");
    }
  }

  async function handleDelete(contractId) {
    if (!confirm("Excluir este contrato? Esta ação não pode ser desfeita.")) {
      return;
    }
    try {
      await api.delete(`/contracts/${contractId}`);
      setContracts((prev) => prev.filter((c) => c.id !== contractId));
    } catch {
      setError("Não foi possível excluir o contrato.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Contratos</h1>
      <p className="mt-2 text-muted-foreground">
        Cadastre e acompanhe os contratos de locação dos seus imóveis.
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
          <h2 className="text-xl font-semibold">Contratos</h2>
          <CreateContractDialog
            onCreate={handleCreate}
            renters={renters}
            addresses={addresses}
          />
        </div>
      )}

      {error && (
        <p className="mt-4 text-sm font-medium text-destructive">{error}</p>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <div className="mt-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Carregando...
            </div>
          ) : contracts.length === 0 ? (
            <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground shadow-sm">
              Nenhum contrato cadastrado para este proprietário. Clique em
              &quot;Adicionar&quot; para começar.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {contracts.map((contract) => {
                const renter = renterMap[contract.renter_id];
                const address = addressMap[contract.address_id];
                return (
                  <Card key={contract.id}>
                    <CardHeader>
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-1">
                          <CardTitle className="text-lg">
                            {renter?.name ?? `Inquilino #${contract.renter_id}`}
                          </CardTitle>
                          <CardDescription>
                            {address
                              ? `${address.street_name}, ${address.number}`
                              : `Imóvel #${contract.address_id}`}
                          </CardDescription>
                        </div>
                        <span className="shrink-0 rounded-md border bg-muted px-2 py-1 text-xs font-medium">
                          {STATUS_LABELS[contract.status] ?? contract.status}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <p className="text-sm">
                        <span className="text-muted-foreground">Período:</span>{" "}
                        {formatIsoDate(contract.start_date)} até{" "}
                        {formatIsoDate(contract.end_date)}
                      </p>
                      <p className="text-sm">
                        <span className="text-muted-foreground">Aluguel:</span>{" "}
                        {CURRENCY.format(Number(contract.monthly_revenue))}
                      </p>
                      <p className="text-sm">
                        <span className="text-muted-foreground">Depósito:</span>{" "}
                        {CURRENCY.format(Number(contract.deposit_value))} (
                        {contract.deposit_months}x)
                      </p>
                      <Button
                        className="mt-2"
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(contract.id)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Excluir
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CreateContractDialog({ onCreate, renters, addresses }) {
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
      renter_id: Number(form.renter_id),
      address_id: Number(form.address_id),
      start_date: `${form.start_date}T00:00:00`,
      end_date: `${form.end_date}T00:00:00`,
      monthly_revenue: form.monthly_revenue,
      deposit_value: form.deposit_value,
      deposit_months: Number(form.deposit_months),
    };
    setIsSubmitting(true);
    try {
      await onCreate(payload, handleClose);
    } finally {
      setIsSubmitting(false);
    }
  }

  const canSubmit =
    form.renter_id &&
    form.address_id &&
    form.start_date &&
    form.end_date &&
    form.monthly_revenue &&
    form.deposit_value &&
    form.deposit_months;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Adicionar
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Adicionar contrato</DialogTitle>
            <DialogDescription>
              Cadastre um novo contrato de locação.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="renter_id">Inquilino</Label>
                <Select
                  value={form.renter_id}
                  onValueChange={(value) => updateField("renter_id", value)}
                >
                  <SelectTrigger id="renter_id">
                    <SelectValue placeholder="Selecione o inquilino" />
                  </SelectTrigger>
                  <SelectContent>
                    {renters.map((renter) => (
                      <SelectItem key={renter.id} value={String(renter.id)}>
                        {renter.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="address_id">Imóvel</Label>
                <Select
                  value={form.address_id}
                  onValueChange={(value) => updateField("address_id", value)}
                >
                  <SelectTrigger id="address_id">
                    <SelectValue placeholder="Selecione o imóvel" />
                  </SelectTrigger>
                  <SelectContent>
                    {addresses.map((address) => (
                      <SelectItem key={address.id} value={String(address.id)}>
                        {address.street_name}, {address.number}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="start_date">Início</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={form.start_date}
                  onChange={(e) => updateField("start_date", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="end_date">Fim</Label>
                <Input
                  id="end_date"
                  type="date"
                  value={form.end_date}
                  onChange={(e) => updateField("end_date", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="grid gap-2">
                <Label htmlFor="monthly_revenue">Aluguel mensal</Label>
                <Input
                  id="monthly_revenue"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="1500,00"
                  value={form.monthly_revenue}
                  onChange={(e) => updateField("monthly_revenue", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="deposit_value">Valor do depósito</Label>
                <Input
                  id="deposit_value"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="3000,00"
                  value={form.deposit_value}
                  onChange={(e) => updateField("deposit_value", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="deposit_months">Meses de depósito</Label>
                <Input
                  id="deposit_months"
                  type="number"
                  min="1"
                  step="1"
                  placeholder="2"
                  value={form.deposit_months}
                  onChange={(e) => updateField("deposit_months", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting || !canSubmit}>
              {isSubmitting ? "Criando..." : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}