import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2 import service_account

# --- 1. KONFIGURACJA I STYLIZACJA ENTERPRISE ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1e293b;
}

.main {
    background-color: #f8fafc;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #94a3b8 !important;
    font-size: 13px;
}

/* Nagłówki sekcji */
.section-header {
    font-size: 12px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 16px 0 8px 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 12px;
}

/* Kalendarz - Kompaktowy styl */
.day-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 8px;
    min-height: 150px;
    height: 100%;
}
.day-header {
    text-align: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 4px;
    margin-bottom: 6px;
}
.day-name { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
.day-date { font-size: 13px; font-weight: 600; color: #1e293b; }

/* Bloki grupujące w kalendarzu */
.cal-group {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 3px;
    margin-bottom: 4px;
    padding: 4px;
}
.cal-group-header {
    font-size: 9px;
    font-weight: 800;
    color: #475569;
    text-transform: uppercase;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 3px;
    padding-bottom: 2px;
}
.cal-item-text {
    font-size: 10px;
    font-weight: 500;
    color: #1e293b;
    line-height: 1.2;
    padding-left: 4px;
    border-left: 2px solid #3b82f6;
    margin-bottom: 2px;
}
.cal-item-done { border-left-color: #10b981 !important; color: #64748b; text-decoration: line-through; }

/* Reszta UI */
.badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; display: inline-block; }
.status-process { background-color: #fef3c7; color: #92400e; }
.status-done { background-color: #dcfce7; color: #166534; }
.label-text { font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
.data-text { font-size: 13px; color: #1e293b; font-weight: 600; }
.details-box { background: #f8fafc; border: 1px solid #f1f5f9; padding: 10px; border-radius: 4px; font-size: 12px; color: #475569; }

.stButton>button { height: 32px !important; font-size: 12px !important; }
div[data-testid="stHorizontalBlock"] { align-items: flex-start !important; gap: 0.5rem !important; }
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

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        try:
            termin = str(item.get('termin', '')).strip()
            if not termin: return (2, 9999, 99, 99, 99, pilne)
            parts = termin.split('.')
            return (0, 2026, int(parts[1]), int(parts[0]), t_score, pilne)
        except: return (1, 9999, 99, 99, 99, pilne)
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

def zapisz_dane(dane_do_zapisu):
    client = get_gsheet_client()
    if not client: return
    try:
        dane_do_zapisu = posortuj_dane(dane_do_zapisu)
        sh = client.open(GSHEET_NAME)
        ws = sh.get_worksheet(0)
        ws.update_acell('A1', json.dumps(dane_do_zapisu))
    except: pass

dane = wczytaj_dane()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = "wgląd"

if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br><h3 style='text-align:center;'>GROPAK ERP</h3>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Użytkownik"); p = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p: 
                    st.session_state.user, st.session_state.role = u, dane["uzytkownicy"][u]["role"]
                    zapisz_dane(dane); st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

can_edit = st.session_state.role in ["admin", "edycja"]
is_admin = st.session_state.role == "admin"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### GROPAK ERP")
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    if can_edit:
        typ = st.selectbox("Nowy wpis:", ["Produkcja", "Odbiór", "Dostawa PZ", "Dyspozycja"])
        with st.form("f_add", clear_on_submit=True):
            if typ=="Produkcja":
                kl, tm, sz, au, kr, pi = st.text_input("Klient"), st.text_input("Termin"), st.text_area("Szczegóły"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5]), st.checkbox("Priorytet")
                if st.form_submit_button("Zapisz"):
                    if kl: dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"pilne":pi,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")}); zapisz_dane(dane); st.rerun()
            elif typ=="Odbiór":
                mj, tm, tw, au, kr = st.text_input("Skąd"), st.text_input("Termin"), st.text_area("Co"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    if mj: dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":au,"kurs":kr,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")}); zapisz_dane(dane); st.rerun()
            elif typ=="Dostawa PZ":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Termin"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    if ds: dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")}); zapisz_dane(dane); st.rerun()
            elif typ=="Dyspozycja":
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    if ty: dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")}); zapisz_dane(dane); st.rerun()

# --- 5. HARMONOGRAM (GRUPOWANIE PO AUTACH) ---
st.markdown('<div class="section-header">Harmonogram</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
c1, _, c3 = st.columns([1,10,1])
if c1.button("Poprzedni"): st.session_state.wo -= 7; st.rerun()
if c3.button("Następny"): st.session_state.wo += 7; st.rerun()

start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
cols = st.columns(7)
for i in range(7):
    day = start + timedelta(days=i); d_str = day.strftime('%d.%m')
    with cols[i]:
        st.markdown(f"<div class='day-card'><div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{d_str}</div></div>", unsafe_allow_html=True)
        
        # Logika grupowania zadań na ten dzień
        day_tasks = {}
        for z in dane["w_realizacji"]:
            if z.get('termin') == d_str:
                key = (z.get('auto', 'Brak'), z.get('kurs', 1))
                if key not in day_tasks: day_tasks[key] = []
                day_tasks[key].append(z)
        for o in dane["odbiory"]:
            if o.get('termin') == d_str:
                key = (o.get('auto', 'Brak'), o.get('kurs', 1))
                if key not in day_tasks: day_tasks[key] = []
                day_tasks[key].append(o)
        
        # Wyświetlanie zgrupowanych bloków
        for (auto, kurs) in sorted(day_tasks.keys()):
            tasks = day_tasks[(auto, kurs)]
            auto_lbl = f"{auto} / K{kurs}" if auto != "Brak" else "Brak transportu"
            st.markdown(f"<div class='cal-group'><div class='cal-group-header'>{auto_lbl}</div>", unsafe_allow_html=True)
            for t in tasks:
                name = t.get('klient') or t.get('miejsce')
                status_cls = "cal-item-done" if t.get('status') == "Gotowe" else ""
                st.markdown(f"<div class='cal-item-text {status_cls}'>{name}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Dostawy PZ i Dyspozycje (osobno, bo nie mają aut)
        for p in dane["przyjecia"]:
            if p.get('termin') == d_str: st.markdown(f"<div class='cal-item-text' style='border-left-color:#10b981; background:#f0fdf4;'>PZ: {p.get('dostawca')}</div>", unsafe_allow_html=True)
        for d in dane["dyspozycje"]:
            if d.get('termin') == d_str: st.markdown(f"<div class='cal-item-text' style='border-left-color:#64748b; background:#f8fafc;'>D: {d.get('tytul')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. TABELE REALIZACJI (UJEDNOLICONE) ---
st.markdown('<div class="section-header">Zestawienie Realizacji</div>', unsafe_allow_html=True)
tabs = st.tabs(["Produkcja", "Odbiory", "Dostawy PZ", "Dyspozycje"])

def render_table(lista_danych, k_nazwa, k_szczeg, k_id, h_key):
    s1, s2, s3 = st.tabs(["Aktywne", "Do zaplanowania", "Historia"])
    def draw(data, planned=False):
        if not data: st.info("Brak wpisów."); return
        hc = st.columns([2.0, 1.0, 4.5, 1.2, 0.6])
        hc[0].markdown('<div class="label-text">Podmiot</div>', unsafe_allow_html=True)
        hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
        hc[2].markdown('<div class="label-text">Zarządzanie</div>', unsafe_allow_html=True)
        hc[3].markdown('<div class="label-text">Akcja</div>', unsafe_allow_html=True)
        for i, item in enumerate(data):
            st.markdown("<div style='padding:8px 0; border-bottom:1px solid #f1f5f9;'>", unsafe_allow_html=True)
            c = st.columns([2.0, 1.0, 4.5, 1.2, 0.6])
            status = item.get('status','W toku')
            st_cls = "status-done" if status=='Gotowe' else "status-process"
            c[0].markdown(f"<div class='data-text'>{item.get(k_nazwa)}</div><span class='badge {st_cls}'>{status}</span>", unsafe_allow_html=True)
            c[1].markdown(f"<div class='data-text'>{item.get('termin', 'BRAK')}</div>", unsafe_allow_html=True)
            u_id = f"{k_id}_{i}_{item.get('data_p','')}".replace('.','_')
            with c[2].popover("Szczegóły"):
                new_t = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                new_s = st.text_area("Treść", item.get(k_szczeg), key=f"s_{u_id}")
                if any(x in k_id for x in ["prod", "odb"]):
                    new_au = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(item.get('auto','Brak')), key=f"au_{u_id}")
                    new_kr = st.selectbox("Kurs", [1,2,3,4,5], int(item.get('kurs',1))-1, key=f"kr_{u_id}")
                    if st.button("Zapisz", key=f"sv_{u_id}"): item.update({"termin":new_t, k_szczeg:new_s, "auto":new_au, "kurs":new_kr}); zapisz_dane(dane); st.rerun()
                else:
                    if st.button("Zapisz", key=f"sv_{u_id}"): item.update({"termin":new_t, k_szczeg:new_s}); zapisz_dane(dane); st.rerun()
            if status != "Gotowe":
                if c[3].button("ZROBIONE", key=f"ok_{u_id}"): item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"send_{u_id}"): dane[h_key].append(data.pop(i)); zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"): data.pop(i); zapisz_dane(dane); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with s1: draw([z for z in lista_danych if str(z.get('termin','')).strip()])
    with s2: draw([z for z in lista_danych if not str(z.get('termin','')).strip()], True)
    with s3: st.dataframe(dane[h_key][::-1], use_container_width=True)

with tabs[0]: render_table(dane["w_realizacji"], "klient", "szczegoly", "prod", "zrealizowane")
with tabs[1]: render_table(dane["odbiory"], "miejsce", "towar", "odb", "odbiory_historia")
with tabs[2]: render_table(dane["przyjecia"], "dostawca", "towar", "pz", "przyjecia_historia")
with tabs[3]: render_table(dane["dyspozycje"], "tytul", "opis", "dysp", "dyspozycje_historia")
