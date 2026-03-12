import clsx from "clsx";
import { useState } from "react";
import type { Product } from "../types";
import { PriceChart } from "./PriceChart";

const CURRENCY_SYMBOL: Record<string, string> = {
  GBP: "£",
  USD: "$",
  EUR: "€",
};

interface Props {
  product: Product;
}

export function ProductCard({ product }: Props) {
  const [showHistory, setShowHistory] = useState(false);
  const symbol = CURRENCY_SYMBOL[product.currency] ?? product.currency;

  return (
    <div
      className={clsx(
        "flex flex-col rounded-2xl border bg-white shadow-sm transition hover:shadow-md",
        !product.available && "opacity-60",
        product.price_drop && "border-blue-400",
        product.on_sale && !product.price_drop && "border-amber-400"
      )}
    >
      {/* Image */}
      <div className="relative h-44 overflow-hidden rounded-t-2xl bg-coffee-100">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-5xl">
            ☕
          </div>
        )}

        {/* Badges */}
        <div className="absolute left-2 top-2 flex gap-1">
          {product.on_sale && (
            <span className="rounded-full bg-amber-400 px-2 py-0.5 text-xs font-bold text-white shadow">
              SALE
            </span>
          )}
          {product.price_drop && (
            <span className="rounded-full bg-blue-500 px-2 py-0.5 text-xs font-bold text-white shadow">
              -{product.price_drop_pct?.toFixed(0)}% DROP
            </span>
          )}
          {!product.available && (
            <span className="rounded-full bg-red-500 px-2 py-0.5 text-xs font-bold text-white shadow">
              OUT OF STOCK
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col p-4">
        <p className="text-xs font-medium text-coffee-600">{product.supplier}</p>
        <a
          href={product.url}
          target="_blank"
          rel="noreferrer"
          className="mt-1 line-clamp-2 font-semibold text-coffee-900 hover:underline"
        >
          {product.name}
        </a>

        {/* Price */}
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-coffee-900">
            {symbol}{Number(product.current_price).toFixed(2)}
          </span>
          {product.previous_price && product.price_drop && (
            <span className="text-sm text-gray-400 line-through">
              {symbol}{Number(product.previous_price).toFixed(2)}
            </span>
          )}
        </div>

        {/* History toggle */}
        <button
          onClick={() => setShowHistory((v) => !v)}
          className="mt-3 self-start text-xs text-coffee-600 underline-offset-2 hover:underline"
        >
          {showHistory ? "Hide" : "Show"} price history
        </button>

        {showHistory && (
          <div className="mt-2">
            <PriceChart productId={product.product_id} currency={symbol} />
          </div>
        )}
      </div>
    </div>
  );
}
