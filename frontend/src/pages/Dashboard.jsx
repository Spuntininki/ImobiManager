import { Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { useOwners } from "@/lib/useOwners";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CURRENCY = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

function formatIsoDate(isoDate) {
  if (!isoDate) return "";
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

function formatShortMonth(isoDate) {
  if (!isoDate) return "";
  const [year, month] = isoDate.split("-");
  return `${month}/${year}`;
}

function formatCurrencyShort(value) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    notation: "compact",
    compactDisplay: "short",
  }).format(value);
}

function getDefaultDateRange() {
  const today = new Date();
  const start = today.toISOString().split("T")[0];
  const end = new Date(today.setFullYear(today.getFullYear() + 1))
    .toISOString()
    .split("T")[0];
  return { start, end };
}

export function Dashboard() {
  const { email, userName } = useAuth();
  const { owners, isLoading: ownersLoading, error: ownersError } = useOwners();
  const [selectedOwnerId, setSelectedOwnerId] = useState(null);

  const defaultRange = useMemo(() => getDefaultDateRange(), []);
  const [startDate, setStartDate] = useState(defaultRange.start);
  const [endDate, setEndDate] = useState(defaultRange.end);

  const [timeline, setTimeline] = useState([]);
  const [summary, setSummary] = useState({ total_amount: "0.00", total_payments: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (selectedOwnerId === null && owners.length > 0) {
      setSelectedOwnerId(String(owners[0].id));
    }
  }, [owners, selectedOwnerId]);

  useEffect(() => {
    if (selectedOwnerId === null) return;
    let cancelled = false;
    setIsLoading(true);
    setError("");
    Promise.all([
      api.get(`/owners/${selectedOwnerId}/revenue-timeline`, {
        params: { start_date: startDate, end_date: endDate },
      }),
      api.get(`/owners/${selectedOwnerId}/revenue-timeline/summary`, {
        params: { start_date: startDate, end_date: endDate },
      }),
    ])
      .then(([timelineResp, summaryResp]) => {
        if (!cancelled) {
          setTimeline(timelineResp.data);
          setSummary(summaryResp.data);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Não foi possível carregar a projeção de receitas.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedOwnerId, startDate, endDate]);

  const chartData = useMemo(
    () =>
      timeline.map((item) => ({
        label: formatShortMonth(item.payment_date),
        amount: Number(item.amount),
        fullDate: formatIsoDate(item.payment_date),
      })),
    [timeline]
  );

  return (
    <div className="mx-auto w-full max-w-[1800px] px-4 py-8 md:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
      <p className="mt-2 text-muted-foreground">
        Bem-vindo{userName ? `, ${userName}` : email ? `, ${email}` : ""}.
      </p>

      <div className="mt-6 grid gap-4 md:grid-cols-[1fr_180px_180px]">
        <div className="grid gap-2">
          <Label htmlFor="owner-select">Proprietário</Label>
          {ownersLoading ? (
            <div className="flex items-center text-sm text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Carregando...
            </div>
          ) : owners.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nenhum proprietário cadastrado.
            </p>
          ) : (
            <Select
              value={selectedOwnerId ?? undefined}
              onValueChange={setSelectedOwnerId}
            >
              <SelectTrigger id="owner-select">
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

        <div className="grid gap-2">
          <Label htmlFor="start-date">Data inicial</Label>
          <Input
            id="start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="end-date">Data final</Label>
          <Input
            id="end-date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
      </div>

      {ownersError && (
        <p className="mt-4 text-sm font-medium text-destructive">{ownersError}</p>
      )}

      {error && (
        <p className="mt-4 text-sm font-medium text-destructive">{error}</p>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardDescription>Total a receber</CardDescription>
              <CardTitle className="text-2xl">
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  CURRENCY.format(Number(summary.total_amount))
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                No período selecionado
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardDescription>Total de pagamentos</CardDescription>
              <CardTitle className="text-2xl">
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  summary.total_payments
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Parcelas projetadas
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardDescription>Receita média mensal</CardDescription>
              <CardTitle className="text-2xl">
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : summary.total_payments > 0 ? (
                  CURRENCY.format(
                    Number(summary.total_amount) / summary.total_payments
                  )
                ) : (
                  CURRENCY.format(0)
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Média dos valores projetados por mês
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {selectedOwnerId !== null && owners.length > 0 && (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Projeção de receitas</CardTitle>
            <CardDescription>
              Valores que o proprietário deve receber ao longo do período.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground">
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Carregando...
              </div>
            ) : chartData.length === 0 ? (
              <div className="py-16 text-center text-muted-foreground">
                Nenhuma receita projetada para este período.
                <br />
                Verifique se existem contratos ativos para o proprietário
                selecionado.
              </div>
            ) : (
              <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    margin={{ top: 8, right: 8, bottom: 8, left: 0 }}
                    maxBarSize={48}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={formatCurrencyShort}
                    />
                    <Tooltip
                      formatter={(value) => [CURRENCY.format(Number(value)), "Valor"]}
                      labelFormatter={(_label, payload) =>
                        payload?.[0]?.payload?.fullDate ?? _label
                      }
                      cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }}
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "0.5rem",
                        color: "hsl(var(--card-foreground))",
                      }}
                      itemStyle={{ color: "hsl(var(--card-foreground))" }}
                    />
                    <Bar
                      dataKey="amount"
                      fill="hsl(var(--primary))"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
