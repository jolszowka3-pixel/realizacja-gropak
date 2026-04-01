import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2 import service_account

# --- 1. KONFIGURACJA I STYLIZACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Reset i bazy */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main {
    background-color: #f8fafc;
}

/* Sidebar - Ciemny, profesjonalny */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #94a3b8 !important;
    font-size: 13px;
}

/* Nagłówki sekcji */
.section-header {
    font-size: 13px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 24px 0 12px 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 16px;
}

/* Przyciski - Styl Enterprise */
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
}

/* Przyciski akcji (Primary) */
button:contains("Zapisz"), button:contains("Zaloguj"), button:contains("Opublikuj") {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
}

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
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    display: inline-block;
}
.status-process { background-color: #fef3c7; color: #92400e; }
.status-done { background-color: #dcfce7; color: #166534; }
.status-neutral { background-color: #f1f5f9; color: #475569; }

/* Kalendarz */
.day-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px;
    min-height: 220px;
}
.day-header {
    text-align: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 8px;
    margin-bottom: 8px;
}
.day-name { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
.day-date { font-size: 14px; font-weight: 600; color: #1e293b; }

.cal-item {
    font-size: 10px;
    padding: 4px 6px;
    margin-bottom: 3px;
    border-radius: 3px;
    font-weight: 600;
    border-left: 3px solid #3b82f6;
    background: #f0f7ff;
    color: #1e40af;
}
.cal-item-done { border-left-color: #10b981; background: #f0fdf4; color: #166534; }

/* Tabela */
.label-text { font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
.data-text { font-size: 13px; color: #1e293b; font-weight: 600; }
.details-box { background: #f8fafc; border: 1px solid #f1f5f9; padding: 8px; border-radius: 4px; font-size: 12px; color: #475569; line-height: 1.4; }

</style>
""", unsafe_allow_html=True)

# --- 2. BAZA DANYCH (GOOGLE SHEETS) ---
GSHEET_NAME = "GROPAK_ERP_DB"
OPCJE_TRANSPORTU = ["Brak", "Auto 1", "Auto 2", "Transport zewnętrzny", "Odbiór osobisty", "Kurier"]

@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        scoped = credentials.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(scoped)
    except:
        return None

def posortuj_dane(d):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        try:
            termin = str(item.get('termin', '')).strip()
            if not termin: return (2, 9999, 99, 99, pilne)
            parts = termin.split('.')
            d, m = int(parts[0]), int(parts[1])
            return (0, 2026, m, d, t_score, pilne)
        except: return (1, 9999, 99, 99, pilne)
    for k in ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]:
        if k in d: d[k].sort(key=sort_key)
    return d

def wczytaj_dane():
    default = {
        "w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [],
        "dyspozycje": [], "dyspozycje_historia": [], "odbiory": [], "odbiory_historia": [],
        "tablica": [], "uzytkownicy": {"admin": {"pass": "gropak2026", "role": "admin", "last_login": ""}}
    }
    client = get_gsheet_client()
    if not client: return default
    try:
        sh = client.open(GSHEET_NAME)
        ws = sh.get_worksheet(0)
        val = ws.acell('A1').value
        if val:
            d = json.loads(val)
            for k, v in default.items():
                if k not in d: d[k] = v
            return posortuj_dane(d)
    except: pass
    return default

def zapisz_dane(d):
    client = get_gsheet_client()
    if not client: return
    try:
        d = posortuj_dane(d)
        sh = client.open(GSHEET_NAME)
        ws = sh.get_worksheet(0)
        ws.update_acell('A1', json.dumps(d))
    except Exception as e:
        st.error(f"Sync error: {e}")

dane = wczytaj_dane()

# --- 3. LOGOWANIE ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = "wgląd"

if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br><h3 style='text-align:center;'>GROPAK ERP</h3>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Użytkownik")
            p = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p:
                    st.session_state.user, st.session_state.role = u, dane["uzytkownicy"][u]["role"]
                    dane["uzytkownicy"][u]["last_login"] = datetime.now().strftime("%d.%m %H:%M")
                    zapisz_dane(dane); st.rerun()
                else: st.error("Błąd autoryzacji")
    st.stop()

can_edit = st.session_state.role in ["admin", "edycja"]
is_admin = st.session_state.role == "admin"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### PANEL KONTROLNY")
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()

    if can_edit:
        st.markdown("DODAJ NOWY WPIS")
        typ = st.selectbox("Kategoria", ["Produkcja", "Odbiór", "Dostawa PZ", "Dyspozycja"])
        with st.form("f_add", clear_on_submit=True):
            if typ == "Produkcja":
                kl, tm, sz, au, kr, pi = st.text_input("Klient"), st.text_input("Termin (np. 01.04)"), st.text_area("Szczegóły"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5]), st.checkbox("Priorytet")
                if st.form_submit_button("Zapisz"):
                    if kl: dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"pilne":pi,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ == "Odbiór":
                mj, tm, tw, au, kr = st.text_input("Skąd"), st.text_input("Termin"), st.text_area("Co"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    if mj: dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":au,"kurs":kr,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ == "Dostawa PZ":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Termin"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    if ds: dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ == "Dyspozycja":
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    if ty: dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()

# --- 5. TERMINARZ ---
st.markdown('<div class="section-header">Harmonogram Operacyjny</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
c1, _, c3 = st.columns([1, 8, 1])
if c1.button("Poprzedni"): st.session_state.wo -= 7; st.rerun()
if c3.button("Następny"): st.session_state.wo += 7; st.rerun()

start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
cols = st.columns(7)
for i in range(7):
    day = start + timedelta(days=i)
    d_str = day.strftime('%d.%m')
    with cols[i]:
        st.markdown(f"<div class='day-card'><div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{d_str}</div></div>", unsafe_allow_html=True)
        for z in dane["w_realizacji"]:
            if z.get('termin') == d_str:
                cls = "cal-item-done" if z.get('status') == "Gotowe" else "cal-item"
                st.markdown(f"<div class='{cls}'>{z.get('klient')} ({z.get('auto')})</div>", unsafe_allow_html=True)
        for o in dane["odbiory"]:
            if o.get('termin') == d_str:
                st.markdown(f"<div class='cal-item' style='border-left-color:#a855f7; background:#faf5ff; color:#7e22ce;'>Odb: {o.get('miejsce')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. LISTY REALIZACJI ---
st.markdown('<div class="section-header">Zestawienie zadań</div>', unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["Produkcja", "Odbiory", "Dostawy PZ", "Dyspozycje"])

def render_table(lista, k_name, k_desc, k_id, typ_h):
    if not lista:
        st.info("Brak aktywnych zadań.")
        return
    
    # Nagłówki
    h = st.columns([2.2, 1, 4, 1.2, 0.6])
    h[0].markdown('<div class="label-text">Podmiot / Status</div>', unsafe_allow_html=True)
    h[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
    h[2].markdown('<div class="label-text">Specyfikacja / Edycja</div>', unsafe_allow_html=True)
    h[3].markdown('<div class="label-text">Akcja</div>', unsafe_allow_html=True)
    
    for i, item in enumerate(lista):
        st.markdown("<div style='padding:8px 0; border-bottom:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        c = st.columns([2.2, 1, 4, 1.2, 0.6])
        
        status = item.get('status','W toku')
        st_cls = "status-done" if status == "Gotowe" else ("status-neutral" if "odbiory" in k_id else "status-process")
        prio = " [PRIO]" if item.get('pilne') else ""
        
        c[0].markdown(f"<div class='data-text'>{item.get(k_name)}{prio}</div><span class='badge {st_cls}'>{status}</span>", unsafe_allow_html=True)
        c[1].markdown(f"<div class='data-text'>{item.get('termin')}</div>", unsafe_allow_html=True)
        
        u_id = f"{k_id}_{i}"
        if not can_edit:
            c[2].markdown(f"<div class='details-box'>{item.get(k_desc)}</div>", unsafe_allow_html=True)
        else:
            with c[2].popover("Edytuj"):
                nt = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                ns = st.text_area("Szczegóły", item.get(k_desc), key=f"s_{u_id}")
                if "w_realizacji" in k_id or "odbiory" in k_id:
                    na = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(item.get('auto','Brak')), key=f"a_{u_id}")
                    nk = st.selectbox("Kurs", [1,2,3,4,5], int(item.get('kurs',1))-1, key=f"k_{u_id}")
                    if st.button("Zapisz", key=f"sv_{u_id}"):
                        item.update({"termin":nt, k_desc:ns, "auto":na, "kurs":nk}); zapisz_dane(dane); st.rerun()
                else:
                    if st.button("Zapisz", key=f"sv_{u_id}"):
                        item.update({"termin":nt, k_desc:ns}); zapisz_dane(dane); st.rerun()
        
        if can_edit:
            if status != "Gotowe":
                if c[3].button("ZROBIONE", key=f"ok_{u_id}"):
                    item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"arc_{u_id}"):
                    dane[typ_h].append(lista.pop(i)); zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"):
                lista.pop(i); zapisz_dane(dane); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with t1: render_table(dane["w_realizacji"], "klient", "szczegoly", "prod", "zrealizowane")
with t2: render_table(dane["odbiory"], "miejsce", "towar", "odb", "odbiory_historia")
with t3: render_table(dane["przyjecia"], "dostawca", "towar", "pz", "przyjecia_historia")
with t4: render_table(dane["dyspozycje"], "tytul", "opis", "dysp", "dyspozycje_historia")

# --- 7. TABLICA OGŁOSZEŃ ---
st.markdown('<div class="section-header">Komunikaty</div>', unsafe_allow_html=True)
if can_edit:
    with st.form("f_note", clear_on_submit=True):
        nt = st.text_area("Treść ogłoszenia")
        if st.form_submit_button("Opublikuj ogłoszenie"):
            if nt: dane["tablica"].append({"tresc":nt, "data":datetime.now().strftime("%d.%m %H:%M"), "autor":st.session_state.user}); zapisz_dane(dane); st.rerun()

for i, n in enumerate(reversed(dane["tablica"])):
    st.markdown(f"""<div style="background:white; border:1px solid #e2e8f0; padding:12px; border-radius:4px; margin-bottom:8px;">
        <div style="font-size:11px; color:#94a3b8; font-weight:700;">{n['data']} | {n['autor']}</div>
        <div style="font-size:13px; color:#334155; margin-top:4px;">{n['tresc']}</div>
    </div>""", unsafe_allow_html=True)
