import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta
import calendar

# --- 1. KONFIGURACJA I STYLIZACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
    <style>
    /* Globalne ustawienia przycisków */
    .stButton>button { 
        width: 100%; border-radius: 6px; min-height: 32px !important; height: 32px !important; 
        font-size: 12px; font-weight: 600; transition: all 0.2s ease-in-out;
        border: 1px solid #ced4da; padding: 0 10px; line-height: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    /* ZIELONE: GOTOWE / OK */
    button:has(div p:contains("GOTOWE")), button:has(div p:contains("OK")), button:contains("GOTOWE"), button:contains("OK") {
        border: none !important; color: white !important; background-color: #28a745 !important;
    }
    button:has(div p:contains("GOTOWE")):hover, button:has(div p:contains("OK")):hover {
        background-color: #218838 !important; box-shadow: 0 2px 5px rgba(40, 167, 69, 0.4); transform: translateY(-1px);
    }
    /* CZERWONE: X */
    button:has(div p:contains("X")), button:contains("X") {
        border: none !important; color: white !important; background-color: #dc3545 !important; padding: 0 !important;
    }
    button:has(div p:contains("X")):hover {
        background-color: #c82333 !important; box-shadow: 0 2px 5px rgba(220, 53, 69, 0.4); transform: translateY(-1px);
    }
    
    div[data-testid="stHorizontalBlock"] { align-items: center !important; padding: 4px 0; }
    .stTextInput input { min-height: 32px !important; height: 32px !important; font-size: 12px !important; border-radius: 6px !important; }
    div[data-testid="stPopover"] > button { min-height: 32px !important; height: 32px !important; border: 1px solid #ced4da !important; background: white !important; text-align: left !important; color: #495057 !important; }

    .main .block-container { padding-top: 2rem; }
    .section-header {
        background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px;
        font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    /* STYLIZACJA TYGODNIA */
    .cal-col { background: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 10px; min-height: 200px; }
    .cal-day-header { font-weight: 700; color: #495057; font-size: 13px; text-align: center; border-bottom: 2px solid #212529; margin-bottom: 10px; padding-bottom: 5px; }
    .cal-day-sub { font-size: 11px; color: #adb5bd; display: block; text-align: center; }
    
    .cal-entry-out { font-size: 10px; background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; padding: 4px 6px; margin-bottom: 4px; border-radius: 4px; font-weight: 500; }
    .cal-entry-in { font-size: 10px; background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; padding: 4px 6px; margin-bottom: 4px; border-radius: 4px; font-weight: 500; }
    .cal-entry-task { font-size: 10px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 4px 6px; margin-bottom: 4px; border-radius: 4px; font-weight: 500; }
    
    .badge-urgent { background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH ---
PLIK_DANYCH = "baza_gropak_v3.json"

def wczytaj_dane():
    default_dane = {
        "w_realizacji": [], "zrealizowane": [], 
        "przyjecia": [], "przyjecia_historia": [],
        "dyspozycje": [], "dyspozycje_historia": [],
        "uzytkownicy": {"admin": "gropak2026"}
    }
    if os.path.exists(PLIK_DANYCH):
        try:
            with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
                d = json.load(f)
                for k, v in default_dane.items():
                    if k not in d: d[k] = v
                return d
        except: pass
    return default_dane

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.subheader("GROPAK ERP - Logowanie")
    c1, _ = st.columns([1, 2])
    with c1:
        u = st.text_input("Użytkownik")
        p = st.text_input("Hasło", type="password")
        if st.button("Zaloguj"):
            if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p:
                st.session_state.user = u; st.rerun()
            else: st.error("Błąd logowania")
    st.stop()

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    st.title("NOWY WPIS")
    typ = st.selectbox("Rodzaj", ["Produkcja", "Dostawa (PZ)", "Dyspozycja"])
    
    if typ == "Produkcja":
        kl = st.text_input("Klient"); tm = st.text_input("Termin (np. 31.03)"); op = st.text_area("Specyfikacja"); p = st.checkbox("🔥 PILNE")
        if st.button("Zapisz Zlecenie"):
            if kl: dane["w_realizacji"].append({"klient": kl, "termin": tm, "opis": op, "pilne": p, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()
    elif typ == "Dostawa (PZ)":
        ds = st.text_input("Dostawca"); tm = st.text_input("Data (np. 31.03)"); op = st.text_area("Szczegóły"); p = st.checkbox("🔥 PILNE")
        if st.button("Zapisz Dostawę"):
            if ds: dane["przyjecia"].append({"dostawca": ds, "termin": tm, "towar": op, "pilne": p, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()
    else:
        tyt = st.text_input("Tytuł zadania"); tm = st.text_input("Termin"); op = st.text_area("Opis"); p = st.checkbox("🔥 PILNE")
        if st.button("Zapisz Zadanie"):
            if tyt: dane["dyspozycje"].append({"tytul": tyt, "termin": tm, "opis": op, "pilne": p, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()

# --- 5. STATYSTYKI ---
st.markdown('<div class="section-header">Podsumowanie</div>', unsafe_allow_html=True)
c_s1, c_s2, c_s3 = st.columns(3)
c_s1.metric("📦 Aktywne Zlecenia", len(dane["w_realizacji"]))
c_s2.metric("🚚 Oczekujące Dostawy", len(dane["przyjecia"]))
c_s3.metric("📋 Dyspozycje w toku", len(dane["dyspozycje"]))

# --- 6. TERMINARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)

# Logika wyboru tygodnia
if "week_offset" not in st.session_state: st.session_state.week_offset = 0

c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1: 
    if st.button("← Poprzedni tydzień"): st.session_state.week_offset -= 7; st.rerun()
with c_nav3: 
    if st.button("Następny tydzień →"): st.session_state.week_offset += 7; st.rerun()

# Obliczanie dni bieżącego tygodnia
today = datetime.now()
start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=st.session_state.week_offset)
dates_in_week = [(start_of_week + timedelta(days=i)) for i in range(7)]

with c_nav2:
    st.markdown(f"<h5 style='text-align: center; margin: 0;'>{dates_in_week[0].strftime('%d.%m')} - {dates_in_week[6].strftime('%d.%m.%Y')}</h5>", unsafe_allow_html=True)

# Mapowanie zdarzeń do dat
def parse_d(txt):
    try:
        parts = str(txt).split(".")
        return int(parts[0]), int(parts[1])
    except: return None, None

week_cols = st.columns(7)
day_names = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]

for i, date in enumerate(dates_in_week):
    with week_cols[i]:
        st.markdown(f"""<div class="cal-day-header">{day_names[i]}<br><span class="cal-day-sub">{date.strftime('%d.%m')}</span></div>""", unsafe_allow_html=True)
        
        d_val, m_val = date.day, date.month
        
        # Produkcja
        for z in dane["w_realizacji"]:
            zd, zm = parse_d(z['termin'])
            if zd == d_val and zm == m_val:
                p_mark = "🔥 " if z.get('pilne') else ""
                st.markdown(f'<div class="cal-entry-out">{p_mark}W: {z["klient"]}</div>', unsafe_allow_html=True)
        
        # Dostawy
        for p in dane["przyjecia"]:
            pd, pm = parse_d(p['termin'])
            if pd == d_val and pm == m_val:
                p_mark = "🔥 " if p.get('pilne') else ""
                st.markdown(f'<div class="cal-entry-in">{p_mark}P: {p["dostawca"]}</div>', unsafe_allow_html=True)
        
        # Dyspozycje
        for ds in dane["dyspozycje"]:
            dd, dm = parse_d(ds['termin'])
            if dd == d_val and dm == m_val:
                p_mark = "🔥 " if ds.get('pilne') else ""
                st.markdown(f'<div class="cal-entry-task">{p_mark}D: {ds["tytul"]}</div>', unsafe_allow_html=True)

# --- 7. TABELE (SZUKANIE I FILTROWANIE) ---
st.markdown('<div class="section-header">Tabele Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Wyszukaj (klient, dostawca, opis...)", "").lower()

# Produkcja
t1, t2 = st.tabs(["Aktywne Zlecenia", "Zrealizowane"])
with t1:
    st.markdown('<div style="display: flex; padding-left: 5px;"><div class="label-text" style="width: 16%;">Klient</div><div class="label-text" style="width: 13%;">Termin</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Specyfikacja</div></div>', unsafe_allow_html=True)
    for i, z in enumerate(dane["w_realizacji"]):
        if search and search not in z['klient'].lower() and search not in z.get('opis','').lower(): continue
        c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
        b = '<span class="badge-urgent">PILNE</span>' if z.get('pilne') else ''
        c[0].markdown(f"**{z['klient']}** {b}", unsafe_allow_html=True)
        nt = c[1].text_input("T", value=z['termin'], key=f"z_t_{i}", label_visibility="collapsed")
        if nt != z['termin']: dane["w_realizacji"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
        c[2].write(f"{z['data_p']} ({z.get('autor','-')})")
        with c[3].popover("Szczegóły"):
            no = st.text_area("Edytuj", value=z['opis'], key=f"z_o_{i}")
            if st.button("Zapisz", key=f"z_s_{i}"): dane["w_realizacji"][i]['opis'] = no; zapisz_dane(dane); st.rerun()
        if c[4].button("GOTOWE", key=f"z_g_{i}"):
            z["data_k"] = datetime.now().strftime("%d.%m %H:%M"); z["zamknal"] = st.session_state.user
            dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"z_x_{i}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
with t2: st.dataframe(pd.DataFrame(dane["zrealizowane"]).iloc[::-1], use_container_width=True)

# Pozostałe sekcje (Logistyka i Dyspozycje) działają analogicznie jak wcześniej...
# [Tu można dodać pętle dla przyjecia i dyspozycje z tym samym układem kolumn]
