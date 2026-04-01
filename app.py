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

/* Globalne ustawienia typografii */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1e293b;
}

.main {
    background-color: #f8fafc;
}

/* Sidebar - Modern Dark Mode */
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

/* Profesjonalne Przyciski */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
    background-color: #ffffff !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 4px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    height: 36px !important;
    transition: all 0.2s ease;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}

.stButton>button:hover {
    border-color: #3b82f6 !important;
    color: #3b82f6 !important;
}

/* Przyciski Akcji (Primary) */
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

/* Etykiety Statusów (Badges) */
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

/* Kalendarz Tygodniowy */
.day-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px;
    min-height: 240px;
}
.day-header {
    text-align: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.day-name { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
.day-date { font-size: 15px; font-weight: 600; color: #1e293b; }

.cal-item {
    font-size: 10px;
    padding: 5px 8px;
    margin-bottom: 4px;
    border-radius: 4px;
    font-weight: 600;
    border-left: 3px solid #3b82f6;
    background: #f0f7ff;
    color: #1e40af;
}
.cal-item-done { border-left-color: #10b981; background: #f0fdf4; color: #166534; }

/* Tabela Realizacji */
.label-text { font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
.data-text { font-size: 13px; color: #1e293b; font-weight: 600; }
.details-box { background: #f8fafc; border: 1px solid #f1f5f9; padding: 10px; border-radius: 4px; font-size: 12px; color: #475569; line-height: 1.5; }

div[data-testid="stHorizontalBlock"] { align-items: flex-start !important; }
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
    except:
        return None

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        try:
            termin = str(item.get('termin', '')).strip()
            if not termin: return (2, 9999, 99, 99, 99, pilne)
            parts = termin.split('.')
            d, m = int(parts[0]), int(parts[1])
            return (0, 2026, m, d, t_score, pilne)
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
    except Exception as e:
        st.error(f"Sync error: {e}")

dane = wczytaj_dane()

# --- 3. FUNKCJE POMOCNICZE ---
def generuj_html_do_druku(z):
    auto_val = z.get('auto', 'Brak'); k_val = z.get('kurs', 1); transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    return f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:30px;}} .card{{border:5px solid black;padding:30px;}} h1{{text-align:center;border-bottom:3px solid black;}} .row{{display:flex;justify-content:space-between;margin-top:20px;font-size:20px;}} .box{{border:1px solid #666;padding:15px;margin-top:20px;min-height:300px;font-size:20px;white-space:pre-wrap;line-height:1.4;}}</style></head><body onload="window.print()"><div class="card"><h1>Zlecenie: {z.get('klient')}</h1><div class="row"><div><b>Termin:</b> {z.get('termin')}</div><div><b>Transport:</b> {transport_str}</div></div><p><b>SZCZEGÓŁY:</b></p><div class="box">{z.get('szczegoly')}</div><div style="margin-top:50px;text-align:right;">Podpis: __________________________</div></div></body></html>"""

def generuj_rozpiske_zbiorcza(data_cel, lista_zlecen, lista_odbiorow):
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:20px;}} .h1{{text-align:center;border-bottom:4px solid #000;}} .transport-title{{background:#f8f9fa;padding:10px;border:2px solid #000;margin:10px 0;}} table{{width:100%;border-collapse:collapse;}} th, td{{border:1px solid #000;padding:8px;text-align:left;}} .details{{white-space:pre-wrap;}}</style></head><body onload="window.print()"><div class="h1"><h1>PLAN TRANSPORTU - {data_cel}</h1></div>"""
    z_dnia = [z for z in lista_zlecen if z.get('termin') == data_cel]; o_dnia = [o for o in lista_odbiorow if o.get('termin') == data_cel]
    grupy = {}
    for z in z_dnia:
        k = (z.get('auto', 'Brak'), z.get('kurs', 1))
        if k not in grupy: grupy[k] = {"prod": [], "odb": []}
        grupy[k]["prod"].append(z)
    for o in o_dnia:
        k = (o.get('auto', 'Brak'), o.get('kurs', 1))
        if k not in grupy: grupy[k] = {"prod": [], "odb": []}
        grupy[k]["odb"].append(o)
    if not grupy: html += f"<h2 style='text-align:center;'>Brak zadań na dzień {data_cel}.</h2>"
    else:
        for (tr, kr), content in grupy.items():
            html += f"<div class='transport-title'>TR: {tr} / KURS {kr}</div><table><tr><th style='width:30%'>KONTRAHENT</th><th>SZCZEGÓŁY</th></tr>"
            for it in content["prod"]: html += f"<tr><td><b>{it.get('klient')}</b></td><td class='details'>{it.get('szczegoly')}</td></tr>"
            for it in content["odb"]: html += f"<tr><td><b>ODBIÓR: {it.get('miejsce')}</b></td><td class='details'>{it.get('towar')}</td></tr>"
            html += "</table>"
    html += "</body></html>"; return html

# --- 4. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = "wgląd"

if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br><h3 style='text-align:center; color:#0f172a;'>GROPAK ERP</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Użytkownik"); p = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p: 
                    st.session_state.user, st.session_state.role = u, dane["uzytkownicy"][u]["role"]
                    dane["uzytkownicy"][u]["last_login"] = datetime.now().strftime("%d.%m %H:%M")
                    zapisz_dane(dane); st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

is_readonly = st.session_state.role == "wgląd"
can_edit = st.session_state.role in ["admin", "edycja"]
is_admin = st.session_state.role == "admin"

# --- 5. PANEL BOCZNY ---
with st.sidebar:
    st.markdown("<div style='padding:10px 0;'><h4 style='color:white; margin:0;'>GROPAK ERP</h4></div>", unsafe_allow_html=True)
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    
    if is_admin:
        with st.expander("Użytkownicy"):
            with st.form("add_u_f", clear_on_submit=True):
                nu, np, nr = st.text_input("Login"), st.text_input("Hasło"), st.selectbox("Rola", ["edycja","wgląd","admin"])
                if st.form_submit_button("Dodaj"):
                    if nu: dane["uzytkownicy"][nu] = {"pass": np, "role": nr, "last_login": ""}; zapisz_dane(dane); st.rerun()
            for usr, info in dane["uzytkownicy"].items():
                c1, c2, c3 = st.columns([2,1.2,0.8]); c1.write(f"{usr}")
                with c2.popover("Edytuj"):
                    ep = st.text_input("Hasło", info["pass"], key=f"up_{usr}")
                    er = st.selectbox("Rola", ["edycja","wgląd","admin"], ["edycja","wgląd","admin"].index(info["role"]), key=f"ur_{usr}")
                    if st.button("Zapisz", key=f"us_{usr}"): dane["uzytkownicy"][usr].update({"pass": ep, "role": er}); zapisz_dane(dane); st.rerun()
                if usr != "admin":
                    if c3.button("X", key=f"del_{usr}"): del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()

    if can_edit:
        st.markdown('<div style="color:white; font-size:11px; font-weight:700; letter-spacing:1px; margin-bottom:10px;">NOWY WPIS</div>', unsafe_allow_html=True)
        typ = st.selectbox("Kategoria:", ["Produkcja", "Odbiór", "Dostawa PZ", "Dyspozycja"])
        with st.form("f_add", clear_on_submit=True):
            if typ=="Produkcja":
                kl, tm, sz, au, kr, pi = st.text_input("Klient"), st.text_input("Termin (DD.MM)"), st.text_area("Szczegóły"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5]), st.checkbox("Priorytet")
                if st.form_submit_button("Zapisz"):
                    if kl: dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"pilne":pi,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ=="Odbiór":
                mj, tm, tw, au, kr = st.text_input("Miejsce"), st.text_input("Termin"), st.text_area("Towar"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    if mj: dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":au,"kurs":kr,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ=="Dostawa PZ":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Termin"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    if ds: dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ=="Dyspozycja":
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    if ty: dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
    
    st.divider()
    data_druk = st.text_input("Plan transportu na:", value=datetime.now().strftime("%d.%m"))
    st.download_button("Pobierz rozpiskę", data=generuj_rozpiske_zbiorcza(data_druk, dane["w_realizacji"], dane["odbiory"]), file_name=f"Plan_{data_druk}.html", mime="text/html")

# --- 6. HARMONOGRAM TYGODNIOWY ---
st.markdown('<div class="section-header">Harmonogram Operacyjny</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
cn1, _, cn3 = st.columns([1,4,1])
if cn1.button("Poprzedni"): st.session_state.wo -= 7; st.rerun()
if cn3.button("Następny"): st.session_state.wo += 7; st.rerun()
start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
cols = st.columns(7)
for i in range(7):
    day = start + timedelta(days=i); d_str = day.strftime('%d.%m')
    with cols[i]:
        st.markdown(f"<div class='day-card'><div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{d_str}</div></div>", unsafe_allow_html=True)
        for z in dane["w_realizacji"]:
            if z.get('termin') == d_str:
                cl = "cal-item-done" if z.get('status') == 'Gotowe' else "cal-item"
                st.markdown(f"<div class='{cl}'>{z.get('klient')} ({z.get('auto')})</div>", unsafe_allow_html=True)
        for o in dane["odbiory"]:
            if o.get('termin') == d_str:
                st.markdown(f"<div class='cal-item' style='border-left-color:#7c3aed; background:#f5f3ff; color:#5b21b6;'>Odb: {o.get('miejsce')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. TABELE REALIZACJI (UJEDNOLICONE) ---
st.markdown('<div class="section-header">Zestawienie Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("Szukaj we wszystkich wpisach...", "").lower()

def renderuj_tabele_ujednolicona(lista_danych, klucz_nazwa, klucz_szczegoly, klucz_id, typ_sekcji):
    if not lista_danych: 
        st.info("Brak aktywnych wpisów.")
        return
    
    hc = st.columns([2.0, 1.0, 4.5, 1.2, 0.6])
    hc[0].markdown('<div class="label-text">Podmiot / Status</div>', unsafe_allow_html=True)
    hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
    hc[2].markdown('<div class="label-text">Szczegóły / Zarządzanie</div>', unsafe_allow_html=True)
    hc[3].markdown('<div class="label-text">Akcja</div>', unsafe_allow_html=True)
    
    last_date = None
    for i, item in enumerate(lista_danych):
        if search and search not in str(item).lower(): continue
        
        curr_date = item.get('termin', '').strip()
        if curr_date and curr_date != last_date and typ_sekcji != "planned":
            st.markdown(f"<div style='background:#f1f5f9; padding:6px 12px; border-radius:4px; margin-top:16px; font-size:11px; font-weight:700; color:#475569;'>Termin: {curr_date}</div>", unsafe_allow_html=True)
            last_date = curr_date

        st.markdown("<div style='padding:12px 0; border-bottom:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        c = st.columns([2.0, 1.0, 4.5, 1.2, 0.6])
        status = item.get('status','W toku')
        st_cls = "status-done" if status=='Gotowe' else "status-process"
        
        c[0].markdown(f"<div class='data-text'>{item.get(klucz_nazwa)}</div><span class='badge {st_cls}'>{status}</span>", unsafe_allow_html=True)
        c[1].markdown(f"<div class='data-text'>{item.get('termin', 'BRAK')}</div>", unsafe_allow_html=True)
        
        u_id = f"{klucz_id}_{i}_{item.get('data_p','')}".replace(':','').replace(' ','_').replace('.','_')
        if is_readonly:
            c[2].markdown(f"<div class='details-box'>{item.get(klucz_szczegoly,'-')}</div>", unsafe_allow_html=True)
        else:
            with c[2].popover("Szczegóły i Edycja"):
                if "prod" in klucz_id:
                    st.download_button("Karta A4", generuj_html_do_druku(item), f"Karta_{u_id}.html", "text/html", key=f"dl_{u_id}")
                new_t = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                new_s = st.text_area("Treść", item.get(klucz_szczegoly), key=f"s_{u_id}")
                if any(x in klucz_id for x in ["prod", "odb"]):
                    new_au = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(item.get('auto','Brak')), key=f"au_{u_id}")
                    new_kr = st.selectbox("Kurs", [1,2,3,4,5], int(item.get('kurs',1))-1, key=f"kr_{u_id}")
                    if st.button("Zaktualizuj", key=f"sv_{u_id}"):
                        item.update({"termin":new_t, klucz_szczegoly:new_s, "auto":new_au, "kurs":new_kr}); zapisz_dane(dane); st.rerun()
                else:
                    if st.button("Zaktualizuj", key=f"sv_{u_id}"):
                        item.update({"termin":new_t, klucz_szczegoly:new_s}); zapisz_dane(dane); st.rerun()
        
        if not is_readonly:
            if status != "Gotowe":
                if c[3].button("ZROBIONE", key=f"ok_{u_id}"):
                    item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"send_{u_id}"):
                    h_map = {"prod":"zrealizowane", "odb":"odbiory_historia", "pz":"przyjecia_historia", "dysp":"dyspozycje_historia"}
                    h_key = h_map.get(klucz_id.split('_')[0], "zrealizowane")
                    dane[h_key].append(lista_danych.pop(i)); zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"):
                lista_danych.pop(i); zapisz_dane(dane); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

tabs = st.tabs(["Produkcja", "Odbiory", "Dostawy PZ", "Dyspozycje"])

with tabs[0]: # PRODUKCJA
    s1, s2, s3 = st.tabs(["Aktywne", "Do zaplanowania", "Historia"])
    with s1: renderuj_tabele_ujednolicona([z for z in dane["w_realizacji"] if str(z.get('termin','')).strip()], "klient", "szczegoly", "prod_act", "active")
    with s2: renderuj_tabele_ujednolicona([z for z in dane["w_realizacji"] if not str(z.get('termin','')).strip()], "klient", "szczegoly", "prod_plan", "planned")
    with s3: st.dataframe(dane["zrealizowane"][::-1], use_container_width=True)

with tabs[1]: # ODBIORY
    s1, s2, s3 = st.tabs(["Aktywne", "Do zaplanowania", "Historia"])
    with s1: renderuj_tabele_ujednolicona([z for z in dane["odbiory"] if str(z.get('termin','')).strip()], "miejsce", "towar", "odb_act", "active")
    with s2: renderuj_tabele_ujednolicona([z for z in dane["odbiory"] if not str(z.get('termin','')).strip()], "miejsce", "towar", "odb_plan", "planned")
    with s3: st.dataframe(dane["odbiory_historia"][::-1], use_container_width=True)

with tabs[2]: # DOSTAWY PZ
    s1, s2, s3 = st.tabs(["Aktywne", "Do zaplanowania", "Historia"])
    with s1: renderuj_tabele_ujednolicona([z for z in dane["przyjecia"] if str(z.get('termin','')).strip()], "dostawca", "towar", "pz_act", "active")
    with s2: renderuj_tabele_ujednolicona([z for z in dane["przyjecia"] if not str(z.get('termin','')).strip()], "dostawca", "towar", "pz_plan", "planned")
    with s3: st.dataframe(dane["przyjecia_historia"][::-1], use_container_width=True)

with tabs[3]: # DYSPOZYCJE
    s1, s2, s3 = st.tabs(["Aktywne", "Do zaplanowania", "Historia"])
    with s1: renderuj_tabele_ujednolicona([z for z in dane["dyspozycje"] if str(z.get('termin','')).strip()], "tytul", "opis", "dysp_act", "active")
    with s2: renderuj_tabele_ujednolicona([z for z in dane["dyspozycje"] if not str(z.get('termin','')).strip()], "tytul", "opis", "dysp_plan", "planned")
    with s3: st.dataframe(dane["dyspozycje_historia"][::-1], use_container_width=True)

# --- 8. KOMUNIKATY ---
st.markdown('<div class="section-header">Komunikaty Wewnętrzne</div>', unsafe_allow_html=True)
if can_edit:
    with st.form("bottom_note", clear_on_submit=True):
        nowa_tresc = st.text_area("Dodaj ogłoszenie:")
        if st.form_submit_button("Opublikuj"):
            if nowa_tresc: dane["tablica"].append({"tresc": nowa_tresc, "data": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()

if not dane["tablica"]: st.info("Brak aktywnych ogłoszeń.")
else:
    nc = st.columns(3)
    for i, note in enumerate(reversed(dane["tablica"])):
        ridx = len(dane["tablica"])-1-i
        with nc[i % 3]:
            st.markdown(f"<div style='background:white; border:1px solid #e2e8f0; padding:16px; border-radius:6px; margin-bottom:12px; box-shadow:0 1px 2px rgba(0,0,0,0.05);'>{note['tresc']}<div style='font-size:10px; color:#94a3b8; margin-top:12px; border-top:1px solid #f1f5f9; padding-top:6px;'>{note['data']} | {note['autor']}</div></div>", unsafe_allow_html=True)
            if is_admin:
                if st.button("Usuń", key=f"dn_{ridx}"): dane["tablica"].pop(ridx); zapisz_dane(dane); st.rerun()
