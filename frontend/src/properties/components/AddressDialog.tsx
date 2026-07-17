import { Pencil, Plus } from "lucide-react";
import { useState } from "react";

import {
  validateState,
  validateZipCode,
  validateRequiredText,
} from "@/lib/formatters";
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
import type { Address } from "@/types/domain";

interface AddressDialogProps {
  address?: Address;
  onSubmit: (payload: Record<string, unknown>, onClose: () => void) => void;
}

const PROPERTY_TYPE_LABELS: Record<string, string> = {
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

export function AddressDialog({ address, onSubmit }: AddressDialogProps) {
  const isEdit = address !== undefined;
  const initialForm = isEdit
    ? {
        street_name: address.street_name,
        number: address.number,
        complement: address.complement ?? "",
        neighborhood: address.neighborhood,
        city: address.city,
        state: address.state,
        zip_code: address.zip_code,
        type: address.type,
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

    const trimmed: Record<string, string | null> = {
      street_name: form.street_name.trim(),
      number: form.number.trim(),
      complement: form.complement.trim() || null,
      neighborhood: form.neighborhood.trim(),
      city: form.city.trim(),
      state: form.state.trim().toUpperCase(),
      zip_code: form.zip_code.trim(),
    };

    const errors: Record<string, string> = {};
    const streetErr = validateRequiredText(trimmed.street_name as string, "Logradouro");
    if (streetErr) errors.street_name = streetErr;
    const numberErr = validateRequiredText(trimmed.number as string, "Número", 20);
    if (numberErr) errors.number = numberErr;
    const neighborhoodErr = validateRequiredText(trimmed.neighborhood as string, "Bairro");
    if (neighborhoodErr) errors.neighborhood = neighborhoodErr;
    const cityErr = validateRequiredText(trimmed.city as string, "Cidade");
    if (cityErr) errors.city = cityErr;
    const stateErr = validateState(trimmed.state as string);
    if (stateErr) errors.state = stateErr;
    const zipErr = validateZipCode(trimmed.zip_code as string);
    if (zipErr) errors.zip_code = zipErr;

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    const payload: Record<string, unknown> = { ...trimmed, type: form.type };
    setIsSubmitting(true);
    try {
      await onSubmit(payload, handleClose);
    } catch {
      // Error handled by parent
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
      <DialogContent className="max-w-xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Editar imóvel" : "Adicionar imóvel"}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? "Altere os dados do endereço."
                : "Cadastre o endereço de uma propriedade."}
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
                  maxLength={255}
                  required
                  autoFocus
                  aria-invalid={!!fieldErrors.street_name}
                />
                {fieldErrors.street_name && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.street_name}
                  </p>
                )}
              </div>
              <div className="grid gap-2">
                <Label htmlFor="number">Número</Label>
                <Input
                  id="number"
                  placeholder="123"
                  value={form.number}
                  onChange={(e) => updateField("number", e.target.value)}
                  disabled={isSubmitting}
                  maxLength={20}
                  required
                  aria-invalid={!!fieldErrors.number}
                />
                {fieldErrors.number && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.number}
                  </p>
                )}
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
                maxLength={255}
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
                maxLength={255}
                required
                aria-invalid={!!fieldErrors.neighborhood}
              />
              {fieldErrors.neighborhood && (
                <p className="text-sm font-medium text-destructive">
                  {fieldErrors.neighborhood}
                </p>
              )}
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
                  maxLength={255}
                  required
                  aria-invalid={!!fieldErrors.city}
                />
                {fieldErrors.city && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.city}
                  </p>
                )}
              </div>
              <div className="grid gap-2">
                <Label htmlFor="state">Estado</Label>
                <Input
                  id="state"
                  placeholder="SP"
                  value={form.state}
                  onChange={(e) => updateField("state", e.target.value)}
                  disabled={isSubmitting}
                  maxLength={2}
                  required
                  aria-invalid={!!fieldErrors.state}
                />
                {fieldErrors.state && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.state}
                  </p>
                )}
              </div>
              <div className="grid gap-2">
                <Label htmlFor="zip_code">CEP</Label>
                <Input
                  id="zip_code"
                  placeholder="01000-000"
                  value={form.zip_code}
                  onChange={(e) => updateField("zip_code", e.target.value)}
                  disabled={isSubmitting}
                  maxLength={9}
                  required
                  aria-invalid={!!fieldErrors.zip_code}
                />
                {fieldErrors.zip_code && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.zip_code}
                  </p>
                )}
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
              {isSubmitting ? "Salvando..." : isEdit ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
