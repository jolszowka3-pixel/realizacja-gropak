import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="GROPAK - System Zarządzania", layout="wide")

# --- 2. SYSTEM LOGOWANIA ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "gropak2026": # TWOJE HASŁO
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Hasło dostępu", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Hasło dostępu", type="password", on_change=password_entered, key="password")
        st.error("❌ Błędne hasło")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 3. BAZA DANYCH ---
PLIK_DANYCH = "baza_gropak_v2.json"

def wczytaj_dane():
    if os.path.exists(PLIK_DANYCH):
        with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
            return json.load(f)
    # Dodajemy nową listę "przyjecia"
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": []}

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()
if "przyjecia" not in dane: dane["przyjecia"] = [] # Naprawa dla starych plików

# --- 4. INTERFEJS ---
st.title("📦 GROPAK - System Zarządzania")

# SIDEBAR - Wybór co dodajemy
menu = st.sidebar.radio("Co chcesz zrobić?", ["Dodaj Zamówienie Klienta", "Dodaj Przyjęcie Towaru (PZ)"])

if menu == "Dodaj Zamówienie Klienta":
    with st.sidebar:
        st.subheader("➕ Nowe Zamówienie")
        klient = st.text_input("Nazwa Klienta")
        kontakt = st.text_input("Kontakt")
        opis = st.text_area("Opis (co produkujemy?)")
        if st.button("Dodaj do Realizacji"):
            if klient:
                dane["w_realizacji"].append({
                    "klient": klient, "kontakt": kontakt, "opis": opis,
                    "data_p": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                zapisz_dane(dane)
                st.success("Dodano zamówienie!")
                st.rerun()

elif menu == "Dodaj Przyjęcie Towaru (PZ)":
    with st.sidebar:
        st.subheader("🚛 Nowe Przyjęcie (PZ)")
        dostawca = st.text_input("Nazwa Dostawcy")
        towar = st.text_input("Co przyjechało? (np. Granulat)")
        ilosc = st.text_input("Ilość/Waga")
        if st.button("Zapisz Przyjęcie"):
            if dostawca and towar:
                dane["przyjecia"].append({
                    "dostawca": dostawca, "towar": towar, "ilosc": ilosc,
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                zapisz_dane(dane)
                st.success("Zapisano dostawę!")
                st.rerun()

# --- GŁÓWNY PANEL ---
tab1, tab2, tab3 = st.tabs(["🚀 Produkcja (W Realizacji)", "✅ Historia Sprzedaży", "📥 Magazyn - Przyjęcia"])

with tab1:
    for i, z in enumerate(dane["w_realizacji"]):
        with st.expander(f"📌 {z['klient']} ({z['data_p']})"):
            st.write(f"**Kontakt:** {z['kontakt']}")
            st.write(f"**Opis:** {z['opis']}")
            if st.button("ZREALIZOWANE", key=f"zre_{i}"):
                z["data_koniec"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane)
                st.rerun()

with tab2:
    if dane["zrealizowane"]:
        st.dataframe(pd.DataFrame(dane["zrealizowane"]), use_container_width=True)

with tab3:
    st.subheader("Lista ostatnich dostaw (PZ)")
    if dane["przyjecia"]:
        # Wyświetlamy tabelę od najnowszych dostaw
        df_pz = pd.DataFrame(dane["przyjecia"]).iloc[::-1]
        st.table(df_pz)
        if st.button("Wyczyść historię przyjęć"):
            if st.checkbox("Potwierdzam usunięcie wszystkich wpisów PZ"):
                dane["przyjecia"] = []
                zapisz_dane(dane)
                st.rerun()
    else:
        st.info("Brak zarejestrowanych dostaw.")
