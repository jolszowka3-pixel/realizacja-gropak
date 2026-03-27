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
    .stButton>button { width: 100%; border-radius: 2px; height: 1.9em; line-height: 1; padding: 2px; font-size: 14px; }
    .main .block-container { padding-top: 1.5rem; }
    thead tr th { background-color: #f8f9fa !important; color: #333 !important; }
    div[data-testid="stPopover"] > button { 
        border: 1px solid #dcdcdc !important; 
        background: white !important; 
        text-align: left !important; 
        color: #1f77b4 !important;
    }
    .section-header {
        background-color: #f0f2f6;
        padding: 10px; border-radius: 5px; margin-bottom: 10px;
        font-weight: bold; color: #1f77b4;
    }
    .cal-day { font-weight: bold; color: #555; margin-bottom: 5px; border-bottom: 1px solid #eee; }
    .cal-entry-out { font-size: 11px; background: #e1f5fe; color: #01579b; border-left: 3px solid #03a9f4; padding: 2px; margin-bottom: 2px; border-radius: 2px; }
    .cal-entry-in { font-size: 11px; background: #e8f5e9; color: #1b5e20; border-left: 3px solid #4caf50; padding: 2px; margin-bottom: 2px; border-radius: 2px; }
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
                keys = ["w_realizacji", "zrealizowane", "przyjecia", "przyjecia_historia"]
                for k in keys:
                    if k not in d: d[k] = []
                return d
        except: pass
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": []}

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
        k_klient = st.text_input("Klient")
        k_termin = st.text_input("Termin (np. 27.03)")
        k_produkty = st.text_area("Produkty")
        if st.button("Zatwierdź Zlecenie"):
            if k_klient:
                dane["w_realizacji"].append({"klient": k_klient, "termin": k_termin, "opis": k_produkty, "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"})
                zapisz_dane(dane); st.rerun()
    else:
        p_dostawca = st.text_input("Dostawca")
        p_termin = st.text_input("Termin dostawy (np. 28.03)")
        p_towar = st.text_area("Towar")
        if st.button("Zatwierdź Przyjęcie"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({"dostawca": p_dostawca, "termin": p_termin, "towar": p_towar, "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"})
                zapisz_dane(dane); st.rerun()

# --- 5. WIDOK GŁÓWNY ---
st.header("📊 System GROPAK Online")
st.write("---")

# --- SEKCJA KALENDARZA ---
st.markdown('<div class="section-header">📅 KALENDARZ PLANOWANYCH OPERACJI</div>', unsafe_allow_html=True)

# Logika kalendarza
now = datetime.now()
rok, miesiac = now.year, now.month
cal = calendar.monthcalendar(rok, miesiac)
dni_tygodnia = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]

# Mapowanie danych do dni (szukamy formatu DD.MM)
events_map = {}
for z in dane["w_realizacji"]:
    t = z.get('termin', '')
    if "." in t:
        try:
            dzien = int(t.split(".")[0])
            if dzien not in events_map: events_map[dzien] = []
            events_map[dzien].append(f'<div class="cal-entry-out">🚀 {z["klient"]}</div>')
        except: pass

for p in dane["przyjecia"]:
    t = p.get('termin', '')
    if "." in t:
        try:
            dzien = int(t.split(".")[0])
            if dzien not in events_map: events_map[dzien] = []
            events_map[dzien].append(f'<div class="cal-entry-in">📥 {p["dostawca"]}</div>')
        except: pass

# Budowa siatki kalendarza
st.markdown(f"### {calendar.month_name[miesiac]} {rok}")
cols = st.columns(7)
for i, dt in enumerate(dni_tygodnia):
    cols[i].markdown(f"<center><b>{dt}</b></center>", unsafe_allow_html=True)

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("")
        else:
            cell_html = f'<div class="cal-day">{day}</div>'
            if day in events_map:
                cell_html += "".join(events_map[day])
            cols[i].markdown(cell_html, unsafe_allow_html=True)
st.write("---")

# --- SEKCJA A: PRODUKCJA I WYDANIA ---
st.markdown('<div class="section-header">📦 ZAMÓWIENIA I REALIZACJA PRODUKCJI</div>', unsafe_allow_html=True)
tab_p, tab_h = st.tabs(["🚀 Bieżąca Produkcja", "✅ Historia"])
with tab_p:
    if not dane["w_realizacji"]: st.info("Brak zleceń.")
    else:
        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([1.5, 1.2, 4.5, 0.8, 0.8])
            c[0].write(z['klient'])
            c[1].write(f"📅 {z.get('termin', '-')}")
            p_prev = (z['opis'][:60] + '...') if len(z['opis']) > 60 else z['opis']
            with c[2].popover(f"📋 {p_prev if p_prev else 'Edytuj'}"):
                nowe_p = st.text_area("Opis", value=z['opis'], key=f"pe_{i}")
                nowy_t = st.text_input("Termin", value=z.get('termin', '-'), key=f"te_{i}")
                if st.button("Zapisz", key=f"ps_{i}"):
                    dane["w_realizacji"][i]['opis'], dane["w_realizacji"][i]['termin'] = nowe_p, nowy_t
                    zapisz_dane(dane); st.rerun()
            if c[3].button("GOTOWE", key=f"pd_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane); st.rerun()
            if c[4].button("❌", key=f"px_{i}"):
                dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()

# --- SEKCJA B: LOGISTYKA ---
st.markdown('<div class="section-header">📥 LOGISTYKA I PRZYJĘCIA TOWARU</div>', unsafe_allow_html=True)
tab_pz, tab_pzh = st.tabs(["🚚 Zaplanowane", "✅ Historia"])
with tab_pz:
    if not dane["przyjecia"]: st.info("Brak przyjęć.")
    else:
        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([1.5, 1.2, 4.5, 0.8, 0.8])
            c[0].write(p['dostawca'])
            c[1].write(f"📅 {p.get('termin', '-')}")
            t_prev = (p['towar'][:60] + '...') if len(p['towar']) > 60 else p['towar']
            with c[2].popover(f"🚚 {t_prev if t_prev else 'Edytuj'}"):
                nowe_tow = st.text_area("Towar", value=p['towar'], key=f"pze_{i}")
                nowy_pz_t = st.text_input("Termin", value=p.get('termin', '-'), key=f"pzt_{i}")
                if st.button("Zapisz", key=f"pzs_{i}"):
                    dane["przyjecia"][i]['towar'], dane["przyjecia"][i]['termin'] = nowe_tow, nowy_pz_t
                    zapisz_dane(dane); st.rerun()
            if c[3].button("✅", key=f"pzo_{i}"):
                p["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["przyjecia_historia"].append(dane["przyjecia"].pop(i))
                zapisz_dane(dane); st.rerun()
            if c[4].button("❌", key=f"pzx_{i}"):
                dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()
