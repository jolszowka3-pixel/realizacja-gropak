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
    
    /* UNIWERSALNE STYLE DLA PRZYCISKÓW AKCJI (Precyzyjny selektor dla wszystkich sekcji) */
    /* Zielone przyciski akcji (GOTOWE / OK) - Kolumna 5 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(5) button {
        border: 1px solid #c3e6cb !important;
        color: #1e7e34 !important;
        background-color: #f8fff9 !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(5) button:hover {
        background-color: #28a745 !important;
        color: white !important;
    }
    
    /* Czerwone przyciski usuwania (X) - Kolumna 6 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(6) button {
        border: 1px solid #f5c6cb !important;
        color: #bd2130 !important;
        background-color: #fff9f9 !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(6) button:hover {
        background-color: #dc3545 !important;
        color: white !important;
    }

    .main .block-container { padding-top: 2rem; }
    .section-header {
        background-color: #f1f3f5;
        padding: 12px 15px;
        border-radius: 4px;
        margin-bottom: 10px;
        margin-top: 20px;
        font-weight: 600;
        color: #343a40;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-left: 4px solid #495057;
    }
    .cal-day { font-weight: 600; color: #495057; margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid #f1f3f5; }
    .cal-entry-out { font-size: 10px; background: #e9ecef; color: #0056b3; border-left: 3px solid #0056b3; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; font-weight: 500; }
    .cal-entry-in { font-size: 10px; background: #f8f9fa; color: #28a745; border-left: 3px solid #28a745; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; font-weight: 500; }
    .cal-entry-task { font-size: 10px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 2px 5px; margin-bottom: 2px; border-radius: 2px; font-weight: 500; }
    
    div[data-testid="stPopover"] > button { border: 1px solid #dee2e6 !important; background: white !important; text-align: left !important; color: #495057 !important; font-size: 13px !important; height: 2.1em !important; }
    .label-text { font-size: 11px; color: #adb5bd; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .stTextInput input { height: 2.1em !important; font-size: 12px !important; padding: 0 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BAZA DANYCH ---
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

# --- 3. LOGOWANIE ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.subheader("Logowanie do systemu GROPAK ERP")
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

# --- 4. NAWIGACJA KALENDARZA ---
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

# --- 5. PANEL BOCZNY ---
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("Wyloguj"):
        st.session_state.user = None
        st.rerun()
    st.divider()

    if st.session_state.user == "admin":
        with st.expander("Panel Administratora"):
            nu = st.text_input("Nowy login")
            nh = st.text_input("Nowe hasło")
            if st.button("Dodaj konto"):
                if nu: dane["uzytkownicy"][nu] = nh; zapisz_dane(dane); st.rerun()
            st.write("Użytkownicy:")
            for usr in list(dane["uzytkownicy"].keys()):
                if usr != "admin":
                    if st.button(f"Usuń {usr}", key=f"del_u_{usr}"):
                        del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()
    st.divider()

    st.title("OPERACJE")
    opcja = st.selectbox("Typ dokumentu", ["Zlecenie Produkcji", "Przyjęcie Towaru (PZ)", "Dyspozycja Dodatkowa"])
    
    if opcja == "Zlecenie Produkcji":
        k_klient = st.text_input("Klient")
        k_termin = st.text_input("Termin (np. 27.03)")
        k_produkty = st.text_area("Specyfikacja")
        if st.button("Zapisz Zlecenie"):
            if k_klient:
                dane["w_realizacji"].append({"klient": k_klient, "termin": k_termin, "opis": k_produkty, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()
    elif opcja == "Przyjęcie Towaru (PZ)":
        p_dostawca = st.text_input("Dostawca")
        p_termin = st.text_input("Data dostawy (np. 28.03)")
        p_towar = st.text_area("Szczegóły")
        if st.button("Zapisz Przyjęcie"):
            if p_dostawca:
                dane["przyjecia"].append({"dostawca": p_dostawca, "termin": p_termin, "towar": p_towar, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()
    else:
        d_tytul = st.text_input("Tytuł dyspozycji")
        d_termin = st.text_input("Termin (np. 29.03)")
        d_opis = st.text_area("Opis")
        if st.button("Zapisz Dyspozycję"):
            if d_tytul:
                dane["dyspozycje"].append({"tytul": d_tytul, "termin": d_termin, "opis": d_opis, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()

# --- 6. WIDOK GŁÓWNY ---
st.subheader("System Zarządzania GROPAK ERP")

# KALENDARZ
st.markdown('<div class="section-header">Harmonogram Realizacji</div>', unsafe_allow_html=True)
c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1: 
    if st.button("Poprzedni"): zmien_miesiac(-1); st.rerun()
with c_nav2:
    m_names = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    st.markdown(f"<h5 style='text-align: center; margin: 0;'>{m_names[st.session_state.cal_month-1]} {st.session_state.cal_year}</h5>", unsafe_allow_html=True)
with c_nav3: 
    if st.button("Następny"): zmien_miesiac(1); st.rerun()

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
for ds in dane["dyspozycje"]:
    d, m, y = parse_date(ds.get('termin', ''))
    if d and m == st.session_state.cal_month and y == st.session_state.cal_year:
        if d not in events_map: events_map[d] = []
        events_map[d].append(f'<div class="cal-entry-task">D: {ds["tytul"]}</div>')

month_days = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
cols_h = st.columns(7)
for i, d_n in enumerate(["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]):
    cols_h[i].markdown(f"<p style='text-align:center; font-size: 10px; color: #adb5bd; margin:0;'>{d_n}</p>", unsafe_allow_html=True)

for week in month_days:
    w_cols = st.columns(7)
    for i, day in enumerate(week):
        if day != 0:
            html = f'<div class="cal-day">{day}</div>'
            if day in events_map: html += "".join(events_map[day])
            w_cols[i].markdown(html, unsafe_allow_html=True)

# --- SEKCJA PRODUKCJI ---
st.markdown('<div class="section-header">Zlecenia Produkcyjne</div>', unsafe_allow_html=True)
t_prod1, t_prod2 = st.tabs(["W realizacji", "Zrealizowane"])
with t_prod1:
    if not dane["w_realizacji"]: st.info("Brak aktywnych zleceń.")
    else:
        st.markdown('<div style="display: flex;"><div class="label-text" style="width: 16%;">Klient</div><div class="label-text" style="width: 13%;">Termin (edytuj)</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Specyfikacja</div></div>', unsafe_allow_html=True)
        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].write(f"**{z['klient']}**")
            new_term = c[1].text_input("T", value=z.get('termin', '-'), key=f"t_z_{i}", label_visibility="collapsed")
            if new_term != z.get('termin'):
                dane["w_realizacji"][i]['termin'] = new_term; zapisz_dane(dane); st.rerun()
            c[2].write(f"{z.get('data_p', '-')} ({z.get('autor', '?')})")
            with c[3].popover(f"{z['opis'][:60]}..."):
                n_p = st.text_area("Specyfikacja", value=z['opis'], key=f"pe_{i}")
                if st.button("Zapisz", key=f"ps_{i}"):
                    dane["w_realizacji"][i]['opis'] = n_p; zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"pd_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                z["zamknal"] = st.session_state.user
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"px_{i}"):
                dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
with t_prod2:
    if dane["zrealizowane"]: st.dataframe(pd.DataFrame(dane["zrealizowane"]).iloc[::-1], use_container_width=True)

# --- SEKCJA LOGISTYKI ---
st.markdown('<div class="section-header">Przyjęcia Towaru (PZ)</div>', unsafe_allow_html=True)
t_log1, t_log2 = st.tabs(["Zaplanowane", "Historia"])
with t_log1:
    if not dane["przyjecia"]: st.info("Brak zaplanowanych dostaw.")
    else:
        st.markdown('<div style="display: flex;"><div class="label-text" style="width: 16%;">Dostawca</div><div class="label-text" style="width: 13%;">Termin (edytuj)</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Szczegóły</div></div>', unsafe_allow_html=True)
        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].write(f"**{p['dostawca']}**")
            new_term_p = c[1].text_input("T", value=p.get('termin', '-'), key=f"t_p_{i}", label_visibility="collapsed")
            if new_term_p != p.get('termin'):
                dane["przyjecia"][i]['termin'] = new_term_p; zapisz_dane(dane); st.rerun()
            c[2].write(f"{p.get('data_p', '-')} ({p.get('autor', '?')})")
            with c[3].popover(f"{p['towar'][:60]}..."):
                n_tw = st.text_area("Towar", value=p['towar'], key=f"pze_{i}")
                if st.button("Zapisz", key=f"pzs_{i}"):
                    dane["przyjecia"][i]['towar'] = n_tw; zapisz_dane(dane); st.rerun()
            if c[4].button("OK", key=f"pzo_{i}"):
                p["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                p["odebral"] = st.session_state.user
                dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"pzx_{i}"):
                dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()
with t_log2:
    if dane["przyjecia_historia"]: st.dataframe(pd.DataFrame(dane["przyjecia_historia"]).iloc[::-1], use_container_width=True)

# --- SEKCJA DYSPOZYCJI ---
st.markdown('<div class="section-header">Dyspozycje Dodatkowe</div>', unsafe_allow_html=True)
t_dys1, t_dys2 = st.tabs(["W toku", "Historia"])
with t_dys1:
    if not dane["dyspozycje"]: st.info("Brak aktywnych dyspozycji.")
    else:
        st.markdown('<div style="display: flex;"><div class="label-text" style="width: 16%;">Tytuł / Cel</div><div class="label-text" style="width: 13%;">Termin (edytuj)</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Opis zadania</div></div>', unsafe_allow_html=True)
        for i, d in enumerate(dane["dyspozycje"]):
            # Układ [1.5, 1.2, 1.2, 4.5, 0.8, 0.4] zachowany
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].write(f"**{d['tytul']}**")
            new_term_d = c[1].text_input("T", value=d.get('termin', '-'), key=f"t_d_{i}", label_visibility="collapsed")
            if new_term_d != d.get('termin'):
                dane["dyspozycje"][i]['termin'] = new_term_d; zapisz_dane(dane); st.rerun()
            c[2].write(f"{d.get('data_p', '-')} ({d.get('autor', '?')})")
            with c[3].popover(f"{d['opis'][:60]}..."):
                n_do = st.text_area("Opis", value=d['opis'], key=f"pde_{i}")
                if st.button("Zapisz", key=f"pds_{i}"):
                    dane["dyspozycje"][i]['opis'] = n_do; zapisz_dane(dane); st.rerun()
            
            # Przycisk w kolumnie 5 -> Zielony
            if c[4].button("GOTOWE", key=f"pdd_{i}"):
                d["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                d["zamknal"] = st.session_state.user
                dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
            
            # Przycisk w kolumnie 6 -> Czerwony
            if c[5].button("X", key=f"pdx_{i}"):
                dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()
with t_dys2:
    if dane["dyspozycje_historia"]: st.dataframe(pd.DataFrame(dane["dyspozycje_historia"]).iloc[::-1], use_container_width=True)
