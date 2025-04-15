from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import sqlite3
from datetime import datetime
import threading
import time

app = FastAPI()

# Autoriser GitHub Pages à accéder
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Remplace * par ton vrai domaine GitHub Pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer la base de données et la table si elle n'existe pas
def create_db():
    try:
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
    except sqlite3.Error as e:
        print(f"Erreur lors de la création de la base de données : {e}")
    finally:
        conn.close()

# Fonction pour ajouter un prix dans la base de données
def store_price(price):
    try:
        conn = sqlite3.connect("etf_prices.db")
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO prices (price, timestamp) VALUES (?, ?)", (price, timestamp))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erreur lors de l'ajout du prix à la base de données : {e}")
    finally:
        conn.close()

# Récupérer le dernier prix de l'ETF et le stocker dans la base de données
@app.get("/etf-price")
async def get_etf_price(background_tasks: BackgroundTasks):
    try:
        ticker = yf.Ticker("ESE.PA")
        data = ticker.history(period="1d")

        if not data.empty:
            latest_price = data["Close"].iloc[-1]
            store_price(latest_price)  # Stocke le prix dans la base de données
            background_tasks.add_task(fetch_price_every_5_minutes)  # Ajouter une tâche d'arrière-plan
            return {"price": round(float(latest_price), 2)}
        
        return {"error": "No data found"}
    except Exception as e:
        return {"error": f"Erreur lors de la récupération du prix : {e}"}

# Route pour récupérer les 30 derniers prix stockés
@app.get("/price-history")
def get_price_history():
    try:
        conn = sqlite3.connect("etf_prices.db")
        c = conn.cursor()
        c.execute("SELECT * FROM prices ORDER BY timestamp DESC LIMIT 30")
        rows = c.fetchall()
        conn.close()
        
        return {"history": [{"price": row[1], "timestamp": row[2]} for row in rows]}
    except sqlite3.Error as e:
        return {"error": f"Erreur lors de la récupération de l'historique : {e}"}

# Tâche de fond : récupérer et stocker un prix toutes les 5 minutes
def fetch_price_every_5_minutes():
    while True:
        try:
            ticker = yf.Ticker("ESE.PA")
            data = ticker.history(period="1d")
            if not data.empty:
                latest_price = data["Close"].iloc[-1]
                store_price(latest_price)
                print(f"[{datetime.now()}] Prix stocké automatiquement : {latest_price}")
            else:
                print(f"[{datetime.now()}] Aucun prix trouvé")
        except Exception as e:
            print(f"[{datetime.now()}] Erreur lors de la récupération automatique : {e}")
        time.sleep(5 * 60)  # Récupérer le prix toutes les 5 minutes

# Initialiser la base de données
create_db()

# Démarrer la tâche de fond automatique
threading.Thread(target=fetch_price_every_5_minutes, daemon=True).start()

