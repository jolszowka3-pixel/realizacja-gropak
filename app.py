import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2 import service_account

# --- 1. KONFIGURACJA I STYLIZACJA ENTERPRISE ---
st.set_page_config(page_title="GROPAK ERP | Management System", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Globalne ustawienia typografii */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main {
    background-color: #f8fafc;
}

/* Sidebar - Modern Dark Mode */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    color: #f1f5f9 !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #cbd5e1 !important;
    font-size: 14px;
}

/* Nagłówki sekcji */
.section-header {
    font-size: 14px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 20px 0 10px 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 20px;
}

/* Profesjonalne Przyciski */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
    background-color: #ffffff !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 4px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    height: 34px !important;
    transition: all 0.2s ease;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stButton>button:hover {
    border-color: #3b82f6 !important;
    color: #3b82f6 !important;
    background-color: #f8fafc !important;
}

/* Przyciski Akcji (Primary) */
button:contains("Zapisz"), button:contains("Zaloguj"), button:contains("Opublikuj") {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
}
button:contains("Zapisz"):hover {
    background-color: #1d4ed8 !important;
}

/* Przyciski Statusów (Subtelne) */
button:contains("ZROBIONE"), button:contains("OK"), button:contains("WYŚLIJ") {
    background-color: #10b981 !important;
    color: white !important;
    border: none !important;
}
button:contains("X") {
    background-color: #ef4444 !important;
    color: white !important;
    border: none !important;
}

/* Badge Statusów */
.badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
}
.status-process { background-color: #fef3c7; color: #92400e; }
.status-done { background-color: #dcfce7; color: #166534; }
.status-return { background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }

/* Kalendarz - Grid Mode */
.day-col {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    min-height: 200px;
    padding: 8px;
}
.day-header-box {
    text-align: center;
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid #f1f5f9;
}
.day-name { font-weight: 700; font-size: 11px; color: #64748b; text-transform: uppercase; }
.day-date { font-size: 13px; font-weight: 500; color: #1e293b; }

.cal-entry {
    font-size: 10px;
    padding: 5px;
    margin-bottom: 3px;
    border-radius: 3px;
    font-weight: 600;
    border-left: 3px solid #3b82f6;
    background: #eff6ff;
    color: #1e40af;
}
.cal-entry-done { border-left-color: #10b981; background: #ecfdf5; color: #065f46; }

/* Tabele - Wiersze */
.table-row-container {
    background: white;
    padding: 12px;
    border-bottom: 1px solid #f1f5f9;
    align-items: center;
}
.label-text { font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
.data-text { font-size: 13px; color: #1e293b; font-weight: 500; }
.details-box { background: #f8fafc; border: 1px solid #f1f5f9; padding: 8px; border-radius: 4px; font-size: 12px; color: #475569; }

/* Powiadomienia */
.notif-box {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH (GOOGLE SHEETS) ---
GSHEET_NAME = "GROPAK_ERP_DB"
OPCJE_TRANSPORTU = ["Brak", "Auto 1", "Auto 2", "Transport zewnętrzny", "Odbiór osobisty", "Kurier"]

@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        scoped_credentials = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped_credentials)
    except Exception as e:
        st.error(f"Autoryzacja przerwana: {e}")
        return None

def posortuj_dane(dane):
    def sort_key(item):
        prio = 0 if item.get('pilne') else 1
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        try:
            termin = str(item.get('termin', '')).strip()
            if not termin: return (2, 9999, 99, 99, prio)
            parts = termin.split('.')
            d, m = int(parts[0]), int(parts[1])
            return (0, 2026, m, d, t_score, prio)
        except: return (1, 9999, 99, 99, prio)
    
    for k in ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]:
        if k in dane: dane[k].sort(key=sort_key)
    return dane

def wczytaj_dane():
    default_dane = {
        "w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [],
        "dyspozycje": [], "dyspozycje_historia": [], "odbiory": [], "odbiory_historia": [],
        "tablica": [], "uzytkownicy": {"admin": {"pass": "gropak2026", "role": "admin", "last_login": ""}}
    }
    client = get_gsheet_client()
    if not client: return default_dane
    try:
        sh = client.open(GSHEET_NAME)
        ws = sh.get_worksheet(0)
        val = ws.acell('A1').value
        if val:
            d = json.loads(val)
            for k, v in default_dane.items():
                if k not in d: d[k] = v
            return posortuj_dane(d)
    except: pass
    return default_dane

def zapisz_dane(dane_nowe):
    client = get_gsheet_client()
    if not client: return
    try:
        dane_nowe = posortuj_dane(dane_nowe)
        sh = client.open(GSHEET_NAME)
        ws = sh.get_worksheet(0)
        ws.update_acell('A1', json.dumps(dane_nowe))
    except Exception as e:
        st.error(f"Błąd synchronizacji: {e}")

dane = wczytaj_dane()

# --- 3. SYSTEM AUTORYZACJI ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = "wgląd"
if "notif_seen" not in st.session_state: st.session_state.notif_seen = False

if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br><h2 style='text-align:center;'>System ERP</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Identyfikator")
            p = st.text_input("Hasło dostępu", type="password")
            if st.form_submit_button("Zaloguj do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p:
                    st.session_state.user = u
                    st.session_state.role = dane["uzytkownicy"][u]["role"]
                    dane["uzytkownicy"][u]["last_login"] = datetime.now().strftime("%d.%m %H:%M")
                    zapisz_dane(dane); st.rerun()
                else: st.error("Nieprawidłowe poświadczenia.")
    st.stop()

is_admin = st.session_state.role == "admin"
can_edit = st.session_state.role in ["admin", "edycja"]

# --- 4. PANEL NAWIGACYJNY (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"### GROPAK ERP")
    st.markdown(f"Użytkownik: **{st.session_state.user}**")
    if st.button("Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()

    if can_edit:
        st.markdown("NOWY WPIS")
        typ = st.selectbox("Kategoria", ["Produkcja", "Odbiór", "Dostawa PZ", "Dyspozycja"])
        with st.form("add_new", clear_on_submit=True):
            if typ == "Produkcja":
                kl, tm, sz, au, kr, pi = st.text_input("Klient"), st.text_input("Termin (DD.MM)"), st.text_area("Specyfikacja"), st.selectbox("Transport", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5]), st.checkbox("Priorytet")
                if st.form_submit_button("Zapisz"):
                    if kl: dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"pilne":pi,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ == "Odbiór":
                mj, tm, tw, au, kr = st.text_input("Miejsce"), st.text_input("Termin"), st.text_area("Towar"), st.selectbox("Transport", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    if mj: dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":au,"kurs":kr,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            # ... (Logika dla PZ i Dyspozycji analogicznie)

# --- 5. DASHBOARD I HARMONOGRAM ---
st.markdown('<div class="section-header">Harmonogram Operacyjny</div>', unsafe_allow_html=True)

if "wo" not in st.session_state: st.session_state.wo = 0
c1, c2, c3 = st.columns([1, 8, 1])
if c1.button("Poprzedni"): st.session_state.wo -= 7; st.rerun()
if c3.button("Następny"): st.session_state.wo += 7; st.rerun()

start_date = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
grid = st.columns(7)

for i in range(7):
    day = start_date + timedelta(days=i)
    d_str = day.strftime('%d.%m')
    with grid[i]:
        st.markdown(f"""<div class="day-header-box"><div class="day-name">{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class="day-date">{d_str}</div></div>""", unsafe_allow_html=True)
        
        # Filtrowanie zadań na dany dzień
        entries = [z for z in dane["w_realizacji"] if z.get('termin') == d_str]
        for e in entries:
            cls = "cal-entry-done" if e.get('status') == "Gotowe" else "cal-entry"
            st.markdown(f"<div class='{cls}'>{e.get('klient')} ({e.get('auto')})</div>", unsafe_allow_html=True)

# --- 6. LISTY REALIZACJI (MODERN TABLES) ---
st.markdown('<div class="section-header">Zestawienie Realizacji</div>', unsafe_allow_html=True)
tabs = st.tabs(["Produkcja", "Odbiory", "Logistyka PZ", "Dyspozycje"])

def render_enterprise_table(lista, k_title, k_desc, k_id, typ):
    if not lista:
        st.info("Brak aktywnych pozycji w tej kategorii.")
        return

    # Header Tabeli
    h = st.columns([2, 1, 4, 1, 0.5])
    h[0].markdown('<div class="label-text">Kontrahent / Status</div>', unsafe_allow_html=True)
    h[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
    h[2].markdown('<div class="label-text">Specyfikacja / Zarządzanie</div>', unsafe_allow_html=True)
    h[3].markdown('<div class="label-text">Akcja</div>', unsafe_allow_html=True)

    for i, item in enumerate(lista):
        st.markdown('<div style="margin-bottom:1px;">', unsafe_allow_html=True)
        c = st.columns([2, 1, 4, 1, 0.5])
        
        status = item.get('status', 'W toku')
        st_cls = "status-done" if status == "Gotowe" else "status-process"
        prio_tag = " [PRIO]" if item.get('pilne') else ""
        
        c[0].markdown(f"<div class='data-text'>{item.get(k_title)}{prio_tag}</div><span class='badge {st_cls}'>{status}</span>", unsafe_allow_html=True)
        c[1].markdown(f"<div class='data-text'>{item.get('termin')}</div>", unsafe_allow_html=True)
        
        u_id = f"{k_id}_{i}"
        if not can_edit:
            c[2].markdown(f"<div class='details-box'>{item.get(k_desc)}</div>", unsafe_allow_html=True)
        else:
            with c[2].popover("Edytuj dane"):
                nt = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                ns = st.text_area("Szczegóły", item.get(k_desc), key=f"s_{u_id}")
                if st.button("Zaktualizuj", key=f"sv_{u_id}"):
                    item.update({"termin": nt, k_desc: ns}); zapisz_dane(dane); st.rerun()
        
        if can_edit:
            if status != "Gotowe":
                if c[3].button("ZROBIONE", key=f"ok_{u_id}"):
                    item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"arc_{u_id}"):
                    # Logika archiwizacji
                    zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"):
                lista.pop(i); zapisz_dane(dane); st.rerun()

with tabs[0]:
    render_enterprise_table(dane["w_realizacji"], "klient", "szczegoly", "prod", "prod")

# --- 7. KOMUNIKATY I TABLICA ---
st.markdown('<div class="section-header">Komunikaty systemowe</div>', unsafe_allow_html=True)
if not dane["tablica"]:
    st.info("Brak nowych ogłoszeń.")
else:
    for n in reversed(dane["tablica"]):
        st.markdown(f"""
        <div style="background:white; border:1px solid #e2e8f0; padding:15px; border-radius:4px; margin-bottom:10px;">
            <div style="font-size:12px; color:#64748b; margin-bottom:5px;">{n['data']} | Autor: {n['autor']}</div>
            <div style="font-size:14px; color:#1e293b;">{n['tresc']}</div>
        </div>
        """, unsafe_allow_html=True)
