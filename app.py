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
    .cal-day { font-weight: bold; color: #555; margin-bottom: 5px; border-bottom: 1px solid #eee; min-height: 25px; }
    .cal-entry-out { font-size: 10px; background: #e1f5fe; color: #01579b; border-left: 3px solid #03a9f4; padding: 2px; margin-bottom: 2px; border-radius: 2px; line-height: 1.1; }
    .cal-entry-in { font-size: 10px; background: #e8f5e9; color: #1b5e20; border-left: 3px solid #4caf50; padding: 2px; margin-bottom: 2px; border-radius: 2px; line-height: 1.1; }
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

# --- 4. ZARZĄDZANIE DATĄ KALENDARZA ---
if "cal_month" not in st.session_state:
    st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state:
    st.session_state.cal_year = datetime.now().year

def zmien_miesiac(kierunek):
    if kierunek == "nast":
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
    else:
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1

# --- 5. PANEL BOCZNY ---
with st.sidebar:
    st.title("⚙️ OPERACJE")
    opcja = st.selectbox("Typ dokumentu", ["Zlecenie Produkcji", "Przyjęcie Towaru (PZ)"])
    st.divider()
    
    if opcja == "Zlecenie Produkcji":
        k_klient = st.text_input("Klient")
        k_termin = st.text_input("Termin (np. 27.03 lub 27.03.2026)")
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

# --- 6. WIDOK GŁÓWNY ---
st.header("📊 System GROPAK Online")
st.write("---")

# --- SEKCJA KALENDARZA Z NAWIGACJĄ ---
st.markdown('<div class="section-header">📅 KALENDARZ PLANOWANYCH OPERACJI</div>', unsafe_allow_html=True)

# Nagłówek kalendarza z przyciskami
c1, c2, c3 = st.columns([1, 3, 1])
with c1:
    if st.button("◀ Poprzedni"): 
        zmien_miesiac("poprz"); st.rerun()
with c2:
    miesiace_pl = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    st.markdown(f"<h3 style='text-align: center;'>{miesiace_pl[st.session_state.cal_month-1]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
with c3:
    if st.button("Następny ▶"): 
        zmien_miesiac("nast"); st.rerun()

# Logika kalendarza
rok_cal = st.session_state.cal_year
mies_cal = st.session_state.cal_month
cal_grid = calendar.monthcalendar(rok_cal, mies_cal)
dni_tygodnia = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]

# Mapowanie danych do dni (obsługa terminów DD.MM lub DD.MM.YYYY)
events_map = {}

def wyciagnij_date(tekst_daty):
    try:
        if not tekst_daty or "." not in tekst_daty: return None, None
        czesci = tekst_daty.split(".")
        d = int(czesci[0])
        m = int(czesci[1])
        y = int(czesci[2]) if len(czesci) > 2 else rok_cal # Jeśli brak roku, przyjmij aktualny rok kalendarza
        return d, m, y
    except: return None, None

for z in dane["w_realizacji"]:
    d, m, y = wyciagnij_date(z.get('termin', ''))
    if d and m == mies_cal and y == rok_cal:
        if d not in events_map: events_map[d] = []
        events_map[d].append(f'<div class="cal-entry-out">🚀 {z["klient"]}</div>')

for p in dane["przyjecia"]:
    d, m, y = wyciagnij_date(p.get('termin', ''))
    if d and m == mies_cal and y == rok_cal:
        if d not in events_map: events_map[d] = []
        events_map[d].append(f'<div class="cal-entry-in">📥 {p["dostawca"]}</div>')

# Wyświetlanie siatki
cols_header = st.columns(7)
for i, dt in enumerate(dni_tygodnia):
    cols_header[i].markdown(f"<center><b>{dt}</b></center>", unsafe_allow_html=True)

for week in cal_grid:
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
