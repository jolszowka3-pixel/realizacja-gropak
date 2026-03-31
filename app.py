import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import calendar

# --- 1. KONFIGURACJA I STYLIZACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
    <style>
    /* Globalne ustawienia przycisków */
    .stButton>button { 
        width: 100%; 
        border-radius: 6px; 
        min-height: 32px !important;
        height: 32px !important; 
        font-size: 12px; 
        font-weight: 600; 
        transition: all 0.2s ease-in-out;
        border: 1px solid #ced4da;
        padding: 0 10px;
        line-height: 1;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    /* ZIELONE: GOTOWE / OK (Pełny kolor) */
    button:has(div p:contains("GOTOWE")), 
    button:has(div p:contains("OK")),
    button:contains("GOTOWE"),
    button:contains("OK") {
        border: none !important;
        color: white !important;
        background-color: #28a745 !important;
    }
    button:has(div p:contains("GOTOWE")):hover, 
    button:has(div p:contains("OK")):hover,
    button:contains("GOTOWE"):hover,
    button:contains("OK"):hover {
        background-color: #218838 !important;
        box-shadow: 0 2px 5px rgba(40, 167, 69, 0.4);
        transform: translateY(-1px);
    }

    /* CZERWONE: X (Usuwanie - pełny kolor) */
    button:has(div p:contains("X")),
    button:contains("X") {
        border: none !important;
        color: white !important;
        background-color: #dc3545 !important;
        padding: 0 !important;
    }
    button:has(div p:contains("X")):hover,
    button:contains("X"):hover {
        background-color: #c82333 !important;
        box-shadow: 0 2px 5px rgba(220, 53, 69, 0.4);
        transform: translateY(-1px);
    }

    /* Wyśrodkowanie elementów w wierszach tabeli i redukcja luzów */
    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        padding: 4px 0;
    }

    /* Unifikacja wysokości inputów, żeby idealnie pasowały do przycisków */
    .stTextInput input { 
        min-height: 32px !important;
        height: 32px !important; 
        font-size: 12px !important; 
        border-radius: 6px !important;
    }
    
    /* Popover (przycisk rozwijający) też musi trzymać wymiar */
    div[data-testid="stPopover"] > button { 
        min-height: 32px !important;
        height: 32px !important;
        border: 1px solid #ced4da !important; 
        background: white !important; 
        text-align: left !important; 
        color: #495057 !important; 
    }

    .main .block-container { padding-top: 2rem; }
    .section-header {
        background-color: #f8f9fa;
        padding: 12px 15px;
        border-radius: 6px;
        margin-bottom: 12px;
        margin-top: 25px;
        font-weight: 700;
        color: #212529;
        text-transform: uppercase;
        border-left: 5px solid #2b3035;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    .cal-day { font-weight: 700; color: #212529; margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid #dee2e6; }
    .cal-entry-out { font-size: 10px; background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; }
    .cal-entry-in { font-size: 10px; background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; }
    .cal-entry-task { font-size: 10px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; }
    
    .label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
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
                st.session_state.user = u
                st.rerun()
            else: st.error("Błąd logowania")
    st.stop()

# --- 4. PANEL BOCZNY (OPERACJE) ---
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("Wyloguj"):
        st.session_state.user = None
        st.rerun()
    st.divider()

    if st.session_state.user == "admin":
        with st.expander("Zarządzanie kontami"):
            nu = st.text_input("Nowy login")
            nh = st.text_input("Nowe hasło")
            if st.button("Dodaj pracownika"):
                if nu: dane["uzytkownicy"][nu] = nh; zapisz_dane(dane); st.rerun()
            st.write("Lista kont:")
            for usr in list(dane["uzytkownicy"].keys()):
                if usr != "admin":
                    if st.button(f"Usuń {usr}", key=f"del_{usr}"):
                        del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()
    st.divider()

    st.title("NOWY WPIS")
    typ = st.selectbox("Wybierz rodzaj", ["Zlecenie Produkcji", "Dostawa (PZ)", "Dyspozycja"])
    
    if typ == "Zlecenie Produkcji":
        kl = st.text_input("Klient")
        tm = st.text_input("Termin (np. 28.03)")
        op = st.text_area("Specyfikacja")
        if st.button("Zapisz Zlecenie"):
            if kl:
                dane["w_realizacji"].append({"klient": kl, "termin": tm, "opis": op, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()
    elif typ == "Dostawa (PZ)":
        ds = st.text_input("Dostawca")
        tm = st.text_input("Data (np. 29.03)")
        op = st.text_area("Co przyjeżdża?")
        if st.button("Zapisz Dostawę"):
            if ds:
                dane["przyjecia"].append({"dostawca": ds, "termin": tm, "towar": op, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()
    else:
        tyt = st.text_input("Tytuł zadania")
        tm = st.text_input("Na kiedy? (np. 30.03)")
        op = st.text_area("Szczegóły")
        if st.button("Zapisz Zadanie"):
            if tyt:
                dane["dyspozycje"].append({"tytul": tyt, "termin": tm, "opis": op, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()

# --- 5. KALENDARZ ---
if "cal_month" not in st.session_state: st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state: st.session_state.cal_year = datetime.now().year

def parse_date(txt):
    try:
        parts = str(txt).split(".")
        d, m = int(parts[0]), int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else st.session_state.cal_year
        return d, m, y
    except: return None, None, None

st.markdown('<div class="section-header">Harmonogram Miesięczny</div>', unsafe_allow_html=True)
c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1: 
    if st.button("Poprzedni"): 
        st.session_state.cal_month -= 1
        if st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        st.rerun()
with c_nav2:
    m_names = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    st.markdown(f"<h5 style='text-align: center; margin: 0;'>{m_names[st.session_state.cal_month-1]} {st.session_state.cal_year}</h5>", unsafe_allow_html=True)
with c_nav3: 
    if st.button("Następny"): 
        st.session_state.cal_month += 1
        if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        st.rerun()

events = {}
def add_to_cal(list_data, prefix, style_class, key_name):
    for item in list_data:
        d, m, y = parse_date(item.get('termin', ''))
        if d and m == st.session_state.cal_month and y == st.session_state.cal_year:
            if d not in events: events[d] = []
            events[d].append(f'<div class="{style_class}">{prefix}: {item[key_name]}</div>')

add_to_cal(dane["w_realizacji"], "W", "cal-entry-out", "klient")
add_to_cal(dane["przyjecia"], "P", "cal-entry-in", "dostawca")
add_to_cal(dane["dyspozycje"], "D", "cal-entry-task", "tytul")

month_days = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
w_cols_h = st.columns(7)
for i, d_n in enumerate(["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]):
    w_cols_h[i].markdown(f"<p style='text-align:center; font-size: 10px; color: #adb5bd; margin:0;'>{d_n}</p>", unsafe_allow_html=True)

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day != 0:
            html = f'<div class="cal-day">{day}</div>'
            if day in events: html += "".join(events[day])
            cols[i].markdown(html, unsafe_allow_html=True)

# --- 6. TABELE REALIZACJI ---

# 6.1 PRODUKCJA
st.markdown('<div class="section-header">Zlecenia Produkcyjne</div>', unsafe_allow_html=True)
tp1, tp2 = st.tabs(["Aktywne", "Zrealizowane"])
with tp1:
    if not dane["w_realizacji"]: st.info("Brak zleceń.")
    else:
        st.markdown('<div style="display: flex; padding-left: 5px;"><div class="label-text" style="width: 16%;">Klient</div><div class="label-text" style="width: 13%;">Termin</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Specyfikacja</div></div>', unsafe_allow_html=True)
        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].write(f"**{z['klient']}**")
            nt = c[1].text_input("T", value=z['termin'], key=f"z_t_{i}", label_visibility="collapsed")
            if nt != z['termin']: dane["w_realizacji"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
            c[2].write(f"{z['data_p']} ({z.get('autor', 'brak')})")
            with c[3].popover("Szczegóły"):
                no = st.text_area("Edytuj opis", value=z['opis'], key=f"z_o_{i}")
                if st.button("Zapisz", key=f"z_s_{i}"): dane["w_realizacji"][i]['opis'] = no; zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"z_g_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                z["zamknal"] = st.session_state.user
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"z_x_{i}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
with tp2: st.dataframe(pd.DataFrame(dane["zrealizowane"]).iloc[::-1], use_container_width=True)

# 6.2 LOGISTYKA
st.markdown('<div class="section-header">Przyjęcia Towaru (PZ)</div>', unsafe_allow_html=True)
tl1, tl2 = st.tabs(["Zaplanowane", "Historia"])
with tl1:
    if not dane["przyjecia"]: st.info("Brak dostaw.")
    else:
        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].write(f"**{p['dostawca']}**")
            nt = c[1].text_input("T", value=p['termin'], key=f"l_t_{i}", label_visibility="collapsed")
            if nt != p['termin']: dane["przyjecia"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
            c[2].write(f"{p['data_p']} ({p.get('autor', 'brak')})")
            with c[3].popover("Co w dostawie?"):
                no = st.text_area("Edytuj", value=p['towar'], key=f"l_o_{i}")
                if st.button("Zapisz", key=f"l_s_{i}"): dane["przyjecia"][i]['towar'] = no; zapisz_dane(dane); st.rerun()
            if c[4].button("OK", key=f"l_g_{i}"):
                p["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                p["odebral"] = st.session_state.user
                dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"l_x_{i}"): dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()
with tl2: st.dataframe(pd.DataFrame(dane["przyjecia_historia"]).iloc[::-1], use_container_width=True)

# 6.3 DYSPOZYCJE
st.markdown('<div class="section-header">Dyspozycje Dodatkowe</div>', unsafe_allow_html=True)
td1, td2 = st.tabs(["W toku", "Historia"])
with td1:
    if not dane["dyspozycje"]: st.info("Brak zadań.")
    else:
        for i, d in enumerate(dane["dyspozycje"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].write(f"**{d['tytul']}**")
            nt = c[1].text_input("T", value=d['termin'], key=f"d_t_{i}", label_visibility="collapsed")
            if nt != d['termin']: dane["dyspozycje"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
            c[2].write(f"{d['data_p']} ({d.get('autor', 'brak')})")
            with c[3].popover("Szczegóły"):
                no = st.text_area("Edytuj zadanie", value=d['opis'], key=f"d_o_{i}")
                if st.button("Zapisz", key=f"d_s_{i}"): dane["dyspozycje"][i]['opis'] = no; zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"d_g_{i}"):
                d["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                d["zamknal"] = st.session_state.user
                dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"d_x_{i}"): dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()
with td2: st.dataframe(pd.DataFrame(dane["dyspozycje_historia"]).iloc[::-1], use_container_width=True)
