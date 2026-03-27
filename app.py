import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="GROPAK Online", layout="wide")

# --- 2. SYSTEM LOGOWANIA ---
def check_password():
    """Zwraca True, jeśli użytkownik podał poprawne hasło."""
    def password_entered():
        # TUTAJ MOŻESZ ZMIENIĆ HASŁO NA WŁASNE
        if st.session_state["password"] == "gropak2026": 
            st.session_state["password_correct"] = True
            del st.session_state["password"] # Usuwamy hasło z pamięci sesji dla bezpieczeństwa
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Pierwsze uruchomienie, wyświetl pole do wpisania hasła
        st.text_input("Hasło dostępu do systemu GROPAK", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Hasło błędne, wyświetl pole ponownie i błąd
        st.text_input("Hasło dostępu do systemu GROPAK", type="password", on_change=password_entered, key="password")
        st.error("❌ Błędne hasło. Spróbuj ponownie.")
        return False
    else:
        # Hasło poprawne
        return True

# ZATRZYMAJ PROGRAM, JEŚLI NIE MA LOGOWANIA
if not check_password():
    st.stop()

# --- 3. RESZTA PROGRAMU (Dostępna tylko po zalogowaniu) ---

PLIK_DANYCH = "baza_gropak.json"

def wczytaj_dane():
    if os.path.exists(PLIK_DANYCH):
        with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"w_realizacji": [], "zrealizowane": []}

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# INTERFEJS UŻYTKOWNIKA
st.title("📦 GROPAK - Panel Zarządzania")

# Sidebar - Dodawanie zamówienia
with st.sidebar:
    st.header("➕ Nowe Zamówienie")
    klient = st.text_input("Nazwa Klienta")
    kontakt = st.text_input("Kontakt (Tel/Email)")
    opis = st.text_area("Opis zamówienia")
    
    if st.button("Dodaj do systemu"):
        if klient:
            nowe = {
                "id": len(dane["w_realizacji"]) + len(dane["zrealizowane"]) + 1,
                "klient": klient,
                "kontakt": kontakt,
                "opis": opis,
                "data_p": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            dane["w_realizacji"].append(nowe)
            zapisz_dane(dane)
            st.success("Dodano!")
            st.rerun()
        else:
            st.error("Podaj nazwę klienta!")

# GŁÓWNY PANEL
tab1, tab2 = st.tabs(["🚀 W Realizacji", "✅ Historia"])

with tab1:
    if not dane["w_realizacji"]:
        st.info("Brak aktywnych zamówień.")
    else:
        # Tworzymy kopię listy do iteracji, żeby uniknąć błędów przy usuwaniu
        for i, z in enumerate(dane["w_realizacji"]):
            with st.expander(f"📌 {z['klient']} (od: {z['data_p']})"):
                st.write(f"**Kontakt:** {z['kontakt']}")
                st.write(f"**Szczegóły:** {z['opis']}")
                
                col1, col2 = st.columns(2)
                if col1.button("Oznacz jako ZREALIZOWANE", key=f"zre_{i}"):
                    z["data_koniec"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                    zapisz_dane(dane)
                    st.rerun()
                
                if col2.button("Usuń", key=f"del_{i}"):
                    dane["w_realizacji"].pop(i)
                    zapisz_dane(dane)
                    st.rerun()

with tab2:
    if not dane["zrealizowane"]:
        st.info("Historia jest pusta.")
    else:
        df = pd.DataFrame(dane["zrealizowane"])
        st.dataframe(df[["klient", "data_p", "data_koniec", "kontakt"]], use_container_width=True)