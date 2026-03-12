interface Props {
  suppliers: string[];
  selectedSupplier: string;
  onSupplierChange: (s: string) => void;
  showOnlyAvailable: boolean;
  onAvailableChange: (v: boolean) => void;
  showOnlySales: boolean;
  onSalesChange: (v: boolean) => void;
  showOnlyDrops: boolean;
  onDropsChange: (v: boolean) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}

export function FilterBar({
  suppliers,
  selectedSupplier,
  onSupplierChange,
  showOnlyAvailable,
  onAvailableChange,
  showOnlySales,
  onSalesChange,
  showOnlyDrops,
  onDropsChange,
  searchQuery,
  onSearchChange,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <input
        type="search"
        placeholder="Search coffees…"
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        className="rounded-lg border border-coffee-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-coffee-500"
      />

      {/* Supplier select */}
      <select
        value={selectedSupplier}
        onChange={(e) => onSupplierChange(e.target.value)}
        className="rounded-lg border border-coffee-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-coffee-500"
      >
        <option value="">All Suppliers</option>
        {suppliers.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      {/* Toggle chips */}
      {[
        { label: "Available only", value: showOnlyAvailable, onChange: onAvailableChange },
        { label: "On sale", value: showOnlySales, onChange: onSalesChange },
        { label: "Price drops", value: showOnlyDrops, onChange: onDropsChange },
      ].map(({ label, value, onChange }) => (
        <button
          key={label}
          onClick={() => onChange(!value)}
          className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
            value
              ? "bg-coffee-800 text-white"
              : "bg-coffee-100 text-coffee-700 hover:bg-coffee-200"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
