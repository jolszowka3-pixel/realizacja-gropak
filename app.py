import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURACJA I STYLIZACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
    <style>
    .stButton>button, .stFormSubmitButton>button { 
        width: 100%; border-radius: 6px; min-height: 32px !important; height: 32px !important; 
        font-size: 12px; font-weight: 600; transition: all 0.2s ease-in-out;
        border: 1px solid #ced4da; padding: 0 10px; line-height: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    button:has(div p:contains("GOTOWE")), button:has(div p:contains("OK")), button:contains("GOTOWE"), button:contains("OK") {
        border: none !important; color: white !important; background-color: #28a745 !important;
    }
    button:has(div p:contains("X")), button:contains("X") {
        border: none !important; color: white !important; background-color: #dc3545 !important; padding: 0 !important;
    }
    button:has(div p:contains("Zapisz")), button:contains("Zapisz") {
        border: none !important; color: white !important; background-color: #007bff !important;
    }
    
    div[data-testid="stHorizontalBlock"] { align-items: center !important; padding: 4px 0; }
    .stTextInput input { min-height: 32px !important; height: 32px !important; font-size: 12px !important; border-radius: 6px !important; }
    div[data-testid="stPopover"] > button { min-height: 32px !important; height: 32px !important; border: 1px solid #ced4da !important; background: white !important; text-align: left !important; color: #495057 !important; }

    .main .block-container { padding-top: 2rem; }
    .section-header {
        background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px;
        font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    .sidebar-header {
        background: linear-gradient(90deg, #1e7e34, #28a745);
        color: white; padding: 12px; border-radius: 6px; text-align: center;
        font-weight: 700; font-size: 14px; margin-bottom: 15px; letter-spacing: 1px;
    }
    
    .week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; align-items: stretch; margin-top: 15px; margin-bottom: 25px; }
    .day-col { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; flex-direction: column; min-height: 120px; }
    .day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 12px; padding-bottom: 6px; }
    .day-name { font-weight: 700; font-size: 13px; color: #495057; }
    .day-date { font-size: 11px; color: #868e96; }
    
    .cal-entry-out { cursor: help; font-size: 10px; background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; padding: 5px 6px; margin-bottom: 5px; border-radius: 4px; font-weight: 600; }
    .cal-entry-in { cursor: help; font-size: 10px; background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; padding: 5px 6px; margin-bottom: 5px; border-radius: 4px; font-weight: 600; }
    .cal-entry-task { cursor: help; font-size: 10px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 5px 6px; margin-bottom: 5px; border-radius: 4px; font-weight: 600; }
    
    /* STYLE DLA AUT */
    .car-badge { background-color: #343a40; color: white; padding: 1px 4px; border-radius: 3px; font-size: 9px; margin-right: 4px; }
    
    .badge-urgent { background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 5px; }
    .label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    button[data-baseweb="tab"] { font-size: 16px !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH I SORTOWANIE ---
PLIK_DANYCH = "baza_gropak_v3.json"

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        try:
            parts = str(item.get('termin', '')).strip().split('.')
            if len(parts) >= 2:
                d, m = int(parts[0]), int(parts[1])
                y = int(parts[2]) if len(parts) > 2 else datetime.now().year
                return (0, y, m, d, pilne)
            return (1, 9999, 99, 99, pilne) 
        except:
            return (1, 9999, 99, 99, pilne)

    for k in ["w_realizacji", "przyjecia", "dyspozycje"]:
        if k in dane: dane[k].sort(key=sort_key)
    return dane

def wczytaj_dane():
    default_dane = {"w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [], "dyspozycje": [], "dyspozycje_historia": [], "uzytkownicy": {"admin": "gropak2026"}}
    if os.path.exists(PLIK_DANYCH):
        try:
            with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
                d = json.load(f)
                for k, v in default_dane.items():
                    if k not in d: d[k] = v
                return posortuj_dane(d) 
        except: pass
    return default_dane

def zapisz_dane(dane):
    dane = posortuj_dane(dane) 
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- 3. LOGOWANIE ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.subheader("GROPAK ERP - Logowanie")
    c1, _ = st.columns([1, 2])
    with c1:
        with st.form("login_form"):
            u = st.text_input("Użytkownik"); p = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p:
                    st.session_state.user = u; st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

# --- 4. PANEL BOCZNY (TRANSPORT) ---
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()

    st.markdown('<div class="sidebar-header">➕ DODAJ NOWY WPIS</div>', unsafe_allow_html=True)
    typ = st.selectbox("Rodzaj:", ["🏭 Zlecenie Produkcji", "🚚 Dostawa (PZ)", "📋 Dyspozycja"], label_visibility="collapsed")
    
    if typ == "🏭 Zlecenie Produkcji":
        with st.form("form_prod", clear_on_submit=True):
            kl = st.text_input("👤 Klient"); tm = st.text_input("📅 Termin (np. 31.03)")
            op = st.text_area("📝 Specyfikacja ogólna"); sz = st.text_area("📦 Szczegóły (ilości)")
            st.markdown("**🚛 Logistyka Wyjazdowa:**")
            col_a, col_k = st.columns(2)
            auto = col_a.selectbox("Auto:", ["Brak", "Auto 1", "Auto 2"])
            kurs = col_k.selectbox("Kurs nr:", [1, 2, 3, 4, 5])
            p = st.checkbox("🔥 PILNE")
            if st.form_submit_button("💾 Zapisz Zlecenie"):
                if kl: 
                    dane["w_realizacji"].append({
                        "klient": kl, "termin": tm, "opis": op, "szczegoly": sz, "pilne": p, 
                        "auto": auto, "kurs": kurs,
                        "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user
                    })
                    zapisz_dane(dane); st.rerun()
    elif typ == "🚚 Dostawa (PZ)":
        with st.form("form_log", clear_on_submit=True):
            ds = st.text_input("🏢 Dostawca"); tm = st.text_input("📅 Data (np. 31.03)"); op = st.text_area("📦 Co przyjeżdża?"); p = st.checkbox("🔥 PILNE")
            if st.form_submit_button("💾 Zapisz Dostawę"):
                if ds: 
                    dane["przyjecia"].append({"dostawca": ds, "termin": tm, "towar": op, "pilne": p, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                    zapisz_dane(dane); st.rerun()
    else:
        with st.form("form_dysp", clear_on_submit=True):
            tyt = st.text_input("🎯 Tytuł"); tm = st.text_input("📅 Termin"); op = st.text_area("📝 Opis"); p = st.checkbox("🔥 PILNE")
            if st.form_submit_button("💾 Zapisz Zadanie"):
                if tyt: 
                    dane["dyspozycje"].append({"tytul": tyt, "termin": tm, "opis": op, "pilne": p, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                    zapisz_dane(dane); st.rerun()

# --- 5. STATYSTYKI ---
st.markdown('<div class="section-header">Podsumowanie</div>', unsafe_allow_html=True)
c_s1, c_s2, c_s3 = st.columns(3)
c_s1.metric("📦 Aktywne Zlecenia", len(dane["w_realizacji"]))
c_s2.metric("🚚 Oczekujące Dostawy", len(dane["przyjecia"]))
c_s3.metric("📋 Dyspozycje", len(dane["dyspozycje"]))

# --- 6. TERMINARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "week_offset" not in st.session_state: st.session_state.week_offset = 0
c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1: 
    if st.button("← Poprzedni"): st.session_state.week_offset -= 7; st.rerun()
with c_nav3: 
    if st.button("Następny →"): st.session_state.week_offset += 7; st.rerun()

today = datetime.now()
start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=st.session_state.week_offset)
dates_in_week = [(start_of_week + timedelta(days=i)) for i in range(7)]
with c_nav2: st.markdown(f"<h5 style='text-align: center;'>{dates_in_week[0].strftime('%d.%m')} - {dates_in_week[6].strftime('%d.%m.%Y')}</h5>", unsafe_allow_html=True)

def parse_d(txt):
    try: parts = str(txt).split("."); return int(parts[0]), int(parts[1])
    except: return None, None

day_names = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
html_cal = '<div class="week-grid">'
for i, date in enumerate(dates_in_week):
    html_cal += f'<div class="day-col"><div class="day-header"><div class="day-name">{day_names[i]}</div><div class="day-date">{date.strftime("%d.%m")}</div></div>'
    dv, mv = date.day, date.month
    
    for z in dane["w_realizacji"]:
        zd, zm = parse_d(z.get('termin', ''))
        if zd == dv and zm == mv:
            p_m = "🔥 " if z.get('pilne') else ""
            a_m = f'<span class="car-badge">🚗 {z.get("auto", "")[-1]}/{z.get("kurs", "")}</span>' if z.get('auto') != "Brak" else ""
            tooltip = f"Spec: {z.get('opis','')}&#10;Szczegóły: {z.get('szczegoly','')}"
            html_cal += f'<div class="cal-entry-out" title="{tooltip}">{a_m}{p_m}W: {z.get("klient","-")}</div>'
    
    for p in dane["przyjecia"]:
        pd, pm = parse_d(p.get('termin', ''))
        if pd == dv and pm == mv:
            html_cal += f'<div class="cal-entry-in">P: {p.get("dostawca","-")}</div>'
            
    for ds in dane["dyspozycje"]:
        dd, dm = parse_d(ds.get('termin', ''))
        if dd == dv and dm == mv:
            html_cal += f'<div class="cal-entry-task">D: {ds.get("tytul","-")}</div>'
    html_cal += '</div>'
html_cal += '</div>'
st.markdown(html_cal, unsafe_allow_html=True)

# --- 7. TABELE ---
search = st.text_input("🔍 Wyszukaj...", "").lower()
t_p, t_l, t_d = st.tabs(["🏭 Produkcja", "🚚 Przyjęcia", "📋 Dyspozycje"])

with t_p:
    tp1, tp2 = st.tabs(["Aktywne", "Historia"])
    with tp1:
        for i, z in enumerate(dane["w_realizacji"]):
            if search and search not in str(z).lower(): continue
            c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
            c[0].markdown(f"**{z.get('klient')}** {'🔥' if z.get('pilne') else ''}")
            nt = c[1].text_input("T", value=z.get('termin'), key=f"zt{i}", label_visibility="collapsed")
            if nt != z.get('termin'): dane["w_realizacji"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
            
            # Edycja auta/kursu w tabeli
            with c[2].popover(f"🚗 {z.get('auto','-')[-1] if z.get('auto')!='Brak' else 'Brak'}/K{z.get('kurs','-')}"):
                na = st.selectbox("Zmień auto:", ["Brak", "Auto 1", "Auto 2"], index=["Brak", "Auto 1", "Auto 2"].index(z.get('auto', 'Brak')), key=f"na{i}")
                nk = st.selectbox("Zmień kurs:", [1, 2, 3, 4, 5], index=z.get('kurs', 1)-1, key=f"nk{i}")
                if st.button("Zaktualizuj transport", key=f"bt{i}"):
                    dane["w_realizacji"][i]['auto'] = na
                    dane["w_realizacji"][i]['kurs'] = nk
                    zapisz_dane(dane); st.rerun()

            with c[3].popover("Szczegóły"):
                no = st.text_area("Specyfikacja", value=z.get('opis',''), key=f"zo{i}")
                nsz = st.text_area("Ilości", value=z.get('szczegoly',''), key=f"zsz{i}")
                if st.button("Zapisz zmiany", key=f"zs{i}"):
                    dane["w_realizacji"][i]['opis'] = no; dane["w_realizacji"][i]['szczegoly'] = nsz
                    zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"zg{i}"):
                z["zamknal"] = st.session_state.user; dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"zx{i}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()

with t_l:
    for i, p in enumerate(dane["przyjecia"]):
        if search and search not in str(p).lower(): continue
        c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
        c[0].write(f"**{p.get('dostawca')}**")
        nt = c[1].text_input("T", value=p.get('termin'), key=f"lt{i}", label_visibility="collapsed")
        if nt != p.get('termin'): dane["przyjecia"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
        c[2].write(f"{p.get('data_p')}")
        with c[3].popover("Szczegóły"):
            no = st.text_area("Co?", value=p.get('towar',''), key=f"lo{i}")
            if st.button("Zapisz", key=f"ls{i}"): dane["przyjecia"][i]['towar'] = no; zapisz_dane(dane); st.rerun()
        if c[4].button("OK", key=f"lg{i}"): dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"lx{i}"): dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()

with t_d:
    for i, d in enumerate(dane["dyspozycje"]):
        if search and search not in str(d).lower(): continue
        c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
        c[0].write(f"**{d.get('tytul')}**")
        nt = c[1].text_input("T", value=d.get('termin'), key=f"dt{i}", label_visibility="collapsed")
        if nt != d.get('termin'): dane["dyspozycje"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
        c[2].write(f"{d.get('data_p')}")
        with c[3].popover("Opis"):
            no = st.text_area("Szczegóły", value=d.get('opis',''), key=f"do{i}")
            if st.button("Zapisz", key=f"ds{i}"): dane["dyspozycje"][i]['opis'] = no; zapisz_dane(dane); st.rerun()
        if c[4].button("GOTOWE", key=f"dg{i}"): dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"dx{i}"): dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()
