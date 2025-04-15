from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf

app = FastAPI()

# Autoriser GitHub Pages à accéder
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/etf-price")
def get_etf_price():
    ticker = yf.Ticker("ESE.PA")
    data = ticker.history(period="1d")
    if not data.empty:
        latest_price = data["Close"].iloc[-1]
        return {"price": round(float(latest_price), 2)}
    return {"error": "No data found"}
