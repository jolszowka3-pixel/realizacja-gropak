import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

# --- STYLIZACJA CSS (Dla profesjonalnego wyglądu) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 2px; height: 1.8em; line-height: 1; padding: 0; }
    .main .block-container { padding-top: 2rem; }
    div[data-testid="stExpander"] { border: none; box-shadow: none; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGOWANIE ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "gropak2026": # TWOJE HASŁO
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Logowanie do systemu GROPAK", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if not check_password():
    st.stop()

# --- DANE ---
PLIK_DANYCH = "baza_gropak_v3.json"

def wczytaj_dane():
    if os.path.exists(PLIK_DANYCH):
        with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": []}

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- SIDEBAR (FORMULARZE) ---
with st.sidebar:
    st.title("⚙️ PANEL KONTROLNY")
    opcja = st.selectbox("Typ operacji", ["Nowe Zamówienie", "Przyjęcie Towaru (PZ)"])
    st.divider()
    
    if opcja == "Nowe Zamówienie":
        k_klient = st.text_input("Klient")
        k_kontakt = st.text_input("Kontakt")
        k_opis = st.text_area("Specyfikacja zamówienia")
        if st.button("Zatwierdź zamówienie"):
            if k_klient:
                dane["w_realizacji"].append({
                    "klient": k_klient, "kontakt": k_kontakt, "opis": k_opis,
                    "data_p": datetime.now().strftime("%d.%m %H:%M")
                })
                zapisz_dane(dane)
                st.rerun()
    else:
        p_dostawca = st.text_input("Dostawca")
        p_towar = st.text_input("Towar")
        p_ilosc = st.text_input("Ilość")
        if st.button("Zatwierdź PZ"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({
                    "dostawca": p_dostawca, "towar": p_towar, "ilosc": p_ilosc,
                    "data": datetime.now().strftime("%d.%m %H:%M")
                })
                zapisz_dane(dane)
                st.rerun()

# --- GŁÓWNY WIDOK ---
st.header("📊 System Zarządzania Produkcją GROPAK")

tab1, tab2, tab3 = st.tabs(["AKTUALNE ZLECENIA", "HISTORIA WYDAŃ", "REJESTR PRZYJĘĆ (PZ)"])

with tab1:
    if not dane["w_realizacji"]:
        st.write("Brak aktywnych zleceń.")
    else:
        # Nagłówki tabeli
        cols = st.columns([2, 2, 4, 2, 1, 1])
        cols[0].write("**Klient**")
        cols[1].write("**Data**")
        cols[2].write("**Szczegóły**")
        cols[3].write("**Kontakt**")
        cols[4].write("**Akcja**")
        cols[5].write("")
        st.divider()

        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([2, 2, 4, 2, 1, 1])
            c[0].write(z['klient'])
            c[1].write(z['data_p'])
            c[2].write(z['opis'])
            c[3].write(z['kontakt'])
            if c[4].button("Gotowe", key=f"z_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane)
                st.rerun()
            if c[5].button("Usuń", key=f"u_{i}"):
                dane["w_realizacji"].pop(i)
                zapisz_dane(dane)
                st.rerun()

with tab2:
    if dane["zrealizowane"]:
        df_z = pd.DataFrame(dane["zrealizowane"])
        df_z.columns = ["Klient", "Kontakt", "Opis", "Przyjęto", "Zrealizowano"]
        st.table(df_z.iloc[::-1]) # Najnowsze na górze

with tab3:
    if dane["przyjecia"]:
        df_p = pd.DataFrame(dane["przyjecia"])
        df_p.columns = ["Dostawca", "Towar", "Ilość", "Data"]
        st.table(df_p.iloc[::-1])
    else:
        st.write("Brak zarejestrowanych dostaw.")
                dane["przyjecia"] = []
                zapisz_dane(dane)
                st.rerun()
    else:
        st.info("Brak zarejestrowanych dostaw.")
