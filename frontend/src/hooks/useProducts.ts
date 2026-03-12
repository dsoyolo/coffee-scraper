import { useQuery } from "@tanstack/react-query";
import type { DigestSummary, PriceRecord, Product } from "../types";

const API = import.meta.env.VITE_API_URL ?? "/api";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

export function useProducts() {
  return useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: () => fetchJson<Product[]>("/products/"),
    refetchInterval: 5 * 60 * 1000, // refresh every 5 min
  });
}

export function useDigest() {
  return useQuery<DigestSummary>({
    queryKey: ["digest"],
    queryFn: () => fetchJson<DigestSummary>("/products/digest"),
    refetchInterval: 5 * 60 * 1000,
  });
}

export function usePriceHistory(productId: string) {
  return useQuery<PriceRecord[]>({
    queryKey: ["history", productId],
    queryFn: () =>
      fetchJson<PriceRecord[]>(
        `/products/${encodeURIComponent(productId)}/history`
      ),
    enabled: Boolean(productId),
  });
}

export async function triggerScrape(): Promise<void> {
  await fetch(`${API}/scrape/`, { method: "POST" });
}
