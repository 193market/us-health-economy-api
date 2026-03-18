from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(title="US Health Economy API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

FRED_KEY = os.environ.get("FRED_API_KEY", "")
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
WB_BASE = "https://api.worldbank.org/v2"

async def fred(series_id: str, limit: int = 20, frequency: str = None):
    params = {
        "series_id": series_id,
        "api_key": FRED_KEY,
        "file_type": "json",
        "limit": limit,
        "sort_order": "desc"
    }
    if frequency:
        params["frequency"] = frequency
    async with httpx.AsyncClient() as client:
        r = await client.get(FRED_BASE, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        obs = [o for o in data.get("observations", []) if o.get("value") != "."]
        return obs

async def worldbank(indicator: str, country: str = "US", limit: int = 20):
    url = f"{WB_BASE}/country/{country}/indicator/{indicator}"
    params = {"format": "json", "per_page": limit, "mrv": limit}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if len(data) < 2 or not data[1]:
            return []
        return [{"year": d["date"], "value": d["value"]} for d in data[1] if d.get("value") is not None]

@app.get("/")
async def root():
    return {
        "api": "US Health Economy API",
        "version": "1.0.0",
        "description": "US healthcare economic data including health spending, medical prices, pharmaceutical costs, healthcare employment, and insurance. Powered by FRED and World Bank.",
        "endpoints": [
            "GET /summary - Healthcare economy overview",
            "GET /spending - Health expenditure and GDP share",
            "GET /medical-prices - Medical care CPI and PPI",
            "GET /employment - Healthcare sector employment",
            "GET /insurance - Health insurance coverage indicators",
            "GET /pharmaceuticals - Drug price indices",
            "GET /comparison - US vs global health spending"
        ],
        "source": "FRED (Federal Reserve Economic Data) + World Bank"
    }

@app.get("/summary")
async def summary():
    try:
        med_cpi = await fred("CPIMEDSL", limit=4)
        health_employ = await fred("CES6562000001", limit=4)
        pce_health = await fred("DHLCRG3Q086SBEA", limit=4)
        drug_ppi = await fred("PCU3254132541", limit=4)
        return {
            "medical_cpi": {"series": "CPIMEDSL", "description": "CPI: Medical Care", "data": med_cpi[:4]},
            "healthcare_employment": {"series": "CES6562000001", "description": "Health Care & Social Assistance Employment (thousands)", "data": health_employ[:4]},
            "health_pce_deflator": {"series": "DHLCRG3Q086SBEA", "description": "PCE: Health Care Services Price Index", "data": pce_health[:4]},
            "pharmaceutical_ppi": {"series": "PCU3254132541", "description": "PPI: Pharmaceutical Products", "data": drug_ppi[:4]}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spending")
async def spending(limit: int = 20):
    try:
        pce_health = await fred("DHLCRG3Q086SBEA", limit=limit)
        health_pct_gdp = await worldbank("SH.XPD.CHEX.GD.ZS", country="US", limit=limit)
        health_per_capita = await worldbank("SH.XPD.CHEX.PC.CD", country="US", limit=limit)
        oop_pct = await worldbank("SH.XPD.OOPC.CH.ZS", country="US", limit=limit)
        return {
            "description": "US health expenditure data",
            "pce_health_services_deflator": {
                "series": "DHLCRG3Q086SBEA",
                "description": "PCE: Health Care Services Price Index (Quarterly)",
                "source": "FRED",
                "data": pce_health
            },
            "health_pct_gdp": {
                "indicator": "SH.XPD.CHEX.GD.ZS",
                "description": "Current Health Expenditure (% of GDP)",
                "source": "World Bank",
                "data": health_pct_gdp
            },
            "health_per_capita_usd": {
                "indicator": "SH.XPD.CHEX.PC.CD",
                "description": "Current Health Expenditure per Capita (USD)",
                "source": "World Bank",
                "data": health_per_capita
            },
            "out_of_pocket_pct": {
                "indicator": "SH.XPD.OOPC.CH.ZS",
                "description": "Out-of-Pocket Expenditure (% of Current Health Expenditure)",
                "source": "World Bank",
                "data": oop_pct
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/medical-prices")
async def medical_prices(limit: int = 24):
    try:
        med_cpi = await fred("CPIMEDSL", limit=limit)
        hospital_cpi = await fred("CPIEDUSL", limit=limit)
        physician_cpi = await fred("CPIAPPSL", limit=limit)
        rx_cpi = await fred("CUSR0000SAM2", limit=limit)
        med_ppi = await fred("PCUHL--HL--", limit=limit)
        return {
            "description": "Medical care price indices",
            "medical_care_cpi": {
                "series": "CPIMEDSL",
                "description": "CPI: Medical Care (All Urban Consumers)",
                "data": med_cpi
            },
            "rx_drugs_cpi": {
                "series": "CUSR0000SAM2",
                "description": "CPI: Medical Care Commodities (Drugs)",
                "data": rx_cpi
            },
            "hospital_ppi": {
                "series": "PCUHL--HL--",
                "description": "PPI: Health Care Services",
                "data": med_ppi
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/employment")
async def employment(limit: int = 24):
    try:
        health_social = await fred("CES6562000001", limit=limit)
        ambulatory = await fred("CES0620100001", limit=limit)
        hospitals = await fred("CES0620200001", limit=limit)
        nursing = await fred("CES0620300001", limit=limit)
        return {
            "description": "Healthcare sector employment data",
            "health_social_assistance": {
                "series": "CES6562000001",
                "description": "Health Care & Social Assistance: All Employees (thousands)",
                "data": health_social
            },
            "ambulatory_health_services": {
                "series": "CES0620100001",
                "description": "Ambulatory Health Care Services: All Employees (thousands)",
                "data": ambulatory
            },
            "hospitals": {
                "series": "CES0620200001",
                "description": "Hospitals: All Employees (thousands)",
                "data": hospitals
            },
            "nursing_residential_care": {
                "series": "CES0620300001",
                "description": "Nursing & Residential Care: All Employees (thousands)",
                "data": nursing
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insurance")
async def insurance(limit: int = 20):
    try:
        uninsured = await worldbank("SH.UHC.SRHC.ZS", country="US", limit=limit)
        uhc_index = await worldbank("SH.UHC.SRVS.CV.XD", country="US", limit=limit)
        return {
            "description": "Health insurance and coverage data",
            "uhc_service_coverage": {
                "indicator": "SH.UHC.SRVS.CV.XD",
                "description": "UHC Service Coverage Index (0-100)",
                "source": "World Bank",
                "data": uhc_index
            },
            "reproductive_health_coverage": {
                "indicator": "SH.UHC.SRHC.ZS",
                "description": "Universal Health Coverage - Reproductive Health Services (%)",
                "source": "World Bank",
                "data": uninsured
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pharmaceuticals")
async def pharmaceuticals(limit: int = 24):
    try:
        pharma_ppi = await fred("PCU3254132541", limit=limit)
        rx_cpi = await fred("CUSR0000SAM2", limit=limit)
        pharma_manuf = await fred("CES3254100001", limit=limit)
        return {
            "description": "Pharmaceutical industry price and employment data",
            "pharmaceutical_ppi": {
                "series": "PCU3254132541",
                "description": "PPI: Pharmaceutical & Medicine Manufacturing",
                "data": pharma_ppi
            },
            "rx_drug_cpi": {
                "series": "CUSR0000SAM2",
                "description": "CPI: Medical Care Commodities (including Rx drugs)",
                "data": rx_cpi
            },
            "pharma_employment": {
                "series": "CES3254100001",
                "description": "Pharmaceutical & Medicine Manufacturing Employment (thousands)",
                "data": pharma_manuf
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/comparison")
async def comparison(country: str = "USA", limit: int = 20):
    try:
        health_pct_gdp = await worldbank("SH.XPD.CHEX.GD.ZS", country=country, limit=limit)
        life_expectancy = await worldbank("SP.DYN.LE00.IN", country=country, limit=limit)
        physicians = await worldbank("SH.MED.PHYS.ZS", country=country, limit=limit)
        infant_mortality = await worldbank("SP.DYN.IMRT.IN", country=country, limit=limit)
        return {
            "country": country,
            "description": "Health system performance metrics for comparison",
            "health_expenditure_pct_gdp": {
                "indicator": "SH.XPD.CHEX.GD.ZS",
                "description": "Current Health Expenditure (% of GDP)",
                "data": health_pct_gdp
            },
            "life_expectancy": {
                "indicator": "SP.DYN.LE00.IN",
                "description": "Life Expectancy at Birth (years)",
                "data": life_expectancy
            },
            "physicians_per_1000": {
                "indicator": "SH.MED.PHYS.ZS",
                "description": "Physicians per 1,000 People",
                "data": physicians
            },
            "infant_mortality": {
                "indicator": "SP.DYN.IMRT.IN",
                "description": "Infant Mortality Rate (per 1,000 live births)",
                "data": infant_mortality
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path == "/":
        return await call_next(request)
    key = request.headers.get("X-RapidAPI-Key", "")
    if not key:
        return JSONResponse(status_code=401, content={"detail": "Missing X-RapidAPI-Key header"})
    return await call_next(request)
