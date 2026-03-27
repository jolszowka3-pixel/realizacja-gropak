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
    
    /* Zielone przyciski akcji */
    div[data-testid="column"]:nth-of-type(5) button {
        border: 1px solid #c3e6cb !important;
        color: #1e7e34 !important;
        background-color: #f8fff9 !important;
    }
    div[data-testid="column"]:nth-of-type(5) button:hover {
        background-color: #28a745 !important;
        color: white !important;
    }
    
    /* Czerwone przyciski usuwania */
    div[data-testid="column"]:nth-of-type(6) button {
        border: 1px solid #f5c6cb !important;
        color: #bd2130 !important;
        background-color: #fff9f9 !important;
    }
    div[data-testid="column"]:nth-of-type(6) button:hover {
        background-color: #dc3545 !important;
        color: white !important;
    }

    .main .block-container { padding-top: 2rem; }
    .section-header {
        background-color: #f1f3f5;
        padding: 12px 15px;
        border-radius: 4px;
        margin-bottom: 15px;
        font-weight: 600;
        color: #343a40;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-left: 4px solid #495057;
    }
    .cal-day { font-weight: 600; color: #495057; margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid #f1f3f5; }
    .cal-entry-out { font-size: 10px; background: #e9ecef; color: #0056b3; border-left: 3px solid #0056b3; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; font-weight: 500; }
    .cal-entry-in { font-size: 10px; background: #f8f9fa; color: #28a745; border-left: 3px solid #28a745; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; font-weight: 500; }
    div[data-testid="stPopover"] > button { border: 1px solid #dee2e6 !important; background: white !important; text-align: left !important; color: #495057 !important; font-size: 13px !important; height: 2.1em !important; }
    .label-text { font-size: 12px; color: #6c757d; font-weight: 600; margin-bottom: 2px; }
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
        st.text_input("Logowanie do systemu", type="password", on_change=password_entered, key="password")
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
                for k in ["w_realizacji", "zrealizowane", "przyjecia", "przyjecia_historia"]:
                    if k not in d: d[k] = []
                return d
        except: pass
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": []}

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- 4. NAWIGACJA I DATY ---
if "cal_month" not in st.session_state: st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state: st.session_state.cal_year = datetime.now().year

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

def parse_date(txt):
    try:
        parts = txt.split(".")
        d = int(parts[0]); m = int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else st.session_state.cal_year
        return d, m, y
    except: return None, None, None

# --- 5. PANEL BOCZNY ---
with st.sidebar:
    st.title("OPERACJE")
    opcja = st.selectbox("Typ dokumentu", ["Zlecenie Produkcji", "Przyjęcie Towaru (PZ)"])
    st.divider()
    if opcja == "Zlecenie Produkcji":
        k_klient = st.text_input("Klient")
        k_termin = st.text_input("Termin (np. 27.03)")
        k_produkty = st.text_area("Specyfikacja")
        if st.button("Zapisz Zlecenie"):
            if k_klient:
                dane["w_realizacji"].append({"klient": k_klient, "termin": k_termin, "opis": k_produkty, "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"})
                zapisz_dane(dane); st.rerun()
    else:
        p_dostawca = st.text_input("Dostawca")
        p_termin = st.text_input("Data dostawy (np. 28.03)")
        p_towar = st.text_area("Szczegóły")
        if st.button("Zapisz Przyjęcie"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({"dostawca": p_dostawca, "termin": p_termin, "towar": p_towar, "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"})
                zapisz_dane(dane); st.rerun()

# --- 6. WIDOK GŁÓWNY ---
st.subheader("Panel Zarządzania GROPAK ERP")
st.write("---")

# --- KALENDARZ ---
st.markdown('<div class="section-header">Harmonogram Realizacji</div>', unsafe_allow_html=True)
c_prev, c_title, c_next = st.columns([1, 4, 1])
with c_prev:
    if st.button("Poprzedni", key="p_btn"): zmien_miesiac(-1); st.rerun()
with c_title:
    m_names = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    st.markdown(f"<h4 style='text-align: center; margin: 0;'>{m_names[st.session_state.cal_month-1]} {st.session_state.cal_year}</h4>", unsafe_allow_html=True)
with c_next:
    if st.button("Następny", key="n_btn"): zmien_miesiac(1); st.rerun()

events_map = {}
for z in dane["w_realizacji"]:
    d, m, y = parse_date(z.get('termin', ''))
    if d and m == st.session_state.cal_month and y == st.session_state.cal_year:
        if d not in events_map: events_map[d] = []
        events_map[d].append(f'<div class="cal-entry-out">W: {z["klient"]}</div>')
for p in dane["przyjecia"]:
    d, m, y = parse_date(p.get('termin', ''))
    if d and m == st.session_state.cal_month and y == st.session_state.cal_year:
        if d not in events_map: events_map[d] = []
        events_map[d].append(f'<div class="cal-entry-in">P: {p["dostawca"]}</div>')

h_cols = st.columns(7)
for i, d_n in enumerate(["PON", "WT", "ŚR", "CZW", "PT", "SOB", "NDZ"]): h_cols[i].markdown(f"<p style='text-align:center; font-size: 11px; color: #adb5bd; margin-bottom: 5px;'>{d_n}</p>", unsafe_allow_html=True)

month_days = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
for week in month_days:
    w_cols = st.columns(7)
    for i, day in enumerate(week):
        if day != 0:
            html = f'<div class="cal-day">{day}</div>'
            if day in events_map: html += "".join(events_map[day])
            w_cols[i].markdown(html, unsafe_allow_html=True)

st.write("---")

# --- PRODUKCJA ---
st.markdown('<div class="section-header">Zlecenia Produkcyjne</div>', unsafe_allow_html=True)
st.markdown('<div style="display: flex; margin-bottom: 5px;"><div class="label-text" style="width: 15.5%;">Klient</div><div class="label-text" style="width: 12.5%;">Termin</div><div class="label-text" style="width: 12.5%;">Dodano</div><div class="label-text" style="width: 45%;">Specyfikacja</div></div>', unsafe_allow_html=True)

if not dane["w_realizacji"]: st.info("Brak aktywnych zleceń.")
else:
    for i, z in enumerate(dane["w_realizacji"]):
        c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
        c[0].write(f"**{z['klient']}**"); c[1].write(z.get('termin', '-')); c[2].write(z.get('data_p', '-'))
        with c[3].popover(f"{z['opis'][:50]}..."):
            n_p = st.text_area("Specyfikacja", value=z['opis'], key=f"pe_{i}")
            n_t = st.text_input("Termin", value=z.get('termin', '-'), key=f"te_{i}")
            if st.button("Zaktualizuj", key=f"ps_{i}"):
                dane["w_realizacji"][i]['opis'], dane["w_realizacji"][i]['termin'] = n_p, n_t
                zapisz_dane(dane); st.rerun()
        if c[4].button("ZAMKNIJ", key=f"pd_{i}"):
            z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
            dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
            zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"px_{i}"):
            dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()

st.write("")

# --- LOGISTYKA ---
st.markdown('<div class="section-header">Przyjęcia Towaru</div>', unsafe_allow_html=True)
st.markdown('<div style="display: flex; margin-bottom: 5px;"><div class="label-text" style="width: 15.5%;">Dostawca</div><div class="label-text" style="width: 12.5%;">Termin</div><div class="label-text" style="width: 12.5%;">Dodano</div><div class="label-text" style="width: 45%;">Opis Dostawy</div></div>', unsafe_allow_html=True)

if not dane["przyjecia"]: st.info("Brak zaplanowanych przyjęć.")
else:
    for i, p in enumerate(dane["przyjecia"]):
        c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
        c[0].write(f"**{p['dostawca']}**"); c[1].write(p.get('termin', '-')); c[2].write(p.get('data_p', '-'))
        with c[3].popover(f"{p['towar'][:50]}..."):
            n_tw = st.text_area("Towar", value=p['towar'], key=f"pze_{i}")
            n_pt = st.text_input("Termin", value=p.get('termin', '-'), key=f"pzt_{i}")
            if st.button("Zaktualizuj", key=f"pzs_{i}"):
                dane["przyjecia"][i]['towar'], dane["przyjecia"][i]['termin'] = n_tw, n_pt
                zapisz_dane(dane); st.rerun()
        if c[4].button("ODEBRANO", key=f"pzo_{i}"):
            p["data_k"] = datetime.now().strftime("%d.%m %H:%M")
            dane["przyjecia_historia"].append(dane["przyjecia"].pop(i))
            zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"pzx_{i}"):
            dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()

# --- ARCHIWUM ---
st.write("---")
if st.checkbox("Pokaż historię zakończonych operacji"):
    t_h1, t_h2 = st.tabs(["Historia Wydań", "Historia Przyjęć"])
    with t_h1:
        if dane["zrealizowane"]: st.dataframe(pd.DataFrame(dane["zrealizowane"]).iloc[::-1], use_container_width=True)
    with t_h2:
        if dane["przyjecia_historia"]: st.dataframe(pd.DataFrame(dane["przyjecia_historia"]).iloc[::-1], use_container_width=True)
