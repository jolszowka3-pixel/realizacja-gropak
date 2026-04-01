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
/* Wspólne ustawienia przycisków */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button { 
    width: 100%; border-radius: 6px; min-height: 32px !important; height: 32px !important; 
    font-size: 12px; font-weight: 600; transition: all 0.2s ease-in-out;
    border: 1px solid #ced4da; padding: 0 10px; line-height: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* PRZYCISKI KOLOROWE */
button:contains("WYŚLIJ"), button:contains("OK"), button:contains("ZROBIONE"), button:contains("GOTOWE") {
    border: none !important; color: white !important; background-color: #28a745 !important;
}
button:contains("X") {
    border: none !important; color: white !important; background-color: #dc3545 !important; padding: 0 !important;
}
button:contains("Zapisz"), button:contains("Zaloguj"), button:contains("Opublikuj") {
    border: none !important; color: white !important; background-color: #007bff !important;
}

/* PASEK POWIADOMIEŃ (CO NOWEGO) */
.notification-container {
    background-color: #fff3cd;
    border: 2px solid #ffeeba;
    border-left: 10px solid #ffc107;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 25px;
}
.notif-title { font-weight: 900; color: #856404; font-size: 16px; margin-bottom: 8px; }
.notif-item { font-size: 13px; color: #856404; padding: 2px 0; border-bottom: 1px dashed #ffeeba; }

.main .block-container { padding-top: 2rem; }
.section-header { background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px; font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

/* KALENDARZ */
.day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 8px; padding-bottom: 4px; }
.day-name { font-weight: 700; font-size: 12px; color: #495057; text-transform: uppercase; }
.day-date { font-size: 11px; color: #868e96; }

.cal-entry-out, .cal-entry-ready, .cal-entry-in, .cal-entry-task, .cal-entry-return { 
    font-size: 10px; padding: 4px 6px; margin-bottom: 2px; border-radius: 3px; 
    font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; cursor: help; 
}
.cal-entry-out { background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; }
.cal-entry-ready { background: #d4edda; color: #155724; border-left: 3px solid #28a745; }
.cal-entry-return { background: #f3e5f5; color: #7b1fa2; border: 1px solid #7b1fa2; }
.cal-entry-in { background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; }
.cal-entry-task { background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; }

/* TABELE */
.badge-status-prod { background-color: #ffc107; color: #212529; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-ready { background-color: #28a745; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-return { background-color: #7b1fa2; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid #dee2e6; padding-bottom: 4px;}
.readonly-text { font-size: 13px; white-space: pre-wrap; color: #495057; line-height: 1.4; padding: 5px; background: #fdfdfd; border-radius: 4px; border: 1px solid #eee; }
.client-hover { cursor: help; border-bottom: 1px dotted #999; }

/* NOTATKA */
.note-card { background-color: #fff9c4; border-left: 5px solid #fbc02d; padding: 15px; border-radius: 4px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
.note-meta { font-size: 10px; color: #7f8c8d; margin-top: 8px; border-top: 1px solid #f0e68c; padding-top: 4px; }
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
        prio = 0 if item.get('pilne') else 1 
        try:
            t = str(item.get('termin', '')).strip().split('.')
            return (0, 2026, int(t[1]), int(t[0]), prio)
        except: return (1, 9999, 99, 99, prio)
    for k in ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]:
        if k in dane: dane[k].sort(key=sort_key)
    return dane

def wczytaj_dane():
    default = {
        "w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [], 
        "dyspozycje": [], "dyspozycje_historia": [], "odbiory": [], "odbiory_historia": [],
        "tablica": [], "uzytkownicy": {"admin": {"pass": "gropak2026", "role": "admin", "last_login": ""}}
    }
    client = get_gsheet_client()
    if not client: return default
    try:
        sh = client.open(GSHEET_NAME); ws = sh.get_worksheet(0); val = ws.acell('A1').value
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

# --- 3. SYSTEM LOGOWANIA Z PAMIĘCIĄ SESJI ---
if "user" not in st.session_state: st.session_state.user = None
if "prev_login" not in st.session_state: st.session_state.prev_login = ""
if "notif_seen" not in st.session_state: st.session_state.notif_seen = False

if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br><h3 style='text-align:center;'>GROPAK ERP</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("👤 Login"); p = st.text_input("🔒 Hasło", type="password")
            if st.form_submit_button("Zaloguj się do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p: 
                    # Zapisujemy poprzedni czas logowania PRZED aktualizacją
                    st.session_state.prev_login = dane["uzytkownicy"][u].get("last_login", "")
                    st.session_state.user = u
                    st.session_state.role = dane["uzytkownicy"][u].get("role", "edycja")
                    
                    # Aktualizujemy bazę o czas obecnego wejścia
                    dane["uzytkownicy"][u]["last_login"] = datetime.now().strftime("%d.%m %H:%M")
                    zapisz_dane(dane); st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

is_readonly = st.session_state.role == "wgląd"
can_edit = st.session_state.role in ["admin", "edycja"]

# --- 4. PASEK INFORMACJI O ZMIANACH (NOWOŚĆ) ---
if st.session_state.prev_login and not st.session_state.notif_seen:
    try:
        # Konwersja daty ostatniego logowania
        last_dt = datetime.strptime(st.session_state.prev_login, "%d.%m %H:%M").replace(year=2026)
        nowe_wpisy = []
        
        kategorie_notif = [
            ("w_realizacji", "Produkcja"), ("odbiory", "Odbiór"), 
            ("przyjecia", "Dostawa PZ"), ("dyspozycje", "Dyspozycja")
        ]
        
        for klucz, etykieta in kategorie_notif:
            for item in dane.get(klucz, []):
                try:
                    wpis_dt = datetime.strptime(item["data_p"], "%d.%m %H:%M").replace(year=2026)
                    if wpis_dt > last_dt:
                        nazwa = item.get("klient") or item.get("miejsce") or item.get("dostawca") or item.get("tytul")
                        nowe_wpisy.append(f"<b>{etykieta}</b>: {nazwa} (dodano {item['data_p']})")
                except: pass
        
        if nowe_wpisy:
            st.markdown('<div class="notification-container"><div class="notif-title">🔔 ZMIANY OD TWOJEJ OSTATNIEJ WIZYTY:</div>', unsafe_allow_html=True)
            # Wyświetlamy max 6 najnowszych
            for wpis in nowe_wpisy[:6]:
                st.markdown(f'<div class="notif-item">• {wpis}</div>', unsafe_allow_html=True)
            if st.button("Zrozumiałem, ukryj to powiadomienie"):
                st.session_state.notif_seen = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    except: pass

# --- 5. PANEL BOCZNY ---
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user}** (`{st.session_state.role.upper()}`)")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    if can_edit:
        typ = st.selectbox("Rodzaj:", ["Produkcja", "Odbiór (Powrót)", "Dostawa (PZ)", "Dyspozycja"])
        with st.form("f_add", clear_on_submit=True):
            if typ=="Produkcja":
                kl, tm, sz, au, kr, pi = st.text_input("Klient"), st.text_input("Termin"), st.text_area("Produkty"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5]), st.checkbox("PILNE")
                if st.form_submit_button("Zapisz"):
                    dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"pilne":pi,"status":"W produkcji","data_p":datetime.now().strftime("%d.%m %H:%M")})
                    zapisz_dane(dane); st.rerun()
            elif typ=="Odbiór (Powrót)":
                mj, tm, tw, au, kr = st.text_input("Skąd?"), st.text_input("Data"), st.text_area("Co?"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":au,"kurs":kr,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")})
                    zapisz_dane(dane); st.rerun()
            elif typ=="Dostawa (PZ)":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Data"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")})
                    zapisz_dane(dane); st.rerun()
            else:
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")})
                    zapisz_dane(dane); st.rerun()

# --- 6. TERMINARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
cn1, _, cn3 = st.columns([1,4,1])
if cn1.button("← Poprzedni"): st.session_state.wo -= 7; st.rerun()
if cn3.button("Następny →"): st.session_state.wo += 7; st.rerun()
start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
cols = st.columns(7)
for i in range(7):
    day = start + timedelta(days=i); d_str = day.strftime('%d.%m')
    with cols[i]:
        st.markdown(f"<div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{d_str}</div></div>", unsafe_allow_html=True)
        gr = {}
        for z in (dane["w_realizacji"] + dane["odbiory"]):
            if z.get('termin') == d_str:
                k = (z.get('auto','Brak'), z.get('kurs',1))
                if k not in gr: gr[k] = []
                gr[k].append(z)
        for (tr, kr), tasks in gr.items():
            all_r = all(t.get('status')=='Gotowe' for t in tasks if 'klient' in t)
            cl = "cal-entry-ready" if all_r else "cal-entry-out"
            tt = "&#10;".join([f"• {t.get('klient') or t.get('miejsce')}" for t in tasks]).replace('"', "&quot;")
            st.markdown(f"<div class='{cl}' title='{tt}'>{tr}/K{kr} ({len(tasks)})</div>", unsafe_allow_html=True)

# --- 7. TABELE REALIZACJI (UJEDNOLICONE) ---
st.markdown('<div class="section-header">Listy Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Szukaj we wszystkich wpisach...", "").lower()
tabs = st.tabs(["🏭 Produkcja", "🔄 Odbiory", "🚚 Przyjęcia PZ", "📋 Dyspozycje"])

def render_table(lista_zrodlowa, k_nazwa, k_szczegoly, k_id, mode):
    if not lista_zrodlowa: 
        st.info("Brak aktywnych wpisów.")
        return
    hc = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
    hc[0].markdown('<div class="label-text">Podmiot / Tytuł</div>', unsafe_allow_html=True)
    hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
    hc[2].markdown(f'<div class="label-text">{"Szczegóły" if is_readonly else "Zarządzanie"}</div>', unsafe_allow_html=True)
    hc[3].markdown(f'<div class="label-text">Akcja</div>', unsafe_allow_html=True)
    
    last_date = None
    for i, item in enumerate(lista_zrodlowa):
        ma_termin = bool(str(item.get('termin','')).strip())
        if mode == "produkcja" and not ma_termin: continue
        if mode == "plan" and ma_termin: continue
        if search and search not in str(item).lower(): continue
        
        curr_date = item.get('termin', '---')
        if curr_date != last_date and mode != "plan":
            st.markdown(f"<div class='table-group-header'>📅 {curr_date}</div>", unsafe_allow_html=True)
            last_date = curr_date
            
        c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
        status = item.get('status','W toku')
        badge = '<span class="badge-status-ready">✅ GOTOWE</span>' if status=='Gotowe' else '<span class="badge-status-prod">⏳ W TOKU</span>'
        if k_id == "odb": badge = '<span class="badge-status-return">🔄 ODBIÓR</span>'
        
        sz_safe = str(item.get(k_szczegoly, "")).replace('"', "&quot;").replace("'", "&apos;").replace("\n", " ")
        c[0].markdown(f"<span class='client-hover' title='{sz_safe}'>**{item.get(k_nazwa)}**</span><br>{badge}", unsafe_allow_html=True)
        c[1].write(item.get('termin', '---'))
        u_id = f"{k_id}_{i}_{item.get('data_p','')}".replace(':','').replace('.','_')
        
        if is_readonly:
            c[2].markdown(f"<div class='readonly-text'>{item.get(k_szczegoly,'-')}</div>", unsafe_allow_html=True)
        else:
            with c[2].popover("Edytuj"):
                if k_id == "prod": st.download_button("🖨️ Karta A4", generuj_html_do_druku(item), f"Karta_{u_id}.html", "text/html", key=f"dl_{u_id}")
                new_t = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                new_s = st.text_area("Szczegóły", item.get(k_szczegoly), key=f"s_{u_id}")
                if k_id in ["prod", "odb"]:
                    new_au = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(item.get('auto','Brak')), key=f"au_{u_id}")
                    new_kr = st.selectbox("Kurs", [1,2,3,4,5], int(item.get('kurs',1))-1, key=f"kr_{u_id}")
                    if st.button("Zapisz", key=f"sv_{u_id}"): item.update({"termin":new_t, k_szczegoly:new_s, "auto":new_au, "kurs":new_kr}); zapisz_dane(dane); st.rerun()
                elif st.button("Zapisz", key=f"sv_{u_id}"): item.update({"termin":new_t, k_szczegoly:new_s}); zapisz_dane(dane); st.rerun()
        
        if not is_readonly:
            if status != "Gotowe":
                if c[3].button("ZROBIONE" if k_id != "pz" else "OK", key=f"ok_{u_id}"): item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"send_{u_id}"):
                    h_key = {"prod":"zrealizowane", "odb":"odbiory_historia", "pz":"przyjecia_historia", "dysp":"dyspozycje_historia"}[k_id]
                    dane[h_key].append(lista_zrodlowa.pop(i)); zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"): lista_zrodlowa.pop(i); zapisz_dane(dane); st.rerun()

with tabs[0]:
    s1, s2, s3 = st.tabs(["Aktywne", "📂 Poczekalnia", "Historia"])
    with s1: render_table(dane["w_realizacji"], "klient", "szczegoly", "prod", "produkcja")
    with s2: render_table(dane["w_realizacji"], "klient", "szczegoly", "prod", "plan")
    with s3: st.dataframe(dane["zrealizowane"][::-1], use_container_width=True)
with tabs[1]:
    s1, s2 = st.tabs(["Aktywne", "Historia"])
    with s1: render_table(dane["odbiory"], "miejsce", "towar", "odb", "active")
    with s2: st.dataframe(dane["odbiory_historia"][::-1], use_container_width=True)
with tabs[2]:
    s1, s2 = st.tabs(["Aktywne", "Historia"])
    with s1: render_table(dane["przyjecia"], "dostawca", "towar", "pz", "active")
    with s2: st.dataframe(dane["przyjecia_historia"][::-1], use_container_width=True)
with tabs[3]:
    s1, s2 = st.tabs(["Aktywne", "Historia"])
    with s1: render_table(dane["dyspozycje"], "tytul", "opis", "dysp", "active")
    with s2: st.dataframe(dane["dyspozycje_historia"][::-1], use_container_width=True)

# --- 8. TABLICA OGŁOSZEŃ ---
st.markdown("<br><hr style='border: 2px solid #343a40;'><br>", unsafe_allow_html=True)
if can_edit:
    with st.form("bottom_note", clear_on_submit=True):
        nt = st.text_area("Dodaj ogłoszenie:"); 
        if st.form_submit_button("➕ Opublikuj"):
            if nt: dane["tablica"].append({"tresc": nt, "data": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()
if dane["tablica"]:
    nc = st.columns(3)
    for i, note in enumerate(reversed(dane["tablica"])):
        ridx = len(dane["tablica"])-1-i
        with nc[i % 3]:
            st.markdown(f"<div class='note-card'>{note['tresc']}<div class='note-meta'>{note['data']} | {note['autor']}</div></div>", unsafe_allow_html=True)
            if can_edit and st.button("Usuń", key=f"dn_{ridx}"): dane["tablica"].pop(ridx); zapisz_dane(dane); st.rerun()
