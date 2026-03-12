import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { usePriceHistory } from "../hooks/useProducts";

interface Props {
  productId: string;
  currency: string;
}

export function PriceChart({ productId, currency }: Props) {
  const { data, isLoading, isError } = usePriceHistory(productId);

  if (isLoading) return <p className="text-xs text-gray-400">Loading…</p>;
  if (isError || !data?.length)
    return <p className="text-xs text-gray-400">No history yet.</p>;

  const chartData = [...data]
    .reverse()
    .map((r) => ({
      date: new Date(r.scraped_at).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
      }),
      price: Number(r.price),
    }));

  return (
    <ResponsiveContainer width="100%" height={120}>
      <LineChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${currency}${v}`}
        />
        <Tooltip
          formatter={(v: number) => [`${currency}${v.toFixed(2)}`, "Price"]}
          labelStyle={{ fontSize: 11 }}
          contentStyle={{ fontSize: 11 }}
        />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#65503f"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
