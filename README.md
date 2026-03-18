# US Health Economy API

US healthcare economic data including health expenditure, medical prices (CPI/PPI), healthcare employment, pharmaceutical costs, and international health comparisons. Powered by FRED and World Bank.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API info and available endpoints |
| `GET /summary` | Healthcare economy overview |
| `GET /spending` | Health expenditure and GDP share |
| `GET /medical-prices` | Medical care CPI and PPI |
| `GET /employment` | Healthcare sector employment |
| `GET /insurance` | Health insurance coverage indicators |
| `GET /pharmaceuticals` | Drug price indices and pharma employment |
| `GET /comparison` | Health metrics by country (query: country=USA) |

## Query Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `country` | ISO3 country code for /comparison | `USA` |
| `limit` | Number of data points | `20` |

## Data Sources

- Federal Reserve Economic Data (FRED): https://fred.stlouisfed.org
- World Bank Open Data: https://data.worldbank.org

## Authentication

Requires `X-RapidAPI-Key` header via RapidAPI.
