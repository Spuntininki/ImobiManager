import { Loader2, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import api from "@/lib/api";
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
import { useAuth } from "@/contexts/AuthContext";

export function Dashboard() {
  const { email, logout } = useAuth();
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Bem-vindo{email ? `, ${email}` : ""}. Gerencie seus proprietários.
          </p>
        </div>
        <Button onClick={logout} variant="outline">
          Sair
        </Button>
      </div>

      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Proprietários</h2>
        <CreateOwnerDialog onCreate={handleCreate} />
      </div>

      {error && (
        <p className="mt-4 text-sm font-medium text-destructive">{error}</p>
      )}

      <div className="mt-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            Carregando...
          </div>
        ) : owners.length === 0 ? (
          <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground shadow-sm">
            Nenhum proprietário cadastrado. Clique em &quot;Adicionar&quot; para começar.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {owners.map((owner) => (
              <Card key={owner.id}>
                <CardHeader>
                  <CardTitle className="text-lg">{owner.name}</CardTitle>
                  <CardDescription>
                    ID {owner.id}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(owner.id)}
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
    </div>
  );
}

function CreateOwnerDialog({ onCreate }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleClose() {
    setOpen(false);
    setName("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await onCreate(name.trim(), handleClose);
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
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Adicionar proprietário</DialogTitle>
            <DialogDescription>
              Cadastre um novo proprietário para associar imóveis e contratos.
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
              {isSubmitting ? "Criando..." : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}