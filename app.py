import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

# Stylizacja dla lepszej czytelności tabeli
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 2px; height: 1.8em; line-height: 1; padding: 0; }
    .main .block-container { padding-top: 1.5rem; }
    thead tr th { background-color: #f0f2f6 !important; }
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
                return json.load(f)
        except:
            pass
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": []}

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()
# Zapewnienie kompatybilności struktur
if "przyjecia" not in dane: dane["przyjecia"] = []

# --- 4. PANEL BOCZNY (WPISYWANIE) ---
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
                    "data_p": datetime.now().strftime("%d.%m %H:%M")
                })
                zapisz_dane(dane)
                st.rerun()
    else:
        p_dostawca = st.text_input("Dostawca")
        p_towar = st.text_input("Towar / Surowiec")
        p_ilosc = st.text_input("Ilość (kg/szt)")
        if st.button("Zatwierdź Przyjęcie"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({
                    "dostawca": p_dostawca, "towar": p_towar, "ilosc": p_ilosc,
                    "data": datetime.now().strftime("%d.%m %H:%M")
                })
                zapisz_dane(dane)
                st.rerun()

# --- 5. WIDOK GŁÓWNY ---
st.header("📊 System GROPAK Online")

tab1, tab2, tab3 = st.tabs(["🚀 PRODUKCJA", "✅ WYDANIA", "📥 PRZYJĘCIA (PZ)"])

with tab1:
    if not dane["w_realizacji"]:
        st.info("Brak aktywnych zleceń produkcyjnych.")
    else:
        # Tabela aktywnych zleceń
        col_h = st.columns([2, 2, 4, 2, 1, 1])
        col_h[0].write("**Klient**")
        col_h[1].write("**Data Przyjęcia**")
        col_h[2].write("**Specyfikacja**")
        col_h[3].write("**Kontakt**")
        col_h[4].write("**Status**")
        st.divider()

        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([2, 2, 4, 2, 1, 1])
            c[0].write(z['klient'])
            c[1].write(z['data_p'])
            c[2].write(z['opis'])
            c[3].write(z['kontakt'])
            if c[4].button("GOTOWE", key=f"z_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane)
                st.rerun()
            if c[5].button("USUŃ", key=f"u_{i}"):
                dane["w_realizacji"].pop(i)
                zapisz_dane(dane)
                st.rerun()
