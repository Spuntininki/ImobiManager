import { useQuery } from "@tanstack/react-query";

import {
  getRevenueTimeline,
  getRevenueSummary,
} from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";

const EMPTY_TIMELINE: unknown[] = [];
const EMPTY_SUMMARY: { total_amount: string; total_payments: number } = {
  total_amount: "0.00",
  total_payments: 0,
};

export function useRevenueTimeline(
  ownerId: number | undefined,
  {
    start_date,
    end_date,
  }: { start_date: string; end_date: string },
) {
  const range = { start_date, end_date };
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.revenueTimeline(ownerId!, range),
    queryFn: () => getRevenueTimeline(ownerId!, range),
    enabled: ownerId != null,
  });
  return {
    timeline: data ?? EMPTY_TIMELINE,
    isLoading,
    error: error ? "Não foi possível carregar a projeção de receitas." : "",
  };
}

export function useRevenueSummary(
  ownerId: number | undefined,
  {
    start_date,
    end_date,
  }: { start_date: string; end_date: string },
) {
  const range = { start_date, end_date };
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.revenueSummary(ownerId!, range),
    queryFn: () => getRevenueSummary(ownerId!, range),
    enabled: ownerId != null,
  });
  return {
    summary: data ?? EMPTY_SUMMARY,
    isLoading,
    error: error ? "Não foi possível carregar a projeção de receitas." : "",
  };
}
