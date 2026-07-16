import { Pencil, Plus } from "lucide-react";
import { useState } from "react";

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
import type { Contract, Renter, Address } from "@/types/domain";

interface ContractDialogProps {
  contract?: Contract;
  renters: Renter[];
  addresses: Address[];
  onSubmit: (payload: Record<string, unknown>, onClose: () => void) => void;
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Pendente",
  ACTIVE: "Ativo",
  EXPIRED: "Expirado",
  CANCELLED: "Cancelado",
};

const EMPTY_FORM = {
  renter_id: "",
  address_id: "",
  start_date: "",
  end_date: "",
  monthly_revenue: "",
  deposit_value: "",
  deposit_months: "",
  payment_day: "",
};

export function ContractDialog({ contract, renters, addresses, onSubmit }: ContractDialogProps) {
  const isEdit = contract !== undefined;
  const initialForm = isEdit
    ? {
        renter_id: String(contract.renter_id),
        address_id: String(contract.address_id),
        start_date: contract.start_date.split("T")[0],
        end_date: contract.end_date.split("T")[0],
        monthly_revenue: String(contract.monthly_revenue),
        deposit_value: String(contract.deposit_value),
        deposit_months: String(contract.deposit_months),
        payment_day: String(contract.payment_day),
        status: contract.status,
      }
    : EMPTY_FORM;
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleClose() {
    setOpen(false);
    setForm(initialForm);
    setFieldErrors({});
  }

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => ({ ...prev, [field]: "" }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldErrors({});

    const errors: Record<string, string> = {};

    if (!form.start_date) {
      errors.start_date = "Data de início é obrigatória.";
    }
    if (!form.end_date) {
      errors.end_date = "Data de fim é obrigatória.";
    }
    if (form.start_date && form.end_date && form.start_date >= form.end_date) {
      errors.end_date = "Data de fim deve ser posterior à data de início.";
    }
    if (form.deposit_months && Number(form.deposit_months) > 12) {
      errors.deposit_months = "Meses de depósito deve ser no máximo 12.";
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    const payload: Record<string, unknown> = {
      renter_id: Number(form.renter_id),
      address_id: Number(form.address_id),
      start_date: `${form.start_date}T00:00:00`,
      end_date: `${form.end_date}T00:00:00`,
      monthly_revenue: form.monthly_revenue,
      deposit_value: form.deposit_value,
      deposit_months: Number(form.deposit_months),
      payment_day: Number(form.payment_day),
    };
    if (isEdit) {
      payload.status = (form as any).status;
    }
    setIsSubmitting(true);
    try {
      await onSubmit(payload, handleClose);
    } catch {
      // Error handled by parent
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
    form.deposit_months &&
    form.payment_day !== "";

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
      <DialogContent className="max-w-2xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Editar contrato" : "Adicionar contrato"}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? "Altere os dados do contrato de locação."
                : "Cadastre um novo contrato de locação."}
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
                    {renters.map((renter: Renter) => (
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
                    {addresses.map((address: Address) => (
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
                  aria-invalid={!!fieldErrors.start_date}
                />
                {fieldErrors.start_date && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.start_date}
                  </p>
                )}
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
                  aria-invalid={!!fieldErrors.end_date}
                />
                {fieldErrors.end_date && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.end_date}
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
                  max="12"
                  step="1"
                  placeholder="2"
                  value={form.deposit_months}
                  onChange={(e) => updateField("deposit_months", e.target.value)}
                  disabled={isSubmitting}
                  required
                  aria-invalid={!!fieldErrors.deposit_months}
                />
                {fieldErrors.deposit_months && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.deposit_months}
                  </p>
                )}
              </div>

              <div className="grid gap-2">
                <Label htmlFor="payment_day">Dia de pagamento</Label>
                <Input
                  id="payment_day"
                  type="number"
                  min="1"
                  max="31"
                  step="1"
                  placeholder="5"
                  value={form.payment_day}
                  onChange={(e) => updateField("payment_day", e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>
            </div>

            {isEdit && (
              <div className="grid gap-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={(form as any).status}
                  onValueChange={(value) => updateField("status", value)}
                >
                  <SelectTrigger id="status">
                    <SelectValue placeholder="Selecione o status" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(STATUS_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting || !canSubmit}>
              {isSubmitting ? "Salvando..." : isEdit ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
