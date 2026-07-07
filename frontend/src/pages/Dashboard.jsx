import { Building2 } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";

export function Dashboard() {
  const { email, userName } = useAuth();

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
      <p className="mt-2 text-muted-foreground">
        Bem-vindo{userName ? `, ${userName}` : email ? `, ${email}` : ""}.
      </p>

      <div className="mt-8 flex flex-col items-center justify-center rounded-lg border bg-card p-12 text-center text-card-foreground shadow-sm">
        <Building2 className="h-12 w-12 text-muted-foreground" />
        <h2 className="mt-4 text-xl font-semibold">ImobiManager</h2>
        <p className="mt-2 max-w-md text-muted-foreground">
          Use o menu acima para gerenciar imóveis, inquilinos e contratos.
          Os proprietários podem ser gerenciados em
          &quot;Configurações&quot;.
        </p>
      </div>
    </div>
  );
}