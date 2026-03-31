import streamlit as st
import json
import os
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
button:has(div p:contains("ZROBIONE")), button:contains("ZROBIONE") {
    border: none !important; color: #212529 !important; background-color: #ffc107 !important;
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
button:has(div p:contains("Zaloguj się")):hover, button:contains("Zaloguj się"):hover {
    background-color: #155724 !important;
}
.stDownloadButton>button { border: 2px solid #212529 !important; background-color: #f8f9fa !important; color: #212529 !important; }
.stDownloadButton>button:hover { background-color: #212529 !important; color: white !important; }

/* POLA TEKSTOWE */
.stTextInput input { min-height: 32px !important; height: 32px !important; font-size: 12px !important; border-radius: 6px !important; }
div[data-testid="stPopover"] > button { min-height: 32px !important; height: 32px !important; border: 1px solid #ced4da !important; background: white !important; text-align: left !important; color: #495057 !important; }

.main .block-container { padding-top: 2rem; }
.section-header { background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px; font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.sidebar-header { background: linear-gradient(90deg, #1e7e34, #28a745); color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 14px; margin-bottom: 15px; letter-spacing: 1px; }

/* FIX KALENDARZA */
.day-col { 
    background-color: #ffffff; 
    border: 1px solid #dee2e6; 
    border-radius: 8px; 
    padding: 10px; 
    min-height: 200px;
    width: 100%;
}
.day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 12px; padding-bottom: 6px; }
.day-name { font-weight: 700; font-size: 13px; color: #495057; }
.day-date { font-size: 11px; color: #868e96; }

.transport-group { background-color: #f8f9fa; border: 1px dashed #ced4da; border-radius: 6px; padding: 4px; margin-bottom: 8px; }
.transport-group-header { font-size: 9px; font-weight: 800; color: #495057; text-transform: uppercase; margin-bottom: 4px; text-align: center; border-bottom: 1px solid #dee2e6; padding-bottom: 2px; }

.cal-entry-out { cursor: help; font-size: 10px; background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cal-entry-ready { cursor: help; font-size: 10px; background: #d4edda; color: #155724; border-left: 3px solid #28a745; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cal-entry-in { cursor: help; font-size: 10px; background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }
.cal-entry-task { cursor: help; font-size: 10px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }

.table-group-header { background-color: #e9ecef; color: #212529; padding: 6px 12px; font-weight: 700; font-size: 12px; border-radius: 4px; margin: 15px 0 8px 0; border-left: 4px solid #007bff; }
.badge-status-prod { background-color: #ffc107; color: #212529; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-ready { background-color: #28a745; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid #dee2e6; padding-bottom: 4px;}
</style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH ---
PLIK_DANYCH = "baza_gropak_v3.json"
OPCJE_TRANSPORTU = ["Brak", "Auto 1", "Auto 2", "Transport zewnętrzny", "Odbiór osobisty", "Kurier"]

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        k_score = item.get('kurs', 1)
        status_score = 1 if item.get('status') == 'Gotowe' else 0 
        try:
            parts = str(item.get('termin', '')).strip().split('.')
            if len(parts) >= 2:
                d, m = int(parts[0]), int(parts[1])
                y = int(parts[2]) if len(parts) > 2 else datetime.now().year
                return (0, y, m, d, t_score, k_score, status_score, pilne)
            return (1, 9999, 99, 99, 99, 99, 99, pilne) 
        except: return (1, 9999, 99, 99, 99, 99, 99, pilne)
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
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f: json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- FUNKCJA GENERUJĄCA HTML DO DRUKU ---
def generuj_html_do_druku(z):
    pilne_html = '<div style="color:red; border:4px solid red; padding:10px; text-align:center; font-size:24px; font-weight:bold;">🔥 ZLECENIE PILNE 🔥</div>' if z.get('pilne') else ''
    auto_val = z.get('auto', 'Brak'); k_val = z.get('kurs', 1); transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    return f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:30px;}} .card{{border:4px solid black;padding:30px;}} h1{{text-align:center;border-bottom:3px solid black;}} .row{{display:flex;justify-content:space-between;margin-top:20px;font-size:20px;}} .box{{border:1px solid #666;padding:15px;margin-top:20px;min-height:150px;font-size:18px;white-space:pre-wrap;}}</style></head><body onload="window.print()"><div class="card">{pilne_html}<h1>Karta Zlecenia: {z.get('klient')}</h1><div class="row"><div><b>Termin:</b> {z.get('termin')}</div><div><b>Transport:</b> {transport_str}</div></div><p><b>Specyfikacja:</b></p><div class="box">{z.get('opis')}</div><p><b>Ilości:</b></p><div class="box">{z.get('szczegoly')}</div><div style="margin-top:50px;text-align:right;">Podpis: __________________________</div></div></body></html>"""

if "print_order" not in st.session_state: st.session_state.print_order = None

# --- WIDOK DRUKOWANIA ---
if st.session_state.print_order is not None:
    z = st.session_state.print_order
    st.markdown('<style>[data-testid="stSidebar"] {display: none;} header {display: none;}</style>', unsafe_allow_html=True)
    if st.button("⬅️ Wróć do systemu"): st.session_state.print_order = None; st.rerun()
    st.markdown(f"<div style='border:4px solid black;padding:40px;background:white;'><h1>Zlecenie: {z.get('klient')}</h1><p>{z.get('opis')}</p></div>", unsafe_allow_html=True)
    st.stop()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
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
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p: st.session_state.user = u; st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()

    if st.session_state.user == "admin":
        with st.expander("👥 Użytkownicy"):
            with st.form("add_user", clear_on_submit=True):
                nu = st.text_input("Login"); np = st.text_input("Hasło")
                if st.form_submit_button("Dodaj"):
                    if nu: dane["uzytkownicy"][nu] = np; zapisz_dane(dane); st.rerun()
            for usr in list(dane["uzytkownicy"].keys()):
                if usr != "admin":
                    if st.button(f"Usuń {usr}", key=f"del_{usr}"): del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()
        st.divider()

    st.markdown('<div class="sidebar-header">➕ NOWY WPIS</div>', unsafe_allow_html=True)
    typ = st.selectbox("Rodzaj:", ["Produkcja", "Dostawa (PZ)", "Dyspozycja"])
    with st.form("f_add", clear_on_submit=True):
        if typ == "Produkcja":
            kl = st.text_input("👤 Klient"); tm = st.text_input("📅 Termin (np. 31.03)"); op = st.text_area("📝 Specyfikacja"); sz = st.text_area("📦 Ilości"); auto = st.selectbox("Transport:", OPCJE_TRANSPORTU); kr = st.selectbox("Kurs:", [1,2,3,4,5]); p = st.checkbox("🔥 PILNE")
            if st.form_submit_button("💾 Zapisz"):
                if kl: 
                    dane["w_realizacji"].append({"klient":kl,"termin":tm,"opis":op,"szczegoly":sz,"auto":auto,"kurs":kr,"pilne":p,"status":"W produkcji","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                    zapisz_dane(dane); st.rerun()
        elif typ == "Dostawa (PZ)":
            ds = st.text_input("🏢 Dostawca"); tm = st.text_input("📅 Data"); op = st.text_area("📦 Co przyjeżdża?")
            if st.form_submit_button("💾 Zapisz"):
                if ds: dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
        else:
            tyt = st.text_input("🎯 Tytuł"); tm = st.text_input("📅 Termin"); op = st.text_area("📝 Opis")
            if st.form_submit_button("💾 Zapisz"):
                if tyt: dane["dyspozycje"].append({"tytul":tyt,"termin":tm,"opis":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()

    if st.session_state.user == "admin":
        st.divider()
        if st.button("🔥 RESETUJ WSZYSTKIE DANE"):
            for k in ["w_realizacji","zrealizowane","przyjecia","przyjecia_historia","dyspozycje","dyspozycje_historia"]: dane[k] = []
            zapisz_dane(dane); st.rerun()

# --- 5. STATYSTYKI ---
st.markdown('<div class="section-header">Podsumowanie</div>', unsafe_allow_html=True)
c_s1, c_s2, c_s3 = st.columns(3)
c_s1.metric("📦 Zlecenia", len(dane["w_realizacji"])); c_s2.metric("🚚 Dostawy", len(dane["przyjecia"])); c_s3.metric("📋 Dyspozycje", len(dane["dyspozycje"]))

# --- 6. TERMINARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
cn1, _, cn3 = st.columns([1,4,1])
if cn1.button("← Poprzedni"): st.session_state.wo -= 7; st.rerun()
if cn3.button("Następny →"): st.session_state.wo += 7; st.rerun()

start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
cols = st.columns(7)
for i in range(7):
    day = start + timedelta(days=i)
    with cols[i]:
        st.markdown(f"<div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{day.strftime('%d.%m')}</div></div>", unsafe_allow_html=True)
        dv, mv = day.day, day.month
        
        # Produkcja (Grupowana)
        grupy = {}
        for z in dane["w_realizacji"]:
            try:
                zd, zm = map(int, z.get('termin','').split('.')[:2])
                if zd == dv and zm == mv:
                    k = (z.get('auto','Brak'), z.get('kurs',1))
                    if k not in grupy: grupy[k] = []
                    grupy[k].append(z)
            except: pass
        for (tr, kr), items in grupy.items():
            if tr != "Brak":
                st.markdown(f"<div class='transport-group-header'>{tr} (K{kr})</div>", unsafe_allow_html=True)
            for it in items:
                st_cl = "cal-entry-ready" if it.get('status')=="Gotowe" else "cal-entry-out"
                prefix = "✅ " if it.get('status')=="Gotowe" else ""
                op_s = str(it.get('opis','')).replace('"', '&quot;').replace('\n', ' ')
                tooltip = f"SPECYFIKACJA: {op_s}"
                st.markdown(f"<div class='{st_cl}' title='{tooltip}'>{prefix}{it.get('klient')}</div>", unsafe_allow_html=True)
        
        # Przyjęcia PZ (NOWE W KALENDARZU)
        for p in dane["przyjecia"]:
            try:
                pd, pm = map(int, p.get('termin','').split('.')[:2])
                if pd == dv and pm == mv:
                    towar_s = str(p.get('towar','')).replace('"', '&quot;').replace('\n', ' ')
                    st.markdown(f"<div class='cal-entry-in' title='{towar_s}'>P: {p.get('dostawca')}</div>", unsafe_allow_html=True)
            except: pass
            
        # Dyspozycje (NOWE W KALENDARZU)
        for d in dane["dyspozycje"]:
            try:
                dd, dm = map(int, d.get('termin','').split('.')[:2])
                if dd == dv and dm == mv:
                    opis_s = str(d.get('opis','')).replace('"', '&quot;').replace('\n', ' ')
                    st.markdown(f"<div class='cal-entry-task' title='{opis_s}'>D: {d.get('tytul')}</div>", unsafe_allow_html=True)
            except: pass

# --- 7. TABELE REALIZACJI ---
st.markdown('<div class="section-header">Tabele Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Szukaj...", "").lower()
t_prod, t_log, t_dysp = st.tabs(["🏭 Produkcja", "🚚 Przyjęcia", "📋 Dyspozycje"])

with t_prod:
    tp1, tp2 = st.tabs(["Aktywne", "Historia"])
    with tp1:
        if not dane["w_realizacji"]: st.info("Brak aktywnych zleceń.")
        else:
            hc = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
            hc[0].markdown('<div class="label-text">Klient</div>', unsafe_allow_html=True); hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True); hc[2].markdown('<div class="label-text">Dodano</div>', unsafe_allow_html=True); hc[3].markdown('<div class="label-text">Edycja / Druk</div>', unsafe_allow_html=True); hc[4].markdown('<div class="label-text">Status</div>', unsafe_allow_html=True)
            last_g = None
            for i, z in enumerate(dane["w_realizacji"]):
                if search and search not in str(z).lower(): continue
                curr_g = (z.get('termin'), z.get('auto'), z.get('kurs'))
                if curr_g != last_g:
                    st.markdown(f"<div class='table-group-header'>📅 {z.get('termin')} | {z.get('auto')} (K{z.get('kurs')})</div>", unsafe_allow_html=True)
                    last_g = curr_g
                c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
                status = z.get('status','W produkcji')
                b_st = '<span class="badge-status-ready">GOTOWE</span>' if status=='Gotowe' else '<span class="badge-status-prod">PRODUKCJA</span>'
                c[0].markdown(f"**{z.get('klient')}** {'🔥' if z.get('pilne') else ''}<br>{b_st}", unsafe_allow_html=True)
                c[1].write(z.get('termin')); c[2].write(z.get('data_p'))
                
                u_id = f"{z.get('data_p')}_{i}".replace(':','').replace(' ','_')
                with c[3].popover("Menu"):
                    st.download_button("🖨️ Pobierz Kartę", generuj_html_do_druku(z), f"Karta_{u_id}.html", "text/html", key=f"dl_{u_id}")
                    nt = st.text_input("Data", z.get('termin'), key=f"t_{u_id}")
                    na = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(z.get('auto','Brak')), key=f"a_{u_id}")
                    nk = st.selectbox("Kurs", [1,2,3,4,5], int(z.get('kurs',1))-1, key=f"k_{u_id}")
                    no = st.text_area("Specyfikacja", z.get('opis',''), key=f"o_{u_id}")
                    ns = st.text_area("Ilości", z.get('szczegoly',''), key=f"s_{u_id}")
                    if st.button("Zapisz", key=f"sv_{u_id}"):
                        dane["w_realizacji"][i].update({"termin":nt,"auto":na,"kurs":nk,"opis":no,"szczegoly":ns}); zapisz_dane(dane); st.rerun()
                
                if status != "Gotowe":
                    if c[4].button("ZROBIONE", key=f"done_{u_id}"): dane["w_realizacji"][i]['status']="Gotowe"; zapisz_dane(dane); st.rerun()
                else:
                    if c[4].button("WYŚLIJ", key=f"send_{u_id}"): dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
                if c[5].button("X", key=f"x_{u_id}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
    with tp2: st.dataframe(dane["zrealizowane"][::-1], use_container_width=True)

with t_log:
    for i, p in enumerate(dane["przyjecia"]):
        c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
        c[0].write(f"**{p.get('dostawca')}**"); c[1].write(p.get('termin')); c[2].write(p.get('data_p'))
        p_id = f"p_{i}_{p.get('data_p')}".replace(':','').replace(' ','_')
        with c[3].popover("Edytuj"):
            nt = st.text_input("Data", p.get('termin'), key=f"pt_{p_id}"); no = st.text_area("Towar", p.get('towar',''), key=f"po_{p_id}")
            if st.button("Zapisz", key=f"ps_{p_id}"): dane["przyjecia"][i].update({"termin":nt,"towar":no}); zapisz_dane(dane); st.rerun()
        if c[4].button("OK", key=f"pok_{p_id}"): dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"px_{p_id}"): dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()

with t_dysp:
    for i, d in enumerate(dane["dyspozycje"]):
        c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
        c[0].write(f"**{d.get('tytul')}**"); c[1].write(d.get('termin')); c[2].write(d.get('data_p'))
        d_id = f"d_{i}_{d.get('data_p')}".replace(':','').replace(' ','_')
        with c[3].popover("Edytuj"):
            nt = st.text_input("Termin", d.get('termin'), key=f"dt_{d_id}"); no = st.text_area("Opis", d.get('opis',''), key=f"do_{d_id}")
            if st.button("Zapisz", key=f"ds_{d_id}"): dane["dyspozycje"][i].update({"termin":nt,"opis":no}); zapisz_dane(dane); st.rerun()
        if c[4].button("GOTOWE", key=f"dg_{d_id}"): dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"dx_{d_id}"): dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()
