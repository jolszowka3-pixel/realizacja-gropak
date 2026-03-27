import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
    <style>
    /* Profesjonalna stylizacja przycisków w tabeli */
    .stButton>button { width: 100%; border-radius: 2px; height: 1.9em; line-height: 1; padding: 2px; font-size: 14px; }
    .main .block-container { padding-top: 1.5rem; }
    thead tr th { background-color: #f8f9fa !important; color: #333 !important; }
    /* Stylizacja przycisku specyfikacji, żeby wyglądał bardziej jak tekst */
    div[data-testid="stPopover"] > button { 
        border: none !important; 
        background: transparent !important; 
        text-align: left !important; 
        color: #1f77b4 !important;
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGOWANIE ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "gropak2026": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Logowanie GROPAK ERP", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if not check_password():
    st.stop()

# --- 3. BAZA DANYCH ---
PLIK_DANYCH = "baza_gropak_v3.json"

def wczytaj_dane():
    if os.path.exists(PLIK_DANYCH):
        try:
            with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "w_realizacji" not in d: d["w_realizacji"] = []
                if "zrealizowane" not in d: d["zrealizowane"] = []
                if "przyjecia" not in d: d["przyjecia"] = []
                return d
        except: pass
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": []}

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    st.title("⚙️ OPERACJE")
    opcja = st.selectbox("Typ dokumentu", ["Zlecenie Produkcji", "Przyjęcie Towaru (PZ)"])
    st.divider()
    
    if opcja == "Zlecenie Produkcji":
        k_klient = st.text_input("Nazwa Klienta")
        k_kontakt = st.text_input("Telefon / Email")
        k_opis = st.text_area("Specyfikacja (np. folia 120cm/50m)")
        if st.button("Zatwierdź Zlecenie"):
            if k_klient:
                dane["w_realizacji"].append({
                    "klient": k_klient, "kontakt": k_kontakt, "opis": k_opis,
                    "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"
                })
                zapisz_dane(dane)
                st.
