# Coffee Price Aggregator

Tracks your favourite coffees across preferred suppliers, highlights availability, sales and price drops, and delivers a daily digest dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                            │
│                                                             │
│  CloudFront ──► S3 (React SPA)                             │
│                                                             │
│  API Gateway ──► Lambda (FastAPI via Mangum)               │
│                      │                                      │
│                      ▼                                      │
│                 DynamoDB (products + price history)         │
│                                                             │
│  EventBridge (cron) ──► Lambda (scraper job)               │
└─────────────────────────────────────────────────────────────┘
```

## Stack

| Component | Technology |
|-----------|-----------|
| Backend   | Python 3.12, FastAPI, httpx, BeautifulSoup4 |
| Frontend  | React 18, TypeScript, Tailwind CSS, Recharts |
| Database  | AWS DynamoDB |
| Infra     | AWS CDK (Python) |
| Hosting   | Lambda + API Gateway, S3 + CloudFront |

## Project Layout

```
coffee-scraper/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── models/       # Pydantic models
│   │   ├── scrapers/     # Per-supplier scrapers + base
│   │   └── services/     # DynamoDB, digest, comparison logic
│   ├── tests/
│   ├── suppliers.yaml    # Supplier config (URLs, selectors)
│   ├── requirements.txt
│   └── lambda_handler.py
├── frontend/
│   ├── src/
│   │   ├── components/   # ProductCard, PriceChart, DigestBanner
│   │   ├── pages/        # Dashboard, Suppliers
│   │   ├── hooks/        # useProducts, useDigest
│   │   └── types/        # TypeScript interfaces
│   ├── package.json
│   └── ...
└── infra/
    ├── app.py            # CDK app entry point
    ├── stacks/           # CDK stacks
    └── requirements.txt
```

## Getting Started

### Local development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Deploy to AWS

```bash
cd infra
pip install -r requirements.txt
cdk bootstrap
cdk deploy --all
```

## Adding a Supplier

Edit `backend/suppliers.yaml`:

```yaml
suppliers:
  - name: "My Coffee Shop"
    base_url: "https://example.com"
    products_url: "https://example.com/coffee"
    selectors:
      product_list: ".product-item"
      name: ".product-title"
      price: ".price"
      availability: ".stock-status"
      sale_badge: ".sale-badge"        # optional
      image: "img"                     # optional
```
