import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json
import pandas as pd
from datetime import datetime, timedelta

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
button:has(div p:contains("WYŚLIJ")), button:contains("WYŚLIJ"), button:has(div p:contains("OK")), button:contains("OK") {
    border: none !important; color: white !important; background-color: #28a745 !important;
}
button:has(div p:contains("ZROBIONE")), button:contains("ZROBIONE"), button:has(div p:contains("GOTOWE")), button:contains("GOTOWE") {
    border: none !important; color: white !important; background-color: #28a745 !important;
}
button:has(div p:contains("X")), button:contains("X") {
    border: none !important; color: white !important; background-color: #dc3545 !important; padding: 0 !important;
}
button:has(div p:contains("Zapisz")), button:contains("Zapisz") {
    border: none !important; color: white !important; background-color: #007bff !important;
}
button:has(div p:contains("RESETUJ")), button:contains("RESETUJ") {
    border: none !important; color: white !important; background-color: #dc3545 !important; font-weight: 900 !important;
}
button:has(div p:contains("Zaloguj się")), button:contains("Zaloguj się") {
    border: none !important; color: white !important; background-color: #1e7e34 !important; height: 40px !important; font-size: 14px; margin-top: 10px;
}

/* POWIADOMIENIA */
.notification-container {
    background-color: #fff3cd; border: 2px solid #ffeeba; border-left: 10px solid #ffc107;
    padding: 15px; border-radius: 8px; margin-bottom: 25px;
}
.notif-item { font-size: 13px; color: #856404; padding: 2px 0; border-bottom: 1px dashed #ffeeba; }

/* NOTATKA / TABLICA */
.note-card { background-color: #fff9c4; border-left: 5px solid #fbc02d; padding: 15px; border-radius: 4px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
.note-meta { font-size: 10px; color: #7f8c8d; margin-top: 8px; border-top: 1px solid #f0e68c; padding-top: 4px; }

/* KALENDARZ */
[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)):not(:has(> div:nth-child(8))) { gap: 0px !important; }
[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)):not(:has(> div:nth-child(8))) > div {
    flex: 0 0 calc(100% / 7) !important; min-width: calc(100% / 7) !important; max-width: calc(100% / 7) !important; padding: 0 3px !important;
}
.day-col { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 8px; min-height: 250px; display: flex; flex-direction: column; gap: 4px; }
.day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 8px; }
.day-name { font-weight: 700; font-size: 12px; color: #495057; text-transform: uppercase; }
.cal-entry-out, .cal-entry-ready, .cal-entry-in, .cal-entry-task, .cal-entry-return { font-size: 10px; padding: 4px 6px; margin-bottom: 2px; border-radius: 3px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
.cal-entry-out { background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; }
.cal-entry-ready { background: #d4edda; color: #155724; border-left: 3px solid #28a745; }
.cal-entry-return { background: #f3e5f5; color: #7b1fa2; border: 1px solid #7b1fa2; }
.cal-entry-in { background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; }
.cal-entry-task { background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; }

/* TABELE */
.table-group-header { background-color: #e9ecef; color: #212529; padding: 6px 12px; font-weight: 700; font-size: 12px; border-radius: 4px; margin: 15px 0 8px 0; border-left: 4px solid #007bff; }
.badge-status-prod { background-color: #ffc107; color: #212529; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; display: inline-block;}
.badge-status-ready { background-color: #28a745; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; display: inline-block;}
.label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid #dee2e6; padding-bottom: 4px;}
.readonly-text { font-size: 13px; white-space: pre-wrap; color: #495057; line-height: 1.4; padding: 5px; background: #fdfdfd; border-radius: 4px; border: 1px solid #eee; }

.section-header { background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px; font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; }
.sidebar-header { background: linear-gradient(90deg, #1e7e34, #28a745); color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 14px; margin-bottom: 15px; }

div[data-testid="stHorizontalBlock"] { align-items: flex-start !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH (GOOGLE SHEETS) ---
OPCJE_TRANSPORTU = ["Brak", "Auto 1", "Auto 2", "Transport zewnętrzny", "Odbiór osobisty", "Kurier"]

# Połączenie z Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Błąd połączenia z Google Sheets. Sprawdź 'Secrets' w panelu Streamlit.")
    st.stop()

def wczytaj_dane():
    default_dane = {
        "w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [], 
        "dyspozycje": [], "dyspozycje_historia": [], "odbiory": [], "odbiory_historia": [],
        "tablica": [], "uzytkownicy": {"admin": {"pass": "gropak2026", "role": "admin", "last_login": ""}}
    }
    try:
        # Odczyt danych z pierwszej komórki A2 (A1 to nagłówek 'dane')
        df = conn.read(worksheet="Sheet1", usecols=[0], ttl=0) # ttl=0 wymusza odświeżenie
        if not df.empty and pd.notnull(df.iloc[0, 0]):
            return json.loads(df.iloc[0, 0])
    except:
        pass
    return default_dane

def zapisz_dane(dane):
    # Konwersja całego słownika na tekst JSON i zapis do jednej komórki arkusza
    json_payload = json.dumps(dane, indent=None)
    df_to_save = pd.DataFrame([json_payload], columns=["dane"])
    conn.update(worksheet="Sheet1", data=df_to_save)

dane = wczytaj_dane()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = "wgląd"
if "prev_login" not in st.session_state: st.session_state.prev_login = ""
if "notif_seen" not in st.session_state: st.session_state.notif_seen = False

if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("GROPAK ERP")
        with st.form("login_form"):
            u = st.text_input("👤 Login"); p = st.text_input("🔒 Hasło", type="password")
            if st.form_submit_button("Zaloguj się do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u]["pass"] == p: 
                    st.session_state.user = u
                    st.session_state.role = dane["uzytkownicy"][u]["role"]
                    st.session_state.prev_login = dane["uzytkownicy"][u].get("last_login", "")
                    dane["uzytkownicy"][u]["last_login"] = datetime.now().strftime("%d.%m %H:%M")
                    zapisz_dane(dane)
                    st.rerun()
                else: st.error("Nieprawidłowy login lub hasło.")
    st.stop()

is_readonly = st.session_state.role == "wgląd"
can_edit = st.session_state.role in ["admin", "edycja"]
is_admin = st.session_state.role == "admin"

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user}** (`{st.session_state.role.upper()}`)")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    
    if is_admin:
        with st.expander("👥 Użytkownicy"):
            with st.form("add_u"):
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
        st.divider()

    if can_edit:
        st.markdown('<div class="sidebar-header">➕ NOWY WPIS</div>', unsafe_allow_html=True)
        typ = st.selectbox("Rodzaj:", ["Produkcja", "Odbiór (Powrót)", "Dostawa (PZ)", "Dyspozycja"])
        with st.form("f_add"):
            if typ=="Produkcja":
                kl, tm, sz, au, kr = st.text_input("Klient"), st.text_input("Termin"), st.text_area("Produkty"), st.selectbox("Auto", OPCJE_TRANSPORTU), st.selectbox("Kurs", [1,2,3,4,5])
                if st.form_submit_button("Zapisz"):
                    if kl: 
                        dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":au,"kurs":kr,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")})
                        zapisz_dane(dane); st.rerun()
            elif typ=="Odbiór (Powrót)":
                mj, tm, tw = st.text_input("Skąd?"), st.text_input("Data"), st.text_area("Co?")
                if st.form_submit_button("Zapisz"):
                    if mj: 
                        dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")})
                        zapisz_dane(dane); st.rerun()
            elif typ=="Dostawa (PZ)":
                ds, tm, tw = st.text_input("Dostawca"), st.text_input("Data"), st.text_area("Towar")
                if st.form_submit_button("Zapisz"):
                    if ds: 
                        dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tw,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")})
                        zapisz_dane(dane); st.rerun()
            else:
                ty, tm, op = st.text_input("Tytuł"), st.text_input("Termin"), st.text_area("Opis")
                if st.form_submit_button("Zapisz"):
                    if ty: 
                        dane["dyspozycje"].append({"tytul":ty,"termin":tm,"opis":op,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M")})
                        zapisz_dane(dane); st.rerun()

# --- 5. POWIADOMIENIA ---
if st.session_state.prev_login and not st.session_state.notif_seen:
    try:
        p_dt = datetime.strptime(st.session_state.prev_login, "%d.%m %H:%M").replace(year=datetime.now().year)
        nowe = []
        for k, lbl in [("w_realizacji","📦 Prod"), ("odbiory","🔄 Odbiór"), ("przyjecia","🚚 PZ"), ("dyspozycje","📋 Dysp")]:
            for item in dane[k]:
                try:
                    i_dt = datetime.strptime(item["data_p"], "%d.%m %H:%M").replace(year=datetime.now().year)
                    if i_dt > p_dt:
                        nm = item.get("klient") or item.get("miejsce") or item.get("dostawca") or item.get("tytul")
                        nowe.append(f"• <b>{lbl}</b>: {nm} (dodano {item['data_p']})")
                except: pass
        if nowe:
            st.markdown(f'<div class="notification-container"><b>🔔 NOWOŚCI OD OSTATNIEJ WIZYTY:</b>', unsafe_allow_html=True)
            for n in nowe[:5]: st.markdown(f'<div class="notif-item">{n}</div>', unsafe_allow_html=True)
            if st.button("Oznacz jako przeczytane"): st.session_state.notif_seen = True; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    except: pass

# --- 6. TERMINARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
cn1, _, cn3 = st.columns([1,4,1])
if cn1.button("← Poprzedni tydzień"): st.session_state.wo -= 7; st.rerun()
if cn3.button("Następny tydzień →"): st.session_state.wo += 7; st.rerun()
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
        for (tr, kr), cnt in gr.items():
            all_r = all(it.get('status')=='Gotowe' for it in cnt["p"])
            cl = "cal-entry-ready" if (all_r and cnt["p"]) else "cal-entry-out"
            lbl = f"{tr}/K{kr}" if tr in ["Auto 1","Auto 2"] else tr
            st.markdown(f"<div class='{cl}'>{lbl} ({len(cnt['p'])})</div>", unsafe_allow_html=True)

# --- 7. TABELE REALIZACJI (UJEDNOLICONE) ---
st.markdown('<div class="section-header">Listy Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Szukaj we wszystkich wpisach...", "").lower()
tabs = st.tabs(["🏭 Produkcja", "🔄 Odbiory", "🚚 Przyjęcia PZ", "📋 Dyspozycje"])

def renderuj_tabele_ujednolicona(lista_danych, klucz_nazwa, klucz_szczegoly, klucz_id, typ_sekcji):
    if not lista_danych: 
        st.info("Brak aktywnych wpisów.")
        return
    hc = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
    hc[0].markdown('<div class="label-text">Podmiot</div>', unsafe_allow_html=True)
    hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
    hc[2].markdown(f'<div class="label-text">{"Szczegóły" if is_readonly else "Menu"}</div>', unsafe_allow_html=True)
    hc[3].markdown(f'<div class="label-text">Akcja</div>', unsafe_allow_html=True)
    
    for i, item in enumerate(lista_danych):
        if search and search not in str(item).lower(): continue
        c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
        status = item.get('status','W toku')
        badge = '<span class="badge-status-ready">✅ GOTOWE</span>' if status=='Gotowe' else '<span class="badge-status-prod">⏳ W TOKU</span>'
        c[0].markdown(f"**{item.get(klucz_nazwa)}**<br>{badge}", unsafe_allow_html=True)
        c[1].write(item.get('termin', '---'))
        u_id = f"{klucz_id}_{i}_{item.get('data_p','')}".replace(':','_').replace(' ','_')
        if is_readonly:
            c[2].markdown(f"<div class='readonly-text'>{item.get(klucz_szczegoly,'-')}</div>", unsafe_allow_html=True)
        else:
            with c[2].popover("Edytuj"):
                new_t = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                new_s = st.text_area("Szczegóły", item.get(klucz_szczegoly), key=f"s_{u_id}")
                if st.button("Zapisz", key=f"sv_{u_id}"):
                    item.update({"termin":new_t, klucz_szczegoly:new_s})
                    zapisz_dane(dane); st.rerun()
            if status != "Gotowe":
                if c[3].button("ZROBIONE", key=f"ok_{u_id}"):
                    item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[3].button("WYŚLIJ", key=f"send_{u_id}"):
                    hist_key = {"prod":"zrealizowane", "odb":"odbiory_historia", "pz":"przyjecia_historia", "dysp":"dyspozycje_historia"}[klucz_id]
                    dane[hist_key].append(lista_danych.pop(i))
                    zapisz_dane(dane); st.rerun()
            if c[4].button("X", key=f"del_{u_id}"):
                lista_danych.pop(i); zapisz_dane(dane); st.rerun()

with tabs[0]: renderuj_tabele_ujednolicona(dane["w_realizacji"], "klient", "szczegoly", "prod", "produkcja")
with tabs[1]: renderuj_tabele_ujednolicona(dane["odbiory"], "miejsce", "towar", "odb", "odbiory")
with tabs[2]: renderuj_tabele_ujednolicona(dane["przyjecia"], "dostawca", "towar", "pz", "przyjecia")
with tabs[3]: renderuj_tabele_ujednolicona(dane["dyspozycje"], "tytul", "opis", "dysp", "dyspozycje")

# --- 8. TABLICA OGŁOSZEŃ (NA DOLE) ---
st.markdown("<br><hr style='border: 2px solid #343a40;'><br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📌 Tablica Ogłoszeń</div>', unsafe_allow_html=True)
if can_edit:
    with st.form("bottom_note", clear_on_submit=True):
        nowa_tresc = st.text_area("Dodaj ogłoszenie:"); 
        if st.form_submit_button("➕ Opublikuj"):
            if nowa_tresc:
                dane["tablica"].append({"tresc": nowa_tresc, "data": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()
if not dane["tablica"]: st.info("Brak ogłoszeń.")
else:
    nc = st.columns(3)
    for i, note in enumerate(reversed(dane["tablica"][-9:])):
        ridx = len(dane["tablica"])-1-i
        with nc[i % 3]:
            st.markdown(f"<div class='note-card'>{note['tresc']}<div class='note-meta'>{note['data']} | {note['autor']}</div></div>", unsafe_allow_html=True)
            if can_edit:
                if st.button("Usuń", key=f"dn_{ridx}"): dane["tablica"].pop(ridx); zapisz_dane(dane); st.rerun()
