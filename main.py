from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import sqlite3
from datetime import datetime

app = FastAPI()

# Autoriser GitHub Pages à accéder
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou remplace * par ton vrai domaine GitHub Pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer la base de données et la table si elle n'existe pas
def create_db():
    conn = sqlite3.connect("etf_prices.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Fonction pour ajouter un prix dans la base de données
def store_price(price):
    conn = sqlite3.connect("etf_prices.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO prices (price, timestamp) VALUES (?, ?)", (price, timestamp))
    conn.commit()
    conn.close()

# Récupérer le dernier prix de l'ETF et le stocker dans la base de données
@app.get("/etf-price")
def get_etf_price():
    ticker = yf.Ticker("ESE.PA")
    data = ticker.history(period="1d")
    
    if not data.empty:
        latest_price = data["Close"].iloc[-1]
        store_price(latest_price)  # Stocke le prix dans la base de données
        return {"price": round(float(latest_price), 2)}
    
    return {"error": "No data found"}

# Route pour récupérer les 30 derniers prix stockés
@app.get("/price-history")
def get_price_history():
    conn = sqlite3.connect("etf_prices.db")
    c = conn.cursor()
    c.execute("SELECT * FROM prices ORDER BY timestamp DESC LIMIT 30")
    rows = c.fetchall()
    conn.close()
    
    return {"history": [{"price": row[1], "timestamp": row[2]} for row in rows]}

# Initialiser la base de données
create_db()
