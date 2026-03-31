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
button:has(div p:contains("Przywróć")), button:contains("Przywróć") {
    border: none !important; color: white !important; background-color: #17a2b8 !important;
}

/* POLA TEKSTOWE */
.stTextInput input { min-height: 32px !important; height: 32px !important; font-size: 12px !important; border-radius: 6px !important; }
div[data-testid="stPopover"] > button { min-height: 32px !important; height: 32px !important; border: 1px solid #ced4da !important; background: white !important; text-align: left !important; color: #495057 !important; }

.main .block-container { padding-top: 2rem; }
.section-header { background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px; font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.sidebar-header { background: linear-gradient(90deg, #1e7e34, #28a745); color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 14px; margin-bottom: 15px; letter-spacing: 1px; }
.sidebar-print-header { background: #343a40; color: white; padding: 10px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 13px; margin-top: 20px; margin-bottom: 10px; }

/* --- NOTATKA / TABLICA --- */
.note-card {
    background-color: #fff9c4;
    border-left: 5px solid #fbc02d;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 10px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
}
.note-meta {
    font-size: 10px;
    color: #7f8c8d;
    margin-top: 8px;
    border-top: 1px solid #f0e68c;
    padding-top: 4px;
}

/* --- "ZABETONOWANY" UKŁAD KALENDARZA --- */
[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)):not(:has(> div:nth-child(8))) {
    gap: 0px !important;
}
[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)):not(:has(> div:nth-child(8))) > div {
    flex: 0 0 calc(100% / 7) !important;
    min-width: calc(100% / 7) !important;
    max-width: calc(100% / 7) !important;
    padding: 0 3px !important;
}

.day-col { 
    background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 8px; 
    min-height: 300px; width: 100%; display: flex; flex-direction: column; gap: 4px; box-sizing: border-box;
}
.day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 8px; padding-bottom: 4px; }
.day-name { font-weight: 700; font-size: 12px; color: #495057; text-transform: uppercase; }
.day-date { font-size: 11px; color: #868e96; }

.cal-entry-out, .cal-entry-ready, .cal-entry-in, .cal-entry-task, .cal-entry-return { 
    font-size: 10px; padding: 4px 6px; margin-bottom: 2px; border-radius: 3px; font-weight: 600; 
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;
}
.cal-entry-out { background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; }
.cal-entry-ready { background: #d4edda; color: #155724; border-left: 3px solid #28a745; }
.cal-entry-return { background: #f3e5f5; color: #7b1fa2; border: 1px solid #7b1fa2; }
.cal-entry-in { background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; }
.cal-entry-task { background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; }

/* TABELE REALIZACJI */
.table-group-header { background-color: #e9ecef; color: #212529; padding: 6px 12px; font-weight: 700; font-size: 12px; border-radius: 4px; margin: 15px 0 8px 0; border-left: 4px solid #007bff; }
.badge-status-prod { background-color: #ffc107; color: #212529; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-ready { background-color: #28a745; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-return { background-color: #7b1fa2; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid #dee2e6; padding-bottom: 4px;}
button[data-baseweb="tab"] { font-size: 16px !important; font-weight: 600 !important; }

/* Styl dla podglądu bezpośredniego szczegółów */
.readonly-text { 
    font-size: 13px; 
    white-space: pre-wrap; 
    color: #495057; 
    line-height: 1.4; 
    padding: 5px;
    background: #fdfdfd;
    border-radius: 4px;
}

div[data-testid="stHorizontalBlock"] { align-items: flex-start !important; }
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
            termin = str(item.get('termin', '')).strip()
            if not termin: return (2, 9999, 99, 99, 99, 99, 99, pilne)
            parts = termin.split('.')
            d, m = int(parts[0]), int(parts[1])
            y = int(parts[2]) if len(parts) > 2 else datetime.now().year
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
        "tablica": [],
        "uzytkownicy": {"admin": {"pass": "gropak2026", "role": "admin"}}
    }
    if os.path.exists(PLIK_DANYCH):
        try:
            with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "uzytkownicy" in d:
                    for u, val in d["uzytkownicy"].items():
                        if isinstance(val, str):
                            d["uzytkownicy"][u] = {"pass": val, "role": "admin" if u == "admin" else "edycja"}
                for k, v in default_dane.items():
                    if k not in d: d[k] = v
                return posortuj_dane(d)
        except: pass
    return default_dane

def zapisz_dane(dane):
    dane = posortuj_dane(dane) 
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f: json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- FUNKCJE DRUKOWANIA ---
def generuj_html_do_druku(z):
    pilne_html = '<div style="color:red; border:4px solid red; padding:10px; text-align:center; font-size:24px; font-weight:bold;">🔥 ZLECENIE PILNE 🔥</div>' if z.get('pilne') else ''
    auto_val = z.get('auto', 'Brak'); k_val = z.get('kurs', 1); transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    return f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:30px;}} .card{{border:5px solid black;padding:30px;}} h1{{text-align:center;border-bottom:3px solid black;}} .row{{display:flex;justify-content:space-between;margin-top:20px;font-size:20px;}} .box{{border:1px solid #666;padding:15px;margin-top:20px;min-height:300px;font-size:20px;white-space:pre-wrap;line-height:1.4;}}</style></head><body onload="window.print()"><div class="card">{pilne_html}<h1>Karta Zlecenia: {z.get('klient')}</h1><div class="row"><div><b>Termin:</b> {z.get('termin')}</div><div><b>Transport:</b> {transport_str}</div></div><p><b>PRODUKTY / SZCZEGÓŁY ZAMÓWIENIA:</b></p><div class="box">{z.get('szczegoly')}</div><div style="margin-top:50px;text-align:right;">Podpis: __________________________</div></div></body></html>"""

def generuj_rozpiske_zbiorcza(data_cel, lista_zlecen, lista_odbiorow):
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>
    body{{font-family:sans-serif;padding:20px;color:#212529;}}
    .h1{{text-align:center;border-bottom:4px solid #000;padding-bottom:10px;margin-bottom:30px;text-transform:uppercase;}}
    .transport-block{{margin-bottom:40px; page-break-inside: avoid;}}
    .transport-title{{background:#f8f9fa;padding:12px;font-size:22px;font-weight:bold;border:2px solid #000;text-transform:uppercase;margin-bottom:10px;}}
    table{{width:100%;border-collapse:collapse;margin-bottom:20px;}}
    th, td{{border:1px solid #000;padding:10px;text-align:left;font-size:14px; vertical-align: top;}}
    th{{background:#e9ecef; font-weight:bold;}}
    .pilne{{color:#dc3545;font-weight:900;}}
    .odbior_label {{color: #7b1fa2; font-weight: bold;}}
    .details-cell {{ white-space: pre-wrap; font-family: inherit; font-size: 15px; line-height: 1.4; background-color: #fff; }}
    </style></head><body onload="window.print()">
    <div class="h1"><h1>PLAN TRANSPORTU - {data_cel}</h1></div>"""
    
    z_dnia = [z for z in lista_zlecen if z.get('termin') == data_cel]
    o_dnia = [o for o in lista_odbiorow if o.get('termin') == data_cel]
    grupy = {}
    for z in z_dnia:
        key = (z.get('auto', 'Brak'), z.get('kurs', 1))
        if key not in grupy: grupy[key] = {"prod": [], "odb": []}
        grupy[key]["prod"].append(z)
    for o in o_dnia:
        key = (o.get('auto', 'Brak'), o.get('kurs', 1))
        if key not in grupy: grupy[key] = {"prod": [], "odb": []}
        grupy[key]["odb"].append(o)
        
    if not grupy:
        html += f"<h2 style='text-align:center;'>Brak zadań na dzień {data_cel}.</h2>"
    else:
        for (tr, kr), content in grupy.items():
            label = f"{tr} / KURS NR {kr}" if tr in ["Auto 1", "Auto 2"] else tr
            html += f"""<div class="transport-block"><div class="transport-title">🚚 {label}</div>
            <table><tr><th style="width:40px">OK</th><th style="width:25%">KLIENT / MIEJSCE</th><th style="width:60%">PRODUKTY / UWAGI</th><th>STATUS</th></tr>"""
            for it in content["prod"]:
                p_m = '<span class="pilne">[🔥 PILNE]</span> ' if it.get('pilne') else ''
                st_m = "✅ GOTOWE" if it.get('status') == "Gotowe" else "⏳ PROD."
                html += f"<tr><td>[ ]</td><td>{p_m}<b>{it.get('klient')}</b></td><td class='details-cell'>{it.get('szczegoly','-')}</td><td>{st_m}</td></tr>"
            for it in content["odb"]:
                html += f"<tr><td>[ ]</td><td><span class='odbior_label'>🔄 ODBIÓR:</span><br><b>{it.get('miejsce')}</b></td><td class='details-cell' style='background:#f3e5f5;'>{it.get('towar','-')}</td><td>RELOG.</td></tr>"
            html += "</table></div>"
    html += "</body></html>"
    return html

if "print_order" not in st.session_state: st.session_state.print_order = None

# --- WIDOK DRUKOWANIA ---
if st.session_state.print_order is not None:
    z = st.session_state.print_order
    st.markdown('<style>[data-testid="stSidebar"] {display: none;} header {display: none;}</style>', unsafe_allow_html=True)
    if st.button("⬅️ Wróć do systemu"): st.session_state.print_order = None; st.rerun()
    st.markdown(f"<div style='border:4px solid black;padding:40px;background:white;'><h1>Zlecenie: {z.get('klient')}</h1><div style='white-space: pre-wrap; font-size: 18px;'>{z.get('szczegoly')}</div></div>", unsafe_allow_html=True)
    st.stop()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = "wgląd"

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
                    st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

# --- SKRÓTY UPRAWNIEŃ ---
is_readonly = st.session_state.role == "wgląd"
can_edit = st.session_state.role in ["admin", "edycja"]
is_admin = st.session_state.role == "admin"

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    st.write(f"Zalogowany: **{st.session_state.user}**")
    st.write(f"Rola: `{st.session_state.role.upper()}`")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()

    if is_admin:
        with st.expander("👥 Zarządzanie użytkownikami"):
            st.write("**Dodaj nowego:**")
            with st.form("add_u_f", clear_on_submit=True):
                new_u = st.text_input("Login"); new_p = st.text_input("Hasło"); new_r = st.selectbox("Rola:", ["edycja", "wgląd", "admin"])
                if st.form_submit_button("Dodaj użytkownika"):
                    if new_u: dane["uzytkownicy"][new_u] = {"pass": new_p, "role": new_r}; zapisz_dane(dane); st.rerun()
            st.divider(); st.write("**Istniejące konta:**")
            for usr, info in dane["uzytkownicy"].items():
                c1, c2, c3 = st.columns([2, 1.2, 0.8])
                c1.write(f"**{usr}**")
                with c2.popover("Edytuj"):
                    e_p = st.text_input("Hasło", info["pass"], key=f"up_{usr}")
                    e_r = st.selectbox("Rola", ["edycja", "wgląd", "admin"], ["edycja", "wgląd", "admin"].index(info["role"]), key=f"ur_{usr}")
                    if st.button("💾 Zapisz", key=f"us_{usr}"):
                        dane["uzytkownicy"][usr] = {"pass": e_p, "role": e_r}; zapisz_dane(dane); st.rerun()
                if usr != "admin":
                    if c3.button("X", key=f"del_{usr}"): del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()

        with st.expander("🛠️ Korekta i Przywracanie"):
            kat = st.selectbox("Dział:", ["Produkcja", "Odbiory", "Przyjęcia", "Dyspozycje"])
            if kat == "Produkcja":
                for i, item in enumerate(dane["zrealizowane"]):
                    st.markdown(f"**{item.get('klient')}**"); c1, c2 = st.columns(2)
                    if c1.button("↩️ Przywróć", key=f"res_p_{i}"): dane["w_realizacji"].append(dane["zrealizowane"].pop(i)); zapisz_dane(dane); st.rerun()
                    if c2.button("❌ Usuń", key=f"fdel_p_{i}"): dane["zrealizowane"].pop(i); zapisz_dane(dane); st.rerun()
            elif kat == "Odbiory":
                for i, item in enumerate(dane["odbiory_historia"]):
                    st.markdown(f"**{item.get('miejsce')}**"); c1, c2 = st.columns(2)
                    if c1.button("↩️ Przywróć", key=f"res_o_{i}"): dane["odbiory"].append(dane["odbiory_historia"].pop(i)); zapisz_dane(dane); st.rerun()
                    if c2.button("❌ Usuń", key=f"fdel_o_{i}"): dane["odbiory_historia"].pop(i); zapisz_dane(dane); st.rerun()
        st.divider()

    if can_edit:
        st.markdown('<div class="sidebar-header">➕ DODAJ NOWY WPIS</div>', unsafe_allow_html=True)
        typ = st.selectbox("Rodzaj:", ["Produkcja", "Odbiór (Powrót)", "Dostawa (PZ)", "Dyspozycja"])
        with st.form("f_add_new", clear_on_submit=True):
            if typ == "Produkcja":
                kl = st.text_input("👤 Klient"); tm = st.text_input("📅 Termin"); sz = st.text_area("📦 Produkty"); auto = st.selectbox("Transport:", OPCJE_TRANSPORTU); kr = st.selectbox("Kurs:", [1,2,3,4,5]); p = st.checkbox("🔥 PILNE")
                if st.form_submit_button("💾 Zapisz"):
                    if kl: dane["w_realizacji"].append({"klient":kl,"termin":tm,"szczegoly":sz,"auto":auto,"kurs":kr,"pilne":p,"status":"W produkcji","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ == "Odbiór (Powrót)":
                mj = st.text_input("📍 Skąd? (Dostawca)"); tm = st.text_input("📅 Data"); tw = st.text_area("📦 Co?"); auto = st.selectbox("Auto:", OPCJE_TRANSPORTU); kr = st.selectbox("Kurs:", [1,2,3,4,5])
                if st.form_submit_button("💾 Zapisz"):
                    if mj: dane["odbiory"].append({"miejsce":mj,"termin":tm,"towar":tw,"auto":auto,"kurs":kr,"status":"W toku","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            elif typ == "Dostawa (PZ)":
                ds = st.text_input("🏢 Dostawca"); tm = st.text_input("📅 Data"); op = st.text_area("📦 Co przyjeżdża?")
                if st.form_submit_button("💾 Zapisz"):
                    if ds: dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()
            else:
                tyt = st.text_input("🎯 Tytuł"); tm = st.text_input("📅 Termin"); op = st.text_area("📝 Opis")
                if st.form_submit_button("💾 Zapisz"):
                    if tyt: dane["dyspozycje"].append({"tytul":tyt,"termin":tm,"opis":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user}); zapisz_dane(dane); st.rerun()

    st.markdown('<div class="sidebar-print-header">🖨️ DRUKOWANIE PLANU DNIA</div>', unsafe_allow_html=True)
    data_do_druku = st.text_input("Data do rozpiski:", value=datetime.now().strftime("%d.%m"))
    st.download_button(label="📥 Pobierz Rozpiskę (Plan)", data=generuj_rozpiske_zbiorcza(data_do_druku, dane["w_realizacji"], dane["odbiory"]), file_name=f"Rozpiska_{data_do_druku}.html", mime="text/html")

    if is_admin:
        st.divider()
        if st.button("🔥 RESETUJ WSZYSTKIE DANE"):
            for k in ["w_realizacji","zrealizowane","przyjecia","przyjecia_historia","dyspozycje","dyspozycje_historia","odbiory","odbiory_historia","tablica"]: dane[k] = []
            zapisz_dane(dane); st.rerun()

# --- 5. TERMINARZ TYGODNIOWY ---
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
        grupy_transp = {}
        for z in dane["w_realizacji"]:
            try:
                parts = z.get('termin','').split('.'); zd, zm = int(parts[0]), int(parts[1])
                if zd == dv and zm == mv:
                    k_tr = (z.get('auto','Brak'), z.get('kurs',1)); 
                    if k_tr not in grupy_transp: grupy_transp[k_tr] = {"prod": [], "odb": []}
                    grupy_transp[k_tr]["prod"].append(z)
            except: pass
        for o in dane["odbiory"]:
            try:
                parts = o.get('termin','').split('.'); zd, zm = int(parts[0]), int(parts[1])
                if zd == dv and zm == mv:
                    k_tr = (o.get('auto','Brak'), o.get('kurs',1)); 
                    if k_tr not in grupy_transp: grupy_transp[k_tr] = {"prod": [], "odb": []}
                    grupy_transp[k_tr]["odb"].append(o)
            except: pass
        for (tr, kr), content in grupy_transp.items():
            all_ready = all(it.get('status') == 'Gotowe' for it in content["prod"])
            css_cl = "cal-entry-ready" if (all_ready and content["prod"]) else "cal-entry-out"
            label = f"{tr} / K{kr}" if tr in ["Auto 1", "Auto 2"] else (f"{tr}" if tr != "Brak" else "Inne")
            tooltip = "ZLECENIA:&#10;"
            for it in content["prod"]: tooltip += f"• {it.get('klient')} ({it.get('szczegoly','')[:30]}...)&#10;"
            if content["odb"]:
                tooltip += "&#10;🔄 ODBIORY:&#10;"
                for it in content["odb"]: tooltip += f"• {it.get('miejsce')} ({it.get('towar','')[:30]}...)&#10;"
            st.markdown(f"<div class='{css_cl}' title='{tooltip}'>{label} ({len(content['prod'])+len(content['odb'])})</div>", unsafe_allow_html=True)
            if content["odb"]: st.markdown(f"<div class='cal-entry-return' style='height:3px; margin-top:-4px;'></div>", unsafe_allow_html=True)
        for p in dane["przyjecia"]:
            try:
                parts = p.get('termin','').split('.'); pd, pm = int(parts[0]), int(parts[1])
                if pd == dv and pm == mv: st.markdown(f"<div class='cal-entry-in' title='{p.get('towar')}'>P: {p.get('dostawca')}</div>", unsafe_allow_html=True)
            except: pass
        for d in dane["dyspozycje"]:
            try:
                parts = d.get('termin','').split('.'); dd, dm = int(parts[0]), int(parts[1])
                if dd == dv and dm == mv: st.markdown(f"<div class='cal-entry-task' title='{d.get('opis')}'>D: {d.get('tytul')}</div>", unsafe_allow_html=True)
            except: pass

# --- 6. TABELE REALIZACJI ---
st.markdown('<div class="section-header">Tabele Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Szukaj...", "").lower()
t_prod, t_odb, t_log, t_dysp = st.tabs(["🏭 Produkcja", "🔄 Odbiory (Powroty)", "🚚 Przyjęcia (PZ)", "📋 Dyspozycje"])

with t_prod:
    tp1, tp_planned, tp2 = st.tabs(["Aktywne", "📂 Do zaplanowania", "Historia"])
    z_aktywne = [z for z in dane["w_realizacji"] if str(z.get('termin','')).strip()]
    z_do_zaplanowania = [z for z in dane["w_realizacji"] if not str(z.get('termin','')).strip()]
    with tp1:
        if not z_aktywne: st.info("Brak aktywnych zleceń.")
        else:
            hc = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
            hc[0].markdown('<div class="label-text">Klient</div>', unsafe_allow_html=True); hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True)
            hc[2].markdown(f'<div class="label-text">{"Produkty / Szczegóły" if is_readonly else "Menu"}</div>', unsafe_allow_html=True)
            hc[3].markdown(f'<div class="label-text">{"Status" if is_readonly else "Akcja"}</div>', unsafe_allow_html=True)
            last_g = None
            for i, z in enumerate(dane["w_realizacji"]):
                if not str(z.get('termin','')).strip() or (search and search not in str(z).lower()): continue
                curr_g = (z.get('termin'), z.get('auto'), z.get('kurs'))
                if curr_g != last_g: st.markdown(f"<div class='table-group-header'>📅 {z.get('termin')} | {z.get('auto')} (K{z.get('kurs')})</div>", unsafe_allow_html=True); last_g = curr_g
                c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6]); status = z.get('status','W produkcji'); b_st = '<span class="badge-status-ready">✅ GOTOWE</span>' if status=='Gotowe' else '<span class="badge-status-prod">⏳ PRODUKCJA</span>'
                c[0].markdown(f"**{z.get('klient')}** {'🔥' if z.get('pilne') else ''}<br>{b_st}", unsafe_allow_html=True); c[1].write(z.get('termin'))
                u_id = f"z_{z.get('data_p')}_{i}".replace(':','').replace(' ','_')
                if is_readonly: c[2].markdown(f"<div class='readonly-text'>{z.get('szczegoly','-')}</div>", unsafe_allow_html=True)
                else:
                    with c[2].popover("Opcje"):
                        st.download_button("🖨️ Karta", generuj_html_do_druku(z), f"Karta_{u_id}.html", "text/html", key=f"dl_{u_id}")
                        nt = st.text_input("Data", z.get('termin'), key=f"et_{u_id}"); na = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(z.get('auto','Brak')), key=f"ea_{u_id}"); nk = st.selectbox("Kurs", [1,2,3,4,5], int(z.get('kurs',1))-1, key=f"k_{u_id}"); ns = st.text_area("Produkty", z.get('szczegoly',''), key=f"s_{u_id}")
                        if st.button("Zapisz zmiany", key=f"sv_{u_id}"): dane["w_realizacji"][i].update({"termin":nt,"auto":na,"kurs":nk,"szczegoly":ns}); zapisz_dane(dane); st.rerun()
                    if status != "Gotowe":
                        if c[3].button("ZROBIONE", key=f"done_{u_id}"): dane["w_realizacji"][i]['status']="Gotowe"; zapisz_dane(dane); st.rerun()
                    else:
                        if c[3].button("WYŚLIJ", key=f"send_{u_id}"): dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
                    if c[4].button("X", key=f"x_{u_id}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
    with tp_planned:
        for i, z in enumerate(dane["w_realizacji"]):
            if str(z.get('termin','')).strip() or (search and search not in str(z).lower()): continue
            c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6]); c[0].markdown(f"**{z.get('klient')}**<br><span style='color:red;'>BRAK DATY</span>", unsafe_allow_html=True)
            u_id = f"plan_{z.get('data_p')}_{i}".replace(':','').replace(' ','_')
            if is_readonly: c[2].markdown(f"<div class='readonly-text'>{z.get('szczegoly','-')}</div>", unsafe_allow_html=True)
            else:
                with c[2].popover("Zaplanuj"):
                    nt = st.text_input("Data", "", key=f"etp_{u_id}"); na = st.selectbox("Auto", OPCJE_TRANSPORTU, key=f"eap_{u_id}"); nk = st.selectbox("Kurs", [1,2,3,4,5], key=f"ekp_{u_id}"); ns = st.text_area("Produkty", z.get('szczegoly',''), key=f"sp_{u_id}")
                    if st.button("Zapisz i zaplanuj", key=f"svp_{u_id}"): dane["w_realizacji"][i].update({"termin":nt,"auto":na,"kurs":nk,"szczegoly":ns}); zapisz_dane(dane); st.rerun()
                if c[4].button("X", key=f"xp_{u_id}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
    with tp2: st.dataframe(dane["zrealizowane"][::-1], use_container_width=True)

with t_odb:
    to1, to2 = st.tabs(["Aktywne", "Historia"])
    with to1:
        if not dane["odbiory"]: st.info("Brak aktywnych odbiorów.")
        else:
            hc = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
            hc[0].markdown('<div class="label-text">Dostawca / Skąd</div>', unsafe_allow_html=True); hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True); hc[2].markdown(f'<div class="label-text">{"Co odebrać?" if is_readonly else "Menu"}</div>', unsafe_allow_html=True)
            last_o = None
            for i, o in enumerate(dane["odbiory"]):
                if search and search not in str(o).lower(): continue
                curr_g = (o.get('termin'), o.get('auto'), o.get('kurs'))
                if curr_g != last_o: st.markdown(f"<div class='table-group-header'>🔄 {o.get('termin')} | Auto: {o.get('auto')} (K{o.get('kurs')})</div>", unsafe_allow_html=True); last_o = curr_g
                c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6]); b_st = '<span class="badge-status-return">🔄 W TOKU</span>'
                c[0].markdown(f"**{o.get('miejsce')}**<br>{b_st}", unsafe_allow_html=True); c[1].write(o.get('termin'))
                u_id = f"o_{o.get('data_p')}_{i}".replace(':','').replace(' ','_')
                if is_readonly: c[2].markdown(f"<div class='readonly-text'>{o.get('towar','-')}</div>", unsafe_allow_html=True)
                else:
                    with c[2].popover("Menu"):
                        nt = st.text_input("Data", o.get('termin'), key=f"ot_{u_id}"); na = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(o.get('auto','Brak')), key=f"oa_{u_id}"); nk = st.selectbox("Kurs", [1,2,3,4,5], int(o.get('kurs',1))-1, key=f"ok_{u_id}"); ntow = st.text_area("Co?", o.get('towar',''), key=f"ow_{u_id}")
                        if st.button("Zapisz", key=f"os_{u_id}"): dane["odbiory"][i].update({"termin":nt,"auto":na,"kurs":nk,"towar":ntow}); zapisz_dane(dane); st.rerun()
                    if c[3].button("GOTOWE", key=f"og_{u_id}"): dane["odbiory_historia"].append(dane["odbiory"].pop(i)); zapisz_dane(dane); st.rerun()
                    if c[4].button("X", key=f"ox_{u_id}"): dane["odbiory"].pop(i); zapisz_dane(dane); st.rerun()
    with to2: st.dataframe(dane["odbiory_historia"][::-1], use_container_width=True)

with t_log:
    tl1, tl2 = st.tabs(["Aktywne", "Historia"])
    with tl1:
        if not dane["przyjecia"]: st.info("Brak aktywnych dostaw.")
        else:
            hc = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
            hc[0].markdown('<div class="label-text">Dostawca</div>', unsafe_allow_html=True); hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True); hc[2].markdown(f'<div class="label-text">{"Zawartość" if is_readonly else "Menu"}</div>', unsafe_allow_html=True)
            last_p = None
            for i, p in enumerate(dane["przyjecia"]):
                if search and search not in str(p).lower(): continue
                if p.get('termin') != last_p: st.markdown(f"<div class='table-group-header'>🚚 {p.get('termin')} | Dostawy towarów</div>", unsafe_allow_html=True); last_p = p.get('termin')
                c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6]); b_st = '<span class="badge-status-prod">🚚 OCZEKUJE</span>'
                c[0].markdown(f"**{p.get('dostawca')}**<br>{b_st}", unsafe_allow_html=True); c[1].write(p.get('termin'))
                u_id = f"p_{p.get('data_p')}_{i}".replace(':','').replace(' ','_')
                if is_readonly: c[2].markdown(f"<div class='readonly-text'>{p.get('towar','-')}</div>", unsafe_allow_html=True)
                else:
                    with c[2].popover("Menu"):
                        nt = st.text_input("Data", p.get('termin'), key=f"pt_{u_id}"); no = st.text_area("Towar", p.get('towar',''), key=f"po_{u_id}")
                        if st.button("Zapisz", key=f"ps_{u_id}"): dane["przyjecia"][i].update({"termin":nt,"towar":no}); zapisz_dane(dane); st.rerun()
                    if c[3].button("OK", key=f"pok_{u_id}"): dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
                    if c[4].button("X", key=f"px_{u_id}"): dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()
    with tl2: st.dataframe(dane["przyjecia_historia"][::-1], use_container_width=True)

with t_dysp:
    td1, td2 = st.tabs(["Aktywne", "Historia"])
    with td1:
        if not dane["dyspozycje"]: st.info("Brak aktywnych zadań.")
        else:
            hc = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
            hc[0].markdown('<div class="label-text">Tytuł zadania</div>', unsafe_allow_html=True); hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True); hc[2].markdown(f'<div class="label-text">{"Opis" if is_readonly else "Menu"}</div>', unsafe_allow_html=True)
            last_d = None
            for i, d in enumerate(dane["dyspozycje"]):
                if search and search not in str(d).lower(): continue
                if d.get('termin') != last_d: st.markdown(f"<div class='table-group-header'>📋 {d.get('termin')} | Zadania wewnętrzne</div>", unsafe_allow_html=True); last_d = d.get('termin')
                c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6]); b_st = '<span class="badge-status-prod">📋 DO WYKONANIA</span>'
                c[0].markdown(f"**{d.get('tytul')}**<br>{b_st}", unsafe_allow_html=True); c[1].write(d.get('termin'))
                u_id = f"d_{d.get('data_p')}_{i}".replace(':','').replace(' ','_')
                if is_readonly: c[2].markdown(f"<div class='readonly-text'>{d.get('opis','-')}</div>", unsafe_allow_html=True)
                else:
                    with c[2].popover("Menu"):
                        nt = st.text_input("Termin", d.get('termin'), key=f"dt_{u_id}"); no = st.text_area("Opis", d.get('opis',''), key=f"do_{u_id}")
                        if st.button("Zapisz", key=f"ds_{u_id}"): dane["dyspozycje"][i].update({"termin":nt,"opis":no}); zapisz_dane(dane); st.rerun()
                    if c[3].button("GOTOWE", key=f"dg_{u_id}"): dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
                    if c[4].button("X", key=f"dx_{u_id}"): dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()
    with td2: st.dataframe(dane["dyspozycje_historia"][::-1], use_container_width=True)

# --- 7. TABLICA OGŁOSZEŃ (NA STAŁE NA DOLE) ---
st.markdown("<br><hr style='border: 2px solid #343a40;'><br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📌 Tablica Ogłoszeń i Komunikaty</div>', unsafe_allow_html=True)

if can_edit:
    with st.form("bottom_note_form", clear_on_submit=True):
        nowa_tresc = st.text_area("Dodaj nową informację dla wszystkich pracowników:", placeholder="Wpisz treść ogłoszenia...")
        if st.form_submit_button("➕ Opublikuj na tablicy"):
            if nowa_tresc:
                dane["tablica"].append({"tresc": nowa_tresc, "data": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()

if not dane["tablica"]:
    st.info("Tablica jest pusta.")
else:
    notes_cols = st.columns(3)
    for i, note in enumerate(reversed(dane["tablica"])):
        real_idx = len(dane["tablica"]) - 1 - i
        with notes_cols[i % 3]:
            st.markdown(f"""<div class="note-card">{note['tresc']}<div class="note-meta">Dodano: {note['data']} przez: {note['autor']}</div></div>""", unsafe_allow_html=True)
            if can_edit:
                if st.button(f"Usuń", key=f"del_note_bot_{real_idx}"):
                    dane["tablica"].pop(real_idx); zapisz_dane(dane); st.rerun()
