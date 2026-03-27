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

# --- 4. NAWIGACJA KALENDARZA ---
if "cal_month" not in st.session_state:
    st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state:
    st.session_state.cal_year = datetime.now().year

def zmien_miesiac(delta):
    new_month = st.session_state.cal_month + delta
    if new_month > 12:
        st.session_state.cal_month = 1
        st.session_state.cal_year += 1
    elif new_month < 1:
        st.session_state.cal_month = 12
        st.session_state.cal_year -= 1
    else:
        st.session_state.cal_month = new_month

# --- 5. PANEL BOCZNY ---
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
        p_termin = st.text_input("Termin dostawy")
        p_towar = st.text_area("Towar")
        if st.button("Zatwierdź Przyjęcie"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({"dostawca": p_dostawca, "termin": p_termin, "towar": p_towar, "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"})
                zapisz_dane(dane); st.rerun()

# --- 6. WIDOK GŁÓWNY ---
st.header("📊 System GROPAK Online")
st.write("---")

# --- SEKCJA KALENDARZA ---
st.markdown('<div class="section-header">📅 KALENDARZ PLANOWANYCH OPERACJI</div>', unsafe_allow_html=True)

col_prev, col_title, col_next = st.columns([1, 3, 1])
with col_prev:
    if st.button("◀ Poprzedni", key="prev_btn"): zmien_miesiac(-1); st.rerun()
with col_title:
    m_names = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    st.markdown(f"<h3 style='text-align: center;'>{m_names[st.session_state.cal_month-1]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
with col_next:
    if st.button("Następny ▶", key="next_btn"): zmien_miesiac(1); st.rerun()

# Logika mapowania zdarzeń
events_map = {}
def parse_date(txt):
    try:
        parts = txt.split(".")
        d = int(parts[0])
        m = int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else st.session_state.cal_year
        return d, m, y
    except: return None, None, None

for z in dane["w_realizacji"]:
    d, m, y = parse_date(z.get('termin', ''))
    if d and m == st.session_state.cal_month and y == st.session_state.cal_year:
        if d not in events_map: events_map[d] = []
        events_map[d].append(f'<div class="cal-entry-out">🚀 {z["klient"]}</div>')

for p in dane["przyjecia"]:
    d, m, y = parse_date(p.get('termin', ''))
    if d and m == st.session_state.cal_month and y == st.session_state.cal_year:
        if d not in events_map: events_map[d] = []
        events_map[d].append(f'<div class="cal-entry-in">📥 {p["dostawca"]}</div>')

# Rysowanie siatki
dni_tyg = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]
h_cols = st.columns(7)
for i, d_name in enumerate(dni_tyg): h_cols[i].markdown(f"<center><b>{d_name}</b></center>", unsafe_allow_html=True)

month_days = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
for week in month_days:
    w_cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0: w_cols[i].write("")
        else:
            html = f'<div class="cal-day">{day}</div>'
            if day in events_map: html += "".join(events_map[day])
            w_cols[i].markdown(html, unsafe_allow_html=True)

st.write("---")

# --- SEKCJA A: PRODUKCJA ---
st.markdown('<div class="section-header">📦 ZAMÓWIENIA I REALIZACJA PRODUKCJI</div>', unsafe_allow_html=True)
t1, t2 = st.tabs(["🚀 Bieżąca Produkcja", "✅ Historia"])

with t1:
    if not dane["w_realizacji"]: st.info("Brak zleceń.")
    else:
        st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.8]) # Nagłówki wizualne
        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.8])
            c[0].write(z['klient'])
            c[1].write(f"📅 {z.get('termin', '-')}")
            c[2].write(z['data_p'])
            with c[3].popover(f"📋 {z['opis'][:50]}..."):
                n_p = st.text_area("Produkty", value=z['opis'], key=f"pe_{i}")
                n_t = st.text_input("Termin", value=z.get('termin', '-'), key=f"te_{i}")
                if st.button("Zapisz", key=f"ps_{i}"):
                    dane["w_realizacji"][i]['opis'], dane["w_realizacji"][i]['termin'] = n_p, n_t
                    zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"pd_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane); st.rerun()
            if c[5].button("❌", key=f"px_{i}"):
                dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()

# --- SEKCJA B: LOGISTYKA ---
st.markdown('<div class="section-header">📥 LOGISTYKA I PRZYJĘCIA TOWARU</div>', unsafe_allow_html=True)
t3, t4 = st.tabs(["🚚 Zaplanowane", "✅ Historia"])

with t3:
    if not dane["przyjecia"]: st.info("Brak dostaw.")
    else:
        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.8])
            c[0].write(p['dostawca'])
            c[1].write(f"📅 {p.get('termin', '-')}")
            c[2].write(p['data_p'])
            with c[3].popover(f"🚚 {p['towar'][:50]}..."):
                n_tw = st.text_area("Towar", value=p['towar'], key=f"pze_{i}")
                n_pt = st.text_input("Termin", value=p.get('termin', '-'), key=f"pzt_{i}")
                if st.button("Zapisz", key=f"pzs_{i}"):
                    dane["przyjecia"][i]['towar'], dane["przyjecia"][i]['termin'] = n_tw, n_pt
                    zapisz_dane(dane); st.rerun()
            if c[4].button("✅", key=f"pzo_{i}"):
                p["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["przyjecia_historia"].append(dane["przyjecia"].pop(i))
                zapisz_dane(dane); st.rerun()
            if c[5].button("❌", key=f"pzx_{i}"):
                dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()

# --- HISTORIE (Uproszczone) ---
with t2:
    if dane["zrealizowane"]:
        df1 = pd.DataFrame([{"Klient": r.get("klient"), "Wydano": r.get("data_k"), "Produkty": r.get("opis")} for r in dane["zrealizowane"]])
        st.dataframe(df1.iloc[::-1], use_container_width=True)
with t4:
    if dane["przyjecia_historia"]:
        df2 = pd.DataFrame([{"Dostawca": r.get("dostawca"), "Odebrano": r.get("data_k"), "Towar": r.get("towar")} for r in dane["przyjecia_historia"]])
        st.dataframe(df2.iloc[::-1], use_container_width=True)
