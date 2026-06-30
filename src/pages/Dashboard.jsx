export function Dashboard() {
  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
      <p className="mt-2 text-muted-foreground">
        Bem-vindo ao ImobiManager. Aqui você terá uma visão geral dos seus
        imóveis, inquilinos e contratos.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <h2 className="text-lg font-semibold">Imóveis</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Cadastro de endereços e propriedades.
          </p>
        </div>

        <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <h2 className="text-lg font-semibold">Inquilinos</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Gestão dos moradores e seus dados.
          </p>
        </div>

        <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <h2 className="text-lg font-semibold">Contratos</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Condições contratuais e vencimentos.
          </p>
        </div>
      </div>
    </div>
  );
}
