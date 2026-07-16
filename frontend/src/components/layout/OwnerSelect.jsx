import { Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * Standard owner selector used by Properties, Tenants, and Contracts.
 * The three pages share the same label-friendly layout: a left-aligned
 * "Proprietário" label (sm:w-32) and a select (sm:w-80) with three states
 * (loading, empty-with-link-to-settings, populated). Dashboard uses a
 * bespoke layout and is left out of this abstraction.
 */
export function OwnerSelect({
  owners,
  isLoading,
  selectedOwnerId,
  onSelect,
}) {
  return (
    <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
      <Label htmlFor="owner-select" className="sm:w-32">
        Proprietário
      </Label>
      {isLoading ? (
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
          onValueChange={onSelect}
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
  );
}