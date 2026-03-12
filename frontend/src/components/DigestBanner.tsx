import type { DigestSummary } from "../types";

interface Props {
  digest: DigestSummary;
}

interface StatProps {
  label: string;
  value: number;
  color: string;
}

function Stat({ label, value, color }: StatProps) {
  return (
    <div className={`flex flex-col items-center rounded-xl p-4 ${color}`}>
      <span className="text-3xl font-bold">{value}</span>
      <span className="mt-1 text-sm font-medium opacity-80">{label}</span>
    </div>
  );
}

export function DigestBanner({ digest }: Props) {
  const updated = new Date(digest.generated_at).toLocaleString();

  return (
    <div className="rounded-2xl bg-coffee-900 p-6 text-white shadow-lg">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-xl font-bold tracking-tight">Daily Digest</h2>
        <span className="text-xs opacity-60">Updated {updated}</span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat
          label="Available"
          value={digest.available_count}
          color="bg-emerald-700"
        />
        <Stat
          label="Out of Stock"
          value={digest.unavailable_count}
          color="bg-red-700"
        />
        <Stat
          label="On Sale"
          value={digest.on_sale_count}
          color="bg-amber-600"
        />
        <Stat
          label="Price Drops"
          value={digest.price_drops.length}
          color="bg-blue-700"
        />
      </div>

      {digest.price_drops.length > 0 && (
        <div className="mt-4 border-t border-coffee-700 pt-4">
          <p className="mb-2 text-sm font-semibold text-amber-300">
            Biggest price drops today
          </p>
          <ul className="space-y-1">
            {digest.price_drops.slice(0, 3).map((p) => (
              <li key={p.product_id} className="flex justify-between text-sm">
                <a
                  href={p.url}
                  target="_blank"
                  rel="noreferrer"
                  className="truncate underline-offset-2 hover:underline"
                >
                  {p.name}
                </a>
                <span className="ml-4 shrink-0 text-emerald-300">
                  -{p.price_drop_pct?.toFixed(1)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
