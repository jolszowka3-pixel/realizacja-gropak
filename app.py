import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2 import service_account

# --- 1. KONFIGURACJA I STYLIZACJA ULTRA-COMPACT ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1e293b;
}

/* Minimalizacja marginesów głównych */
.main .block-container { padding-top: 1rem; padding-bottom: 1rem; }

/* --- KALENDARZ LOGISTYCZNY (ULTRA-COMPACT) --- */
.day-column {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 4px;
    min-height: 120px;
}

.day-header {
    text-align: center;
    border-bottom: 1px solid #f1f5f9;
    margin-bottom: 4px;
    padding-bottom: 2px;
}

.day-name { font-size: 9px; font-weight: 800; color: #94a3b8; text-transform: uppercase; }
.day-date { font-size: 12px; font-weight: 700; color: #0f172a; }

/* Grupa Auta */
.car-block {
    margin-bottom: 4px;
    border-left: 2px solid #cbd5e1;
    padding-left: 4px;
}
.car-name {
    font-size: 8px;
    font-weight: 900;
    color: #475569;
    text-transform: uppercase;
    margin-bottom: 1px;
}

/* Sekcja Kursu */
.kurs-wrap {
    font-size: 10px;
    line-height: 1.2;
    color: #1e293b;
}
.kurs-id {
    font-weight: 800;
    color: #3b82f6;
    display: inline;
}

/* Elementy zadań */
.task-inline {
    display: inline;
    font-weight: 500;
}
.task-done {
    color: #94a3b8;
    text-decoration: line-through;
}

/* Inne (PZ/Dyspozycje) */
.misc-entry {
    font-size: 9px;
    font-weight: 700;
    padding: 1px 3px;
    border-radius: 2px;
    margin-top: 2px;
}

/* Tabele - Styl Enterprise */
.section-header {
    font-size: 11px;
    font-weight: 800;
    color: #64748b;
    text-transform: uppercase;
    border-bottom: 1px solid #e2e8f0;
    margin: 15px 0 10px 0;
}
.badge { padding: 1px 6px; border-radius: 3px; font-size: 9px; font-weight: 700; text-transform: uppercase; }
.status-process { background-color: #fef3c7; color: #92400e; }
.status-done { background-color: #dcfce7; color: #166534; }
.data-text { font-size: 13px; font-weight: 600; }

[data-testid="stSidebar"] { background-color: #0f172a !important; }
div[data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }
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
        scoped = credentials.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(scoped)
    except: return None

def posortuj_dane(d):
    def sort_key(item):
        prio = 0 if item.get('pilne') else 1
        auto = str(item.get('auto', 'Brak'))
        a_score = OPCJE_TRANSPORTU.index(auto) if auto in OPCJE_TRANSPORTU else 99
        try:
            t = str(item.get('termin', '')).strip().split('.')
            return (0, 2026, int(t[1]), int(t[0]), a_score, int(item.get('kurs', 1)), prio)
        except: return (1, 9999, 99, 99, 99, 99, prio)
    for k in ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]:
        if k in d: d[k].sort(key=sort_key)
    return d

def wczytaj_dane():
    default = {"w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [], "dyspozycje": [], "dyspozycje_historia": [], "odbiory": [], "odbiory_historia": [], "tablica": [], "uzytkownicy": {"admin": {"pass": "gropak2026", "role": "admin", "last_login": ""}}}
    client = get_gsheet_client()
    if not client: return default
    try:
        sh = client.open(GSHEET_NAME)
        ws = sh.get_worksheet(0); val = ws.acell('A1').value
        if val:
            d = json.loads(val)
            for k, v in default.items():
                if k not in d: d[k] = v
            return posortuj_dane(d)
    except: pass
    return default

def zapisz_dane(d):
    client = get_gsheet_client()
    if client:
        try:
            sh = client.open(GSHEET_NAME); ws = sh.get_worksheet(0)
            ws.update_acell('A1', json.dumps(posortuj_dane(d)))
        except: pass

dane = wczytaj_dane()

# --- 3. LOGOWANIE ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><h3 style='text-align:center;'>GROPAK ERP</h3>", unsafe_allow_html=True)
        with st.form("l"):
            u = st.text_input("Użytkownik"); p = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p:
                    st.session_state.user = u; st.session_state.role = dane["uzytkownicy"][u]["role"]; st.rerun()
                else: st.error("Błąd")
    st.stop()

can_edit = st.session_state.role in ["admin", "edycja"]

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h4 style='color:white;'>PANEL ERP</h4>", unsafe_allow_html=True)
    if st.button("Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    if can_edit:
        typ = st.selectbox("Dodaj:", ["Produkcja", "Odbiór", "PZ", "Dyspozycja"])
        with st.form("a", clear_on_submit=True):
            if typ=="Produkcja":
                kl, tm, sz, au, kr, pi = st.text_input("Klient"), st.text_input("Termin"), st.text_area("Szczegóły"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5]), st.checkbox("Prio")
                if st.form_submit_button("Zapisz"):
                    dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"pilne":pi,"status":"W toku","data_p":datetime.now().strftime("%H:%M")}); zapisz_dane(dane); st.rerun()
            elif typ=="Odbiór":
                mj, tm, tw, au, kr = st.text_input("Skąd"), st.text_input("Termin"), st.text_area("Co"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":au,"kurs":kr,"status":"W toku","data_p":datetime.now().strftime("%H:%M")}); zapisz_dane(dane); st.rerun()
            # PZ i Dyspozycje analogicznie (uproszczone dla oszczędności miejsca)
            elif typ=="PZ":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Termin"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%H:%M")}); zapisz_dane(dane); st.rerun()
            elif typ=="Dyspozycja":
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"status":"W toku","data_p":datetime.now().strftime("%H:%M")}); zapisz_dane(dane); st.rerun()

# --- 5. KALENDARZ OPERACYJNY (ULTRA-COMPACT) ---
st.markdown('<div class="section-header">Harmonogram</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
c1, _, c3 = st.columns([1,12,1])
if c1.button("←"): st.session_state.wo -= 7; st.rerun()
if c3.button("→"): st.session_state.wo += 7; st.rerun()

start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
cols = st.columns(7)

for i in range(7):
    day = start + timedelta(days=i); d_str = day.strftime('%d.%m')
    with cols[i]:
        st.markdown(f"<div class='day-column'><div class='day-header'><div class='day-name'>{['PON','WT','ŚR','CZW','PT','SOB','ND'][i]}</div><div class='day-date'>{d_str}</div></div>", unsafe_allow_html=True)
        
        # Grupowanie
        day_map = {}
        for z in (dane["w_realizacji"] + dane["odbiory"]):
            if z.get('termin') == d_str:
                a, k = z.get('auto', 'Brak'), z.get('kurs', 1)
                if a not in day_map: day_map[a] = {}
                if k not in day_map[a]: day_map[a][k] = []
                day_map[a][k].append(z)
        
        for auto in sorted(day_map.keys()):
            st.markdown(f"<div class='car-block'><div class='car-name'>{auto}</div>", unsafe_allow_html=True)
            for kurs in sorted(day_map[auto].keys()):
                tasks = day_map[auto][kurs]
                names = []
                for t in tasks:
                    n = t.get('klient') or t.get('miejsce')
                    done = " task-done" if t.get('status') == "Gotowe" else ""
                    names.append(f"<span class='task-inline{done}'>{n}</span>")
                st.markdown(f"<div class='kurs-wrap'><span class='kurs-id'>K{kurs}:</span> {', '.join(names)}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        for p in dane["przyjecia"]:
            if p.get('termin') == d_str: st.markdown(f"<div class='misc-entry' style='background:#ecfdf5; color:#065f46;'>PZ: {p.get('dostawca')}</div>", unsafe_allow_html=True)
        for d in dane["dyspozycje"]:
            if d.get('termin') == d_str: st.markdown(f"<div class='misc-entry' style='background:#f8fafc; color:#475569;'>D: {d.get('tytul')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. TABELE (UJEDNOLICONE) ---
st.markdown('<div class="section-header">Realizacje</div>', unsafe_allow_html=True)
tabs = st.tabs(["Produkcja", "Odbiory", "Dostawy PZ", "Dyspozycje"])

def render_table(lista, k_name, k_desc, k_id, h_key):
    s1, s2, s3 = st.tabs(["Aktywne", "Poczekalnia", "Historia"])
    def draw(data):
        if not data: st.info("Brak"); return
        hc = st.columns([2, 1, 4.5, 1.2, 0.6])
        for i, item in enumerate(data):
            st.markdown("<div style='padding:4px 0; border-bottom:1px solid #f1f5f9;'>", unsafe_allow_html=True)
            c = st.columns([2, 1, 4.5, 1.2, 0.6])
            status = item.get('status','W toku')
            c[0].markdown(f"<div class='data-text'>{item.get(k_name)}</div><span class='badge {'status-done' if status=='Gotowe' else 'status-process'}'>{status}</span>", unsafe_allow_html=True)
            c[1].write(item.get('termin', '---'))
            with c[2].popover("Edytuj"):
                nt = st.text_input("Termin", item.get('termin'), key=f"t_{k_id}{i}")
                ns = st.text_area("Opis", item.get(k_desc), key=f"s_{k_id}{i}")
                if "auto" in item:
                    na = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(item.get('auto','Brak')), key=f"a_{k_id}{i}")
                    nk = st.selectbox("Kurs", [1,2,3,4,5], int(item.get('kurs',1))-1, key=f"k_{k_id}{i}")
                    if st.button("OK", key=f"b_{k_id}{i}"): item.update({"termin":nt, k_desc:ns, "auto":na, "kurs":nk}); zapisz_dane(dane); st.rerun()
                else:
                    if st.button("OK", key=f"b_{k_id}{i}"): item.update({"termin":nt, k_desc:ns}); zapisz_dane(dane); st.rerun()
            if status != "Gotowe":
                if c[3].button("ZROBIONE", key=f"ok_{k_id}{i}"): item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"arc_{k_id}{i}"): dane[h_key].append(data.pop(i)); zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"d_{k_id}{i}"): data.pop(i); zapisz_dane(dane); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    with s1: draw([z for z in lista if str(z.get('termin','')).strip()])
    with s2: draw([z for z in lista if not str(z.get('termin','')).strip()])
    with s3: st.dataframe(dane[h_key][::-1], use_container_width=True)

with tabs[0]: render_table(dane["w_realizacji"], "klient", "szczegoly", "p", "zrealizowane")
with tabs[1]: render_table(dane["odbiory"], "miejsce", "towar", "o", "odbiory_historia")
with tabs[2]: render_table(dane["przyjecia"], "dostawca", "towar", "pz", "przyjecia_historia")
with tabs[3]: render_table(dane["dyspozycje"], "tytul", "opis", "d", "dyspozycje_historia")
