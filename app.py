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
    border: none !important; color: white !important; background-color: #dc3545 !important;
}
button:contains("Zapisz"), button:contains("Zaloguj"), button:contains("Opublikuj") {
    border: none !important; color: white !important; background-color: #007bff !important;
}

/* PASEK POWIADOMIEŃ */
.notification-container {
    background-color: #fff3cd; border: 2px solid #ffeeba; border-left: 10px solid #ffc107;
    padding: 15px; border-radius: 8px; margin-bottom: 25px;
}

/* KALENDARZ MOBILNY */
.mobile-day-selector {
    display: flex; overflow-x: auto; gap: 10px; padding: 10px 0; margin-bottom: 20px;
    scrollbar-width: none; -ms-overflow-style: none;
}
.mobile-day-selector::-webkit-scrollbar { display: none; }

.cal-entry-out, .cal-entry-ready, .cal-entry-in, .cal-entry-task, .cal-entry-return { 
    font-size: 10px; padding: 4px 6px; margin-bottom: 2px; border-radius: 3px; 
    font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; cursor: help; 
}
.cal-entry-out { background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; }
.cal-entry-ready { background: #d4edda; color: #155724; border-left: 3px solid #28a745; }
.cal-entry-return { background: #f3e5f5; color: #7b1fa2; border: 1px solid #7b1fa2; }
.cal-entry-in { background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; }
.cal-entry-task { background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; }

.client-hover { cursor: help; border-bottom: 1px dotted #999; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH ---
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
            parts = str(item.get('termin', '')).split('.')
            return (0, 2026, int(parts[1]), int(parts[0]), prio)
        except: return (1, 9999, 99, 99, prio)
    for k in ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]:
        if k in dane: dane[k].sort(key=sort_key)
    return dane

def wczytaj_dane():
    default_dane = {"w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [], "dyspozycje": [], "dyspozycje_historia": [], "odbiory": [], "odbiory_historia": [], "tablica": [], "uzytkownicy": {"admin": {"pass": "gropak2026", "role": "admin"}}}
    client = get_gsheet_client()
    if not client: return default_dane
    try:
        sh = client.open(GSHEET_NAME); ws = sh.get_worksheet(0); val = ws.acell('A1').value
        if val:
            d = json.loads(val)
            for k, v in default_dane.items():
                if k not in d: d[k] = v
            return posortuj_dane(d)
    except: pass
    return default_dane

def zapisz_dane(d):
    client = get_gsheet_client()
    if client:
        try:
            sh = client.open(GSHEET_NAME); ws = sh.get_worksheet(0)
            ws.update_acell('A1', json.dumps(posortuj_dane(d)))
        except: pass

dane = wczytaj_dane()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.title("GROPAK ERP")
        with st.form("l"):
            u = st.text_input("👤 Login"); p = st.text_input("🔒 Hasło", type="password")
            if st.form_submit_button("Zaloguj się"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p: 
                    st.session_state.user = u
                    st.session_state.role = dane["uzytkownicy"][u].get("role", "edycja")
                    st.rerun()
    st.stop()

# --- 4. PANEL BOCZNY (PRZEŁĄCZNIK WIDOKU) ---
with st.sidebar:
    st.write(f"Witaj, **{st.session_state.user}**")
    view_mode = st.radio("💻 Tryb wyświetlania:", ["Stacjonarny", "Mobilny"])
    st.divider()
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    
    if st.session_state.role != "wgląd":
        st.markdown("### NOWY WPIS")
        typ = st.selectbox("Rodzaj:", ["Produkcja", "Odbiór", "Dostawa PZ", "Dyspozycja"])
        with st.form("f_add", clear_on_submit=True):
            if typ=="Produkcja":
                kl, tm = st.text_input("Klient"), st.text_input("Termin (np. 01.04)")
                sz = st.text_area("Produkty")
                au, kr = st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"status":"W produkcji","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                    zapisz_dane(dane); st.rerun()
            elif typ=="Odbiór":
                mj, tm, tw = st.text_input("Skąd?"), st.text_input("Data"), st.text_area("Co?")
                if st.form_submit_button("Zapisz"):
                    dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                    zapisz_dane(dane); st.rerun()
            # PZ i Dyspozycje - uproszczone dla czytelności...
            elif typ=="Dostawa PZ":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Data"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                    zapisz_dane(dane); st.rerun()
            elif typ=="Dyspozycja":
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                    zapisz_dane(dane); st.rerun()

# --- 5. TERMINARZ (WIDOKI) ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)

if view_mode == "Stacjonarny":
    # Oryginalny widok 7 kolumn
    if "wo" not in st.session_state: st.session_state.wo = 0
    c1, _, c3 = st.columns([1,4,1])
    if c1.button("← Poprzedni"): st.session_state.wo -= 7; st.rerun()
    if c3.button("Następny →"): st.session_state.wo += 7; st.rerun()
    
    start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
    cols = st.columns(7)
    for i in range(7):
        day = start + timedelta(days=i); d_str = day.strftime('%d.%m')
        with cols[i]:
            st.markdown(f"<div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{d_str}</div></div>", unsafe_allow_html=True)
            # Logika wpisów kalendarza...
            for z in dane["w_realizacji"]:
                if z.get('termin') == d_str:
                    cl = "cal-entry-ready" if z.get('status') == 'Gotowe' else "cal-entry-out"
                    st.markdown(f"<div class='{cl}' title='{z.get('szczegoly')}'>{z.get('klient')}</div>", unsafe_allow_html=True)
            for o in dane["odbiory"]:
                if o.get('termin') == d_str:
                    st.markdown(f"<div class='cal-entry-return' title='{o.get('towar')}'>Odb: {o.get('miejsce')}</div>", unsafe_allow_html=True)
else:
    # WIDOK MOBILNY (Wybór dnia)
    start = datetime.now() - timedelta(days=datetime.now().weekday())
    dates = [(start + timedelta(days=i)).strftime('%d.%m') for i in range(14)]
    chosen_day = st.select_slider("Wybierz dzień:", options=dates, value=datetime.now().strftime('%d.%m'))
    
    st.markdown(f"### Plan na dzień {chosen_day}")
    found = False
    for z in dane["w_realizacji"]:
        if z.get('termin') == chosen_day:
            st.warning(f"📦 **{z.get('klient')}** | {z.get('auto')} | {z.get('szczegoly')}")
            found = True
    for o in dane["odbiory"]:
        if o.get('termin') == chosen_day:
            st.info(f"🔄 **Odbiór: {o.get('miejsce')}** | {o.get('towar')}")
            found = True
    if not found: st.write("Brak zadań na wybrany dzień.")

# --- 6. TABELE REALIZACJI (UJEDNOLICONE) ---
st.markdown('<div class="section-header">Listy Realizacji</div>', unsafe_allow_html=True)
tabs = st.tabs(["🏭 Produkcja", "🔄 Odbiory", "🚚 Przyjęcia PZ", "📋 Dyspozycje"])

def render_table(lista_zrodlowa, k_nazwa, k_szczegoly, k_id, mode):
    if not lista_zrodlowa: 
        st.info("Brak wpisów.")
        return

    # Dostosowanie kolumn do widoku
    col_layout = [2.5, 1.2, 3.5, 1.2, 0.8] if view_mode == "Stacjonarny" else [3, 2, 2]
    
    for i, item in enumerate(lista_zrodlowa):
        ma_termin = bool(str(item.get('termin','')).strip())
        if mode == "produkcja" and not ma_termin: continue
        if mode == "plan" and ma_termin: continue
        
        st.markdown("<div style='padding:10px 0; border-bottom:1px solid #eee;'>", unsafe_allow_html=True)
        c = st.columns(col_layout)
        status = item.get('status','W toku')
        badge_cls = "badge-status-ready" if status=='Gotowe' else "badge-status-prod"
        
        # Kolumna 1: Dane główne
        c[0].markdown(f"**{item.get(k_nazwa)}**<br><span class='badge {badge_cls}'>{status}</span>", unsafe_allow_html=True)
        
        # Kolumna 2: Termin
        c[1].write(item.get('termin', '---'))
        
        # Kolumna 3 (Zarządzanie/Szczegóły)
        u_id = f"{k_id}_{i}"
        if view_mode == "Stacjonarny":
            with c[2].popover("Szczegóły / Edytuj"):
                new_t = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                new_s = st.text_area("Szczegóły", item.get(k_szczegoly), key=f"s_{u_id}")
                if st.button("Zapisz", key=f"sv_{u_id}"):
                    item.update({"termin":new_t, k_szczegoly:new_s}); zapisz_dane(dane); st.rerun()
            
            if status != "Gotowe" and c[3].button("OK", key=f"ok_{u_id}"):
                item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"):
                lista_zrodlowa.pop(i); zapisz_dane(dane); st.rerun()
        else:
            # WIDOK MOBILNY - Akcje skrócone
            with c[2].popover("Akcje"):
                st.write(item.get(k_szczegoly))
                if st.button("ZROBIONE", key=f"mok_{u_id}"):
                    item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
                if st.button("USUŃ", key=f"mdel_{u_id}"):
                    lista_zrodlowa.pop(i); zapisz_dane(dane); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[0]:
    s1, s2 = st.tabs(["Aktywne", "Do zaplanowania"])
    with s1: render_table(dane["w_realizacji"], "klient", "szczegoly", "prod", "produkcja")
    with s2: render_table(dane["w_realizacji"], "klient", "szczegoly", "plan", "plan")
with tabs[1]: render_table(dane["odbiory"], "miejsce", "towar", "odb", "active")
with tabs[2]: render_table(dane["przyjecia"], "dostawca", "towar", "pz", "active")
with tabs[3]: render_table(dane["dyspozycje"], "tytul", "opis", "dysp", "active")

# --- 7. TABLICA OGŁOSZEŃ ---
st.markdown("<br><hr style='border: 2px solid #343a40;'><br>", unsafe_allow_html=True)
if dane["tablica"]:
    for note in reversed(dane["tablica"]):
        st.info(f"📌 {note['tresc']} ({note['data']} | {note['autor']})")
