import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { DigestBanner } from "../components/DigestBanner";
import { FilterBar } from "../components/FilterBar";
import { ProductCard } from "../components/ProductCard";
import { triggerScrape, useDigest, useProducts } from "../hooks/useProducts";
import type { Product } from "../types";

export function Dashboard() {
  const { data: products, isLoading: loadingProducts } = useProducts();
  const { data: digest, isLoading: loadingDigest } = useDigest();
  const queryClient = useQueryClient();

  const [selectedSupplier, setSelectedSupplier] = useState("");
  const [showOnlyAvailable, setShowOnlyAvailable] = useState(false);
  const [showOnlySales, setShowOnlySales] = useState(false);
  const [showOnlyDrops, setShowOnlyDrops] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [scraping, setScraping] = useState(false);

  const suppliers = [...new Set((products ?? []).map((p) => p.supplier))].sort();

  const filtered = (products ?? []).filter((p: Product) => {
    if (selectedSupplier && p.supplier !== selectedSupplier) return false;
    if (showOnlyAvailable && !p.available) return false;
    if (showOnlySales && !p.on_sale) return false;
    if (showOnlyDrops && !p.price_drop) return false;
    if (searchQuery && !p.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  async function handleScrape() {
    setScraping(true);
    await triggerScrape();
    await queryClient.invalidateQueries();
    setScraping(false);
  }

  return (
    <div className="min-h-screen bg-coffee-50">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-coffee-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">☕</span>
            <span className="text-lg font-bold text-coffee-900">
              Coffee Prices
            </span>
          </div>
          <button
            onClick={handleScrape}
            disabled={scraping}
            className="rounded-lg bg-coffee-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-coffee-900 disabled:opacity-50"
          >
            {scraping ? "Refreshing…" : "Refresh Now"}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        {/* Digest banner */}
        {loadingDigest ? (
          <div className="h-36 animate-pulse rounded-2xl bg-coffee-200" />
        ) : digest ? (
          <DigestBanner digest={digest} />
        ) : null}

        {/* Filters */}
        <FilterBar
          suppliers={suppliers}
          selectedSupplier={selectedSupplier}
          onSupplierChange={setSelectedSupplier}
          showOnlyAvailable={showOnlyAvailable}
          onAvailableChange={setShowOnlyAvailable}
          showOnlySales={showOnlySales}
          onSalesChange={setShowOnlySales}
          showOnlyDrops={showOnlyDrops}
          onDropsChange={setShowOnlyDrops}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />

        {/* Results count */}
        {!loadingProducts && (
          <p className="text-sm text-coffee-600">
            Showing {filtered.length} of {products?.length ?? 0} products
          </p>
        )}

        {/* Product grid */}
        {loadingProducts ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-64 animate-pulse rounded-2xl bg-coffee-200" />
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtered.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        ) : (
          <div className="py-20 text-center text-coffee-500">
            <p className="text-4xl">☕</p>
            <p className="mt-2 text-lg font-medium">No coffees found</p>
            <p className="text-sm">Try adjusting your filters or hit Refresh Now.</p>
          </div>
        )}
      </main>
    </div>
  );
}
