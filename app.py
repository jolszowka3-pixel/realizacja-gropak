import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import calendar

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 4px; height: 2.1em; font-size: 12px; font-weight: 500; padding: 0px; }
    div[data-testid="column"]:nth-of-type(5) button { border: 1px solid #c3e6cb !important; color: #1e7e34 !important; background-color: #f8fff9 !important; }
    div[data-testid="column"]:nth-of-type(5) button:hover { background-color: #28a745 !important; color: white !important; }
    div[data-testid="column"]:nth-of-type(6) button { border: 1px solid #f5c6cb !important; color: #bd2130 !important; background-color: #fff9f9 !important; }
    div[data-testid="column"]:nth-of-type(6) button:hover { background-color: #dc3545 !important; color: white !important; }
    .section-header { background-color: #f1f3f5; padding: 12px 15px; border-radius: 4px; margin-bottom: 10px; margin-top: 20px; font-weight: 600; color: #343a40; text-transform: uppercase; border-left: 4px solid #495057; }
    .cal-day { font-weight: 600; color: #495057; margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid #f1f3f5; }
    .cal-entry-out { font-size: 10px; background: #e9ecef; color: #0056b3; border-left: 3px solid #0056b3; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; }
    .cal-entry-in { font-size: 10px; background: #f8f9fa; color: #28a745; border-left: 3px solid #28a745; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; }
    .label-text { font-size: 11px; color: #adb5bd; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .stTextInput input { height: 2.1em !important; font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BAZA DANYCH ---
PLIK_DANYCH = "baza_gropak_v3.json"

def wczytaj_dane():
    default = {
        "w_realizacji": [], "zrealizowane": [], 
        "przyjecia": [], "przyjecia_historia": [],
        "uzytkownicy": {"admin": "gropak2026"} # Domyślny admin
    }
    if os.path.exists(PLIK_DANYCH):
        try:
            with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
                d = json.load(f)
                for k, v in default.items():
                    if k not in d: d[k] = v
                return d
        except: pass
    return default

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state:
    st.session_state.user = None

def login_form():
    st.markdown("### Logowanie do GROPAK ERP")
    col_l, _ = st.columns([1, 2])
    with col_l:
        u = st.text_input("Użytkownik")
        p = st.text_input("Hasło", type="password")
        if st.button("Zaloguj"):
            if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p:
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Błędny login lub hasło")
    st.stop()

if not st.session_state.user:
    login_form()

# --- 4. PANEL BOCZNY (Z wylogowaniem i adminem) ---
with st.sidebar:
    st.write(f"Zalogowany jako: **{st.session_state.user}**")
    if st.button("Wyloguj"):
        st.session_state.user = None
        st.rerun()
    st.divider()
    
    # Zarządzanie użytkownikami (tylko dla admina)
    if st.session_state.user == "admin":
        with st.expander("Zarządzanie użytkownikami"):
            nowy_u = st.text_input("Nowy login")
            nowe_h = st.text_input("Nowe hasło")
            if st.button("Dodaj użytkownika"):
                if nowy_u:
                    dane["uzytkownicy"][nowy_u] = nowe_h
                    zapisz_dane(dane)
                    st.success(f"Dodano: {nowy_u}")
            st.write("Lista kont:")
            for usr in list(dane["uzytkownicy"].keys()):
                if usr != "admin":
                    if st.button(f"Usuń {usr}", key=f"del_{usr}"):
                        del dane["uzytkownicy"][usr]
                        zapisz_dane(dane)
                        st.rerun()
    st.divider()
    
    st.title("OPERACJE")
    opcja = st.selectbox("Typ dokumentu", ["Zlecenie Produkcji", "Przyjęcie Towaru (PZ)"])
    if opcja == "Zlecenie Produkcji":
        k_klient = st.text_input("Klient")
        k_termin = st.text_input("Termin (np. 27.03)")
        k_produkty = st.text_area("Specyfikacja")
        if st.button("Zapisz Zlecenie"):
            if k_klient:
                dane["w_realizacji"].append({"klient": k_klient, "termin": k_termin, "opis": k_produkty, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()
    else:
        p_dostawca = st.text_input("Dostawca")
        p_termin = st.text_input("Data dostawy (np. 28.03)")
        p_towar = st.text_area("Szczegóły")
        if st.button("Zapisz Przyjęcie"):
            if p_dostawca:
                dane["przyjecia"].append({"dostawca": p_dostawca, "termin": p_termin, "towar": p_towar, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()

# --- 5. RESZTA KODU (Kalendarz i Tabele) ---
# [Tutaj wklejamy całą logikę kalendarza i tabel z poprzedniej wersji - bez zmian]
# Poniżej skrócona wersja logiki wyświetlania dla przykładu:

st.subheader("System Zarządzania GROPAK ERP")

# KALENDARZ (Skrócony opis nawigacji)
if "cal_month" not in st.session_state: st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state: st.session_state.cal_year = datetime.now().year

def zmien_miesiac(delta):
    st.session_state.cal_month += delta
    if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
    elif st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1

def parse_date(txt):
    try:
        parts = str(txt).split(".")
        d, m = int(parts[0]), int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else st.session_state.cal_year
        return d, m, y
    except: return None, None, None

st.markdown('<div class="section-header">Harmonogram Realizacji</div>', unsafe_allow_html=True)
c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1: 
    if st.button("Poprzedni"): zmien_miesiac(-1); st.rerun()
with c_nav2:
    m_names = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    st.markdown(f"<h5 style='text-align: center;'>{m_names[st.session_state.cal_month-1]} {st.session_state.cal_year}</h5>", unsafe_allow_html=True)
with c_nav3: 
    if st.button("Następny"): zmien_miesiac(1); st.rerun()

# Logika kalendarza i wyświetlania sekcji produkcji/logistyki (identyczna jak w Twoim "ideolo" kodzie)
# Pamiętaj, aby przy wyświetlaniu tabel zachować kolumny c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])

# --- SEKCJA PRODUKCJI (Przykład wiersza z edycją inline) ---
st.markdown('<div class="section-header">Zlecenia Produkcyjne</div>', unsafe_allow_html=True)
t_prod1, t_prod2 = st.tabs(["W realizacji", "Zrealizowane"])

with t_prod1:
    if not dane["w_realizacji"]: st.info("Brak aktywnych zleceń.")
    else:
        st.markdown('<div style="display: flex;"><div class="label-text" style="width: 16%;">Klient</div><div class="label-text" style="width: 14%;">Termin (edytuj)</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Specyfikacja</div></div>', unsafe_allow_html=True)
        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].write(f"**{z['klient']}**")
            new_term = c[1].text_input("T", value=z.get('termin', '-'), key=f"t_z_{i}", label_visibility="collapsed")
            if new_term != z.get('termin'):
                dane["w_realizacji"][i]['termin'] = new_term
                zapisz_dane(dane); st.rerun()
            c[2].write(f"{z.get('data_p', '-')} ({z.get('autor', '?')})")
            with c[3].popover(f"{z['opis'][:60]}..."):
                n_p = st.text_area("Specyfikacja", value=z['opis'], key=f"pe_{i}")
                if st.button("Zapisz", key=f"ps_{i}"):
                    dane["w_realizacji"][i]['opis'] = n_p
                    zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"pd_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                z["zamknal"] = st.session_state.user
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"px_{i}"):
                dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()

# [Dalsza część kodu dla Przyjęć analogicznie jak wyżej...]
