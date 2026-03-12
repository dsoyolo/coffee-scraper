export interface Product {
  product_id: string;
  supplier: string;
  name: string;
  url: string;
  image_url: string | null;
  current_price: number;
  previous_price: number | null;
  currency: "GBP" | "USD" | "EUR";
  available: boolean;
  on_sale: boolean;
  price_drop: boolean;
  price_drop_pct: number | null;
  last_updated: string;
}

export interface PriceRecord {
  price: number;
  currency: string;
  available: boolean;
  on_sale: boolean;
  scraped_at: string;
}

export interface DigestSummary {
  generated_at: string;
  total_products: number;
  available_count: number;
  unavailable_count: number;
  on_sale_count: number;
  price_drops: Product[];
  new_sales: Product[];
  back_in_stock: Product[];
  out_of_stock: Product[];
  all_products: Product[];
}
