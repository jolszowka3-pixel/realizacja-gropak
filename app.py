import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

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
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-weight: bold;
        color: #1f77b4;
    }
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

# --- FUNKCJA POMOCNICZA DLA DAT ---
def formatuj_date_do_kalendarza(tekst_daty):
    """Próbuje zamienić wpisany tekst na format ISO YYYY-MM-DD"""
    teraz = datetime.now()
    try:
        # Próba formatu DD.MM.YYYY
        dt = datetime.strptime(tekst_daty, "%d.%m.%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        try:
            # Próba formatu DD.MM
            dt = datetime.strptime(tekst_daty, "%d.%m")
            return dt.replace(year=teraz.year).strftime("%Y-%m-%d")
        except:
            return None

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
                dane["w_realizacji"].append({
                    "klient": k_klient, "termin": k_termin, "opis": k_produkty,
                    "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"
                })
                zapisz_dane(dane); st.rerun()
    else:
        p_dostawca = st.text_input("Dostawca")
        p_termin = st.text_input("Termin dostawy")
        p_towar = st.text_area("Towar")
        if st.button("Zatwierdź Przyjęcie"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({
                    "dostawca": p_dostawca, "termin": p_termin, "towar": p_towar, 
                    "data_p": datetime.now().strftime("%d.%m %H:%M"), "data_k": "-"
                })
                zapisz_dane(dane); st.rerun()

# --- 5. WIDOK GŁÓWNY ---
st.header("📊 System GROPAK Online")
st.write("---")

# --- SEKCJA C: KALENDARZ (NA GÓRZE DLA WIDOCZNOŚCI) ---
st.markdown('<div class="section-header">📅 HARMONOGRAM TERMINÓW</div>', unsafe_allow_html=True)
events = []

# Dodaj wydania do kalendarza
for z in dane["w_realizacji"]:
    data_iso = formatuj_date_do_kalendarza(z.get('termin', ''))
    if data_iso:
        events.append({
            "title": f"🚀 WYDANIE: {z['klient']}",
            "start": data_iso,
            "end": data_iso,
            "color": "#1f77b4", # Niebieski
            "allDay": True
        })

# Dodaj przyjęcia do kalendarza
for p in dane["przyjecia"]:
    data_iso = formatuj_date_do_kalendarza(p.get('termin', ''))
    if data_iso:
        events.append({
            "title": f"📥 PRZYJĘCIE: {p['dostawca']}",
            "start": data_iso,
            "end": data_iso,
            "color": "#28a745", # Zielony
            "allDay": True
        })

calendar_options = {
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listWeek"},
    "initialView": "dayGridMonth",
    "locale": "pl"
}
calendar(events=events, options=calendar_options, key="erp_calendar")
st.write("")

# --- SEKCJA A: PRODUKCJA I WYDANIA ---
st.markdown('<div class="section-header">📦 ZAMÓWIENIA I REALIZACJA PRODUKCJI</div>', unsafe_allow_html=True)
tab_prod, tab_hist_prod = st.tabs(["🚀 Bieżąca Produkcja", "✅ Historia Wydań"])

with tab_prod:
    if not dane["w_realizacji"]:
        st.info("Brak aktywnych zleceń.")
    else:
        c_h = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.8])
        c_h[0].write("**Klient**"); c_h[1].write("**Termin**"); c_h[2].write("**Dodano**"); c_h[3].write("**Produkty**")
        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.8])
            c[0].write(z['klient'])
            c[1].write(f"📅 {z.get('termin', '-')}")
            c[2].write(z['data_p'])
            p_prev = (z['opis'][:60] + '...') if len(z['opis']) > 60 else z['opis']
            with c[3].popover(f"📋 {p_prev if p_prev else 'Edytuj'}"):
                nowe_p = st.text_area("Produkty", value=z['opis'], key=f"p_e_{i}")
                nowy_t = st.text_input("Termin", value=z.get('termin', '-'), key=f"t_e_{i}")
                if st.button("Zapisz", key=f"p_s_{i}"):
                    dane["w_realizacji"][i]['opis'], dane["w_realizacji"][i]['termin'] = nowe_p, nowy_t
                    zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"p_d_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane); st.rerun()
            if c[5].button("❌", key=f"p_x_{i}"):
                dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()

with tab_hist_prod:
    if dane["zrealizowane"]:
        df_v = pd.DataFrame([{ "Klient": r.get("klient", "-"), "Termin": r.get("termin", "-"), "Wydano": r.get("data_k", "-"), "Produkty": r.get("opis", "-")} for r in dane["zrealizowane"]])
        st.dataframe(df_v.iloc[::-1], use_container_width=True)

st.write("")

# --- SEKCJA B: LOGISTYKA I PRZYJĘCIA ---
st.markdown('<div class="section-header">📥 LOGISTYKA I PRZYJĘCIA TOWARU</div>', unsafe_allow_html=True)
tab_pz_plan, tab_pz_hist = st.tabs(["🚚 Zaplanowane Dostawy", "✅ Historia Przyjęć"])

with tab_pz_plan:
    if not dane["przyjecia"]:
        st.info("Brak zaplanowanych przyjęć.")
    else:
        c_h2 = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.8])
        c_h2[0].write("**Dostawca**"); c_h2[1].write("**Termin**"); c_h2[2].write("**Dodano**"); c_h2[3].write("**Towar**")
        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.8])
            c[0].write(p['dostawca'])
            c[1].write(f"📅 {p.get('termin', '-')}")
            c[2].write(p['data_p'])
            t_prev = (p['towar'][:60] + '...') if len(p['towar']) > 60 else p['towar']
            with c[3].popover(f"🚚 {t_prev if t_prev else 'Edytuj'}"):
                nowe_tow = st.text_area("Towar", value=p['towar'], key=f"pz_e_{i}")
                nowy_pz_t = st.text_input("Termin", value=p.get('termin', '-'), key=f"pz_dt_{i}")
                if st.button("Zapisz", key=f"pz_s_{i}"):
                    dane["przyjecia"][i]['towar'], dane["przyjecia"][i]['termin'] = nowe_tow, nowy_pz_t
                    zapisz_dane(dane); st.rerun()
            if c[4].button("✅", key=f"pz_o_{i}"):
                p["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["przyjecia_historia"].append(dane["przyjecia"].pop(i))
                zapisz_dane(dane); st.rerun()
            if c[5].button("❌", key=f"pz_x_{i}"):
                dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()

with tab_pz_hist:
    if dane["przyjecia_historia"]:
        df_pz_v = pd.DataFrame([{ "Dostawca": r.get("dostawca", "-"), "Termin": r.get("termin", "-"), "Odebrano": r.get("data_k", "-"), "Towar": r.get("towar", "-")} for r in dane["przyjecia_historia"]])
        st.dataframe(df_pz_v.iloc[::-1], use_container_width=True)
