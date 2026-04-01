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
/* Import czcionki Inter dla nowoczesnego wyglądu */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Główne tło i kontenery */
.main {
    background-color: #f9fafb;
}

.stApp {
    color: #111827;
}

/* Profesjonalne przyciski */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
    background-color: #ffffff !important;
    color: #374151 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    height: 36px !important;
    transition: all 0.2s;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}

.stButton>button:hover {
    border-color: #3b82f6 !important;
    color: #3b82f6 !important;
    background-color: #f0f9ff !important;
}

/* Przyciski akcji (Zapisz/Wyślij) - subtelny niebieski */
button:contains("Zapisz"), button:contains("WYŚLIJ"), button:contains("ZROBIONE"), button:contains("Zaloguj") {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
}

button:contains("Zapisz"):hover, button:contains("WYŚLIJ"):hover {
    background-color: #1d4ed8 !important;
}

/* Sekcje i Nagłówki */
.section-header {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
    padding-bottom: 8px;
    margin-bottom: 20px;
    border-bottom: 2px solid #e5e7eb;
}

/* Tabele i wiersze */
.table-group-header {
    background-color: #f3f4f6;
    color: #4b5563;
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-radius: 4px;
    margin: 20px 0 10px 0;
}

/* Statusy bez emotikon */
.badge-status {
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}
.status-work { background-color: #fef3c7; color: #92400e; }
.status-ready { background-color: #d1fae5; color: #065f46; }
.status-neutral { background-color: #e5e7eb; color: #374151; }

/* Kalendarz - czysta siatka */
.day-col {
    border: 1px solid #e5e7eb;
    background: white;
    padding: 10px;
    min-height: 200px;
}
.day-header {
    text-align: center;
    background: #f9fafb;
    padding: 5px;
    border-bottom: 1px solid #e5e7eb;
    font-weight: 600;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111827 !important;
}
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {
    color: #f9fafb !important;
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
        st.error(f"Błąd autoryzacji: {e}")
        return None

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        k_score = item.get('kurs', 1)
        status_score = 1 if item.get('status') == 'Gotowe' else 0 
        try:
            termin = str(item.get('termin', '')).strip()
            if not termin: return (2, 9999, 99, 99, 99, 99, 99, pilne)
            parts = termin.split('.')
            d, m = int(parts[0]), int(parts[1])
            y = int(parts[2]) if len(parts) > 2 else 2026
            return (0, y, m, d, t_score, k_score, status_score, pilne)
        except: return (1, 9999, 99, 99, 99, 99, 99, pilne)
    for k in ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]:
        if k in dane: dane[k].sort(key=sort_key)
    return dane

def wczytaj_dane():
    default_dane = {
        "w_realizacji": [], "zrealizowane": [], 
        "przyjecia": [], "przyjecia_historia": [], 
        "dyspozycje": [], "dyspozycje_historia": [], 
        "odbiory": [], "odbiory_historia": [],
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
        st.error(f"Błąd zapisu: {e}")

dane = wczytaj_dane()

# --- 3. FUNKCJE POMOCNICZE ---
def generuj_html_do_druku(z):
    auto_val = z.get('auto', 'Brak'); k_val = z.get('kurs', 1); transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    return f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:30px;}} .card{{border:5px solid black;padding:30px;}} h1{{text-align:center;border-bottom:3px solid black;}} .row{{display:flex;justify-content:space-between;margin-top:20px;font-size:20px;}} .box{{border:1px solid #666;padding:15px;margin-top:20px;min-height:300px;font-size:20px;white-space:pre-wrap;line-height:1.4;}}</style></head><body onload="window.print()"><div class="card"><h1>Karta Zlecenia: {z.get('klient')}</h1><div class="row"><div><b>Termin:</b> {z.get('termin')}</div><div><b>Transport:</b> {transport_str}</div></div><p><b>PRODUKTY / SZCZEGÓŁY:</b></p><div class="box">{z.get('szczegoly')}</div><div style="margin-top:50px;text-align:right;">Podpis: __________________________</div></div></body></html>"""

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
            html += f"<div class='transport-title'>🚚 {tr} / KURS {kr}</div><table><tr><th style='width:30%'>KLIENT / DOSTAWCA</th><th>PRODUKTY / UWAGI</th></tr>"
            for it in content["prod"]: html += f"<tr><td><b>{it.get('klient')}</b></td><td class='details'>{it.get('szczegoly')}</td></tr>"
            for it in content["odb"]: html += f"<tr><td><b>🔄 ODBIÓR: {it.get('miejsce')}</b></td><td class='details'>{it.get('towar')}</td></tr>"
            html += "</table>"
    html += "</body></html>"; return html

# --- 4. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = "wgląd"
if "prev_login" not in st.session_state: st.session_state.prev_login = ""
if "notif_seen" not in st.session_state: st.session_state.notif_seen = False

if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo.png", use_container_width=True)
        except: st.title("GROPAK ERP")
        with st.form("login_form"):
            u = st.text_input("👤 Login"); p = st.text_input("🔒 Hasło", type="password")
            if st.form_submit_button("Zaloguj się do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p: 
                    st.session_state.user = u
                    st.session_state.role = dane["uzytkownicy"][u]["role"]
                    st.session_state.prev_login = dane["uzytkownicy"][u].get("last_login", "")
                    dane["uzytkownicy"][u]["last_login"] = datetime.now().strftime("%d.%m %H:%M")
                    zapisz_dane(dane); st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

is_readonly = st.session_state.role == "wgląd"
can_edit = st.session_state.role in ["admin", "edycja"]
is_admin = st.session_state.role == "admin"

# --- 5. PANEL BOCZNY ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    st.write(f"Zalogowany: **{st.session_state.user}** (`{st.session_state.role.upper()}`)")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    
    if is_admin:
        with st.expander("👥 Zarządzanie użytkownikami"):
            with st.form("add_u_f", clear_on_submit=True):
                nu, np, nr = st.text_input("Login"), st.text_input("Hasło"), st.selectbox("Rola", ["edycja","wgląd","admin"])
                if st.form_submit_button("Dodaj"):
                    if nu: dane["uzytkownicy"][nu] = {"pass": np, "role": nr, "last_login": ""}; zapisz_dane(dane); st.rerun()
            for usr, info in dane["uzytkownicy"].items():
                c1, c2, c3 = st.columns([2,1.2,0.8]); c1.write(f"**{usr}**")
                with c2.popover("Edytuj"):
                    ep = st.text_input("Hasło", info["pass"], key=f"up_{usr}")
                    er = st.selectbox("Rola", ["edycja","wgląd","admin"], ["edycja","wgląd","admin"].index(info["role"]), key=f"ur_{usr}")
                    if st.button("💾 Zapisz", key=f"us_{usr}"): dane["uzytkownicy"][usr].update({"pass": ep, "role": er}); zapisz_dane(dane); st.rerun()
                if usr != "admin":
                    if c3.button("X", key=f"del_{usr}"): del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()
        with st.expander("🛠️ Korekta Historii"):
            kat = st.selectbox("Dział:", ["Produkcja", "Odbiory", "Przyjęcia", "Dyspozycje"])
            src = {"Produkcja": "zrealizowane", "Odbiory": "odbiory_historia", "Przyjęcia": "przyjecia_historia", "Dyspozycje": "dyspozycje_historia"}[kat]
            dest = {"Produkcja": "w_realizacji", "Odbiory": "odbiory", "Przyjęcia": "przyjecia", "Dyspozycje": "dyspozycje"}[kat]
            for i, item in enumerate(dane[src]):
                nm = item.get("klient") or item.get("miejsce") or item.get("dostawca") or item.get("tytul")
                st.write(f"• {nm}"); c1, c2 = st.columns(2)
                if c1.button("↩️ Przywróć", key=f"rev_{src}_{i}"): dane[dest].append(dane[src].pop(i)); zapisz_dane(dane); st.rerun()
                if c2.button("❌ Usuń", key=f"fdel_{src}_{i}"): dane[src].pop(i); zapisz_dane(dane); st.rerun()
    
    if can_edit:
        st.markdown('<div class="sidebar-header">➕ NOWY WPIS</div>', unsafe_allow_html=True)
        typ = st.selectbox("Rodzaj:", ["Produkcja", "Odbiór (Powrót)", "Dostawa (PZ)", "Dyspozycja"])
        with st.form("f_add"):
            if typ=="Produkcja":
                kl, tm, sz, au, kr, pi = st.text_input("Klient"), st.text_input("Termin"), st.text_area("Produkty"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5]), st.checkbox("PILNE")
                if st.form_submit_button("Zapisz"):
                    if kl: dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"pilne":pi,"status":"W produkcji","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ=="Odbiór (Powrót)":
                mj, tm, tw, au, kr = st.text_input("Skąd?"), st.text_input("Data"), st.text_area("Co?"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    if mj: dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":au,"kurs":kr,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ=="Dostawa (PZ)":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Data"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    if ds: dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            else:
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    if ty: dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
    
    st.markdown('<div class="sidebar-print-header">🖨️ DRUKOWANIE PLANU</div>', unsafe_allow_html=True)
    data_druk = st.text_input("Podaj datę (np. 31.03):", value=datetime.now().strftime("%d.%m"))
    st.download_button("📥 Pobierz Rozpiskę Dnia", data=generuj_rozpiske_zbiorcza(data_druk, dane["w_realizacji"], dane["odbiory"]), file_name=f"Plan_{data_druk}.html", mime="text/html")
    if is_admin:
        st.divider()
        if st.button("🔥 RESET DANYCH"): 
            for k in ["w_realizacji","zrealizowane","przyjecia","przyjecia_historia","dyspozycje","dyspozycje_historia","odbiory","odbiory_historia","tablica"]: dane[k] = []
            zapisz_dane(dane); st.rerun()

# --- 6. POWIADOMIENIA ---
if st.session_state.prev_login and not st.session_state.notif_seen:
    try:
        p_dt = datetime.strptime(st.session_state.prev_login, "%d.%m %H:%M").replace(year=2026)
        nowe = []
        for k, lbl in [("w_realizacji","📦 Prod"), ("odbiory","🔄 Odbiór"), ("przyjecia","🚚 PZ"), ("dyspozycje","📋 Dysp")]:
            for item in dane[k]:
                try:
                    i_dt = datetime.strptime(item["data_p"], "%d.%m %H:%M").replace(year=2026)
                    if i_dt > p_dt:
                        nm = item.get("klient") or item.get("miejsce") or item.get("dostawca") or item.get("tytul")
                        nowe.append(f"• <b>{lbl}</b>: {nm} (dodano {item['data_p']})")
                except: pass
        if nowe:
            st.markdown(f'<div class="notification-container"><div class="notif-title">🔔 NOWOŚCI OD OSTATNIEJ WIZYTY:</div>', unsafe_allow_html=True)
            for n in nowe[:6]: st.markdown(f'<div class="notif-item">{n}</div>', unsafe_allow_html=True)
            if st.button("Zrozumiałem, ukryj"): st.session_state.notif_seen = True; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    except: pass

# --- 7. TERMINARZ TYGODNIOWY ---
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
        for z in dane["w_realizacji"]:
            try:
                parts = z.get('termin','').split('.'); zd, zm = int(parts[0]), int(parts[1])
                if zd == day.day and zm == day.month:
                    k = (z.get('auto','Brak'), z.get('kurs',1)); 
                    if k not in gr: gr[k] = {"p":[], "o":[]}
                    gr[k]["p"].append(z)
            except: pass
        for o in dane["odbiory"]:
            try:
                parts = o.get('termin','').split('.'); zd, zm = int(parts[0]), int(parts[1])
                if zd == day.day and zm == day.month:
                    k = (o.get('auto','Brak'), o.get('kurs',1)); 
                    if k not in gr: gr[k] = {"p":[], "o":[]}
                    gr[k]["o"].append(o)
            except: pass
        for (tr, kr), cnt in gr.items():
            all_r = all(it.get('status')=='Gotowe' for it in cnt["p"])
            cl = "cal-entry-ready" if (all_r and cnt["p"]) else "cal-entry-out"
            lbl = f"{tr}/K{kr}" if tr in ["Auto 1","Auto 2"] else tr
            tooltip = "ZLECENIA:&#10;"
            for it in cnt["p"]: tooltip += f"• {it.get('klient')} ({it.get('szczegoly','')[:20]})&#10;"
            if cnt["o"]:
                tooltip += "&#10;🔄 ODBIORY:&#10;"
                for it in cnt["o"]: tooltip += f"• {it.get('miejsce')} ({it.get('towar','')[:20]})&#10;"
            st.markdown(f"<div class='{cl}' title='{tooltip}'>{lbl} ({len(cnt['p'])+len(cnt['o'])})</div>", unsafe_allow_html=True)
            if cnt["o"]: st.markdown(f"<div class='cal-entry-return' style='height:3px; margin-top:-4px;'></div>", unsafe_allow_html=True)
        for p in dane["przyjecia"]:
            try:
                parts = p.get('termin','').split('.'); pd, pm = int(parts[0]), int(parts[1])
                if pd == day.day and pm == day.month: st.markdown(f"<div class='cal-entry-in' title='{p.get('towar')}'>P: {p.get('dostawca')}</div>", unsafe_allow_html=True)
            except: pass
        for d in dane["dyspozycje"]:
            try:
                parts = d.get('termin','').split('.'); dd, dm = int(parts[0]), int(parts[1])
                if dd == day.day and dm == day.month: st.markdown(f"<div class='cal-entry-task' title='{d.get('opis')}'>D: {d.get('tytul')}</div>", unsafe_allow_html=True)
            except: pass

# --- 8. TABELE REALIZACJI (UJEDNOLICONE) ---
st.markdown('<div class="section-header">Listy Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Szukaj we wszystkich wpisach...", "").lower()
tabs = st.tabs(["🏭 Produkcja", "🔄 Odbiory", "🚚 Przyjęcia PZ", "📋 Dyspozycje"])

def renderuj_tabele_ujednolicona(lista_danych, klucz_nazwa, klucz_szczegoly, klucz_id, typ_sekcji):
    if not lista_danych: 
        st.info("Brak aktywnych wpisów.")
        return
    hc = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
    hc[0].markdown('<div class="label-text">Podmiot / Tytuł</div>', unsafe_allow_html=True)
    hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
    hc[2].markdown(f'<div class="label-text">{"Szczegóły" if is_readonly else "Menu Edycji"}</div>', unsafe_allow_html=True)
    hc[3].markdown(f'<div class="label-text">{"Status" if is_readonly else "Akcja"}</div>', unsafe_allow_html=True)
    last_date = None
    for i, item in enumerate(lista_danych):
        if not str(item.get('termin','')).strip() and typ_sekcji != "planned": continue
        if search and search not in str(item).lower(): continue
        curr_date = item.get('termin')
        if curr_date != last_date:
            st.markdown(f"<div class='table-group-header'>📅 {curr_date}</div>", unsafe_allow_html=True)
            last_date = curr_date
        c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
        status = item.get('status','W toku')
        badge = '<span class="badge-status-ready">✅ GOTOWE</span>' if status=='Gotowe' else '<span class="badge-status-prod">⏳ W TOKU</span>'
        if typ_sekcji == "odbiory": badge = '<span class="badge-status-return">🔄 ODBIÓR</span>'
        c[0].markdown(f"**{item.get(klucz_nazwa)}**<br>{badge}", unsafe_allow_html=True)
        c[1].write(item.get('termin', '---'))
        u_id = f"{klucz_id}_{i}_{item.get('data_p','')}".replace(':','').replace(' ','_').replace('.','_')
        if is_readonly:
            c[2].markdown(f"<div class='readonly-text'>{item.get(klucz_szczegoly,'-')}</div>", unsafe_allow_html=True)
        else:
            with c[2].popover("Edytuj"):
                if typ_sekcji == "produkcja":
                    st.download_button("🖨️ Karta A4", generuj_html_do_druku(item), f"Karta_{u_id}.html", "text/html", key=f"dl_{u_id}")
                new_t = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                new_s = st.text_area("Szczegóły", item.get(klucz_szczegoly), key=f"s_{u_id}")
                if typ_sekcji in ["produkcja", "odbiory"]:
                    new_au = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(item.get('auto','Brak')), key=f"au_{u_id}")
                    new_kr = st.selectbox("Kurs", [1,2,3,4,5], int(item.get('kurs',1))-1, key=f"kr_{u_id}")
                    if st.button("Zapisz", key=f"sv_{u_id}"):
                        item.update({"termin":new_t, klucz_szczegoly:new_s, "auto":new_au, "kurs":new_kr})
                        zapisz_dane(dane); st.rerun()
                else:
                    if st.button("Zapisz", key=f"sv_{u_id}"):
                        item.update({"termin":new_t, klucz_szczegoly:new_s}); zapisz_dane(dane); st.rerun()
        if not is_readonly:
            if status != "Gotowe":
                if c[3].button("ZROBIONE" if typ_sekcji != "przyjecia" else "OK", key=f"ok_{u_id}"):
                    item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"send_{u_id}"):
                    hist_key = {"produkcja":"zrealizowane", "odbiory":"odbiory_historia", "przyjecia":"przyjecia_historia", "dyspozycje":"dyspozycje_historia"}[typ_sekcji]
                    dane[hist_key].append(lista_danych.pop(i)); zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"):
                lista_danych.pop(i); zapisz_dane(dane); st.rerun()

with tabs[0]:
    sub1, sub2, sub3 = st.tabs(["Aktywne", "📂 Do zaplanowania", "Historia"])
    with sub1: renderuj_tabele_ujednolicona([z for z in dane["w_realizacji"] if str(z.get('termin','')).strip()], "klient", "szczegoly", "prod", "produkcja")
    with sub2: renderuj_tabele_ujednolicona([z for z in dane["w_realizacji"] if not str(z.get('termin','')).strip()], "klient", "szczegoly", "plan", "planned")
    with sub3: st.dataframe(dane["zrealizowane"][::-1], use_container_width=True)
with tabs[1]:
    sub1, sub2 = st.tabs(["Aktywne", "Historia"])
    with sub1: renderuj_tabele_ujednolicona(dane["odbiory"], "miejsce", "towar", "odb", "odbiory")
    with sub2: st.dataframe(dane["odbiory_historia"][::-1], use_container_width=True)
with tabs[2]:
    sub1, sub2 = st.tabs(["Aktywne", "Historia"])
    with sub1: renderuj_tabele_ujednolicona(dane["przyjecia"], "dostawca", "towar", "pz", "przyjecia")
    with sub2: st.dataframe(dane["przyjecia_historia"][::-1], use_container_width=True)
with tabs[3]:
    sub1, sub2 = st.tabs(["Aktywne", "Historia"])
    with sub1: renderuj_tabele_ujednolicona(dane["dyspozycje"], "tytul", "opis", "dysp", "dyspozycje")
    with sub2: st.dataframe(dane["dyspozycje_historia"][::-1], use_container_width=True)

# --- 9. TABLICA OGŁOSZEŃ ---
st.markdown("<br><hr style='border: 2px solid #343a40;'><br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📌 Tablica Ogłoszeń</div>', unsafe_allow_html=True)
if can_edit:
    with st.form("bottom_note", clear_on_submit=True):
        nowa_tresc = st.text_area("Dodaj ogłoszenie:")
        if st.form_submit_button("➕ Opublikuj"):
            if nowa_tresc: dane["tablica"].append({"tresc": nowa_tresc, "data": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()
if not dane["tablica"]: st.info("Brak ogłoszeń.")
else:
    nc = st.columns(3)
    for i, note in enumerate(reversed(dane["tablica"])):
        ridx = len(dane["tablica"])-1-i
        with nc[i % 3]:
            st.markdown(f"<div class='note-card'>{note['tresc']}<div class='note-meta'>{note['data']} | {note['autor']}</div></div>", unsafe_allow_html=True)
            if can_edit:
                if st.button("Usuń", key=f"dn_{ridx}"): dane["tablica"].pop(ridx); zapisz_dane(dane); st.rerun()
