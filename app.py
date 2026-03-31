import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURACJA I STYLIZACJA (TWOJA ORYGINALNA) ---
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

/* STRUKTURA KALENDARZA */
.week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; align-items: stretch; margin-top: 15px; margin-bottom: 25px; }
.day-col { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; flex-direction: column; min-height: 150px; }
.day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 12px; padding-bottom: 6px; }
.day-name { font-weight: 700; font-size: 13px; color: #495057; }
.day-date { font-size: 11px; color: #868e96; }

.transport-group { background-color: #f8f9fa; border: 1px dashed #ced4da; border-radius: 6px; padding: 4px; margin-bottom: 8px; }
.transport-group-header { font-size: 9px; font-weight: 800; color: #495057; text-transform: uppercase; margin-bottom: 4px; text-align: center; border-bottom: 1px solid #dee2e6; padding-bottom: 2px; }

.cal-entry-out { cursor: help; font-size: 10px; background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }
.cal-entry-ready { cursor: help; font-size: 10px; background: #d4edda; color: #155724; border-left: 3px solid #28a745; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }
.cal-entry-in { cursor: help; font-size: 10px; background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }
.cal-entry-task { cursor: help; font-size: 10px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }

.table-group-header { background-color: #e9ecef; color: #212529; padding: 6px 12px; font-weight: 700; font-size: 12px; border-radius: 4px; margin: 15px 0 8px 0; border-left: 4px solid #007bff; }

.badge-urgent { background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 5px; }
.badge-status-prod { background-color: #ffc107; color: #212529; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-ready { background-color: #28a745; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}

.label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; border-bottom: 1px solid #dee2e6; padding-bottom: 4px;}
button[data-baseweb="tab"] { font-size: 16px !important; font-weight: 600 !important; }

/* TWARDE WYRÓWNANIE DO ŚRODKA */
div[data-testid="stHorizontalBlock"] { align-items: center !important; }
div[data-testid="stHorizontalBlock"] p { margin-bottom: 0 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH I SORTOWANIE (TWOJA ORYGINALNA) ---
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

# --- FUNKCJA GENERUJĄCA PLIK DO DRUKU (TWOJA ORYGINALNA) ---
def generuj_html_do_druku(z):
    pilne_html = '<div class="print-urgent">🔥 ZLECENIE PILNE 🔥</div>' if z.get('pilne') else ''
    auto_val = z.get('auto', 'Brak')
    k_val = z.get('kurs', 1)
    transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    return f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><title>Zlecenie - {z.get('klient', 'Brak')}</title><style>body {{ font-family: 'Arial', sans-serif; padding: 20px; color: #212529; background: white; }} .print-card {{ border: 4px solid #212529; padding: 40px; max-width: 900px; margin: 0 auto; }} .print-title {{ text-align: center; font-size: 32px; font-weight: 900; border-bottom: 4px solid #212529; padding-bottom: 15px; margin-bottom: 30px; text-transform: uppercase; }} .print-row {{ display: flex; margin-bottom: 25px; }} .print-col {{ flex: 1; padding-right: 20px; }} .print-label {{ font-size: 14px; font-weight: 700; color: #6c757d; text-transform: uppercase; margin-bottom: 5px; }} .print-val {{ font-size: 24px; font-weight: 800; }} .print-val-text {{ font-size: 20px; white-space: pre-wrap; font-weight: 500; border: 1px solid #dee2e6; padding: 15px; border-radius: 6px; background-color: #f8f9fa; }} .print-urgent {{ color: #dc3545; border: 5px solid #dc3545; font-size: 28px; font-weight: 900; text-align: center; padding: 15px; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 2px; }} @media print {{ body {{ padding: 0; }} .print-card {{ border: none; padding: 0; max-width: 100%; }} .print-val-text {{ border: 2px solid #000; background-color: transparent; }} }}</style></head><body onload="window.print()"><div class="print-card">{pilne_html}<div class="print-title">Karta Zlecenia Produkcyjnego</div><div class="print-row"><div class="print-col"><div class="print-label">Klient / Firma</div><div class="print-val">{z.get('klient', '-')}</div></div><div class="print-col"><div class="print-label">Termin Realizacji</div><div class="print-val">{z.get('termin', '-')}</div></div></div><div class="print-row"><div class="print-col"><div class="print-label">Transport / Logistyka</div><div class="print-val">{transport_str}</div></div><div class="print-col"><div class="print-label">Data dodania (Kto dodał)</div><div class="print-val" style="font-size: 18px;">{z.get('data_p', '-')} ({z.get('autor', '-')})</div></div></div><div style="margin-bottom: 30px; margin-top: 30px;"><div class="print-label">Specyfikacja Ogólna</div><div class="print-val-text">{z.get('opis', 'Brak specyfikacji')}</div></div><div><div class="print-label">Szczegóły Zamówienia (Ilości, Wymiary)</div><div class="print-val-text">{z.get('szczegoly', 'Brak szczegółów')}</div></div><div style="margin-top: 120px; text-align: right;"><div style="display: inline-block; width: 350px; border-top: 2px solid #000; padding-top: 10px; text-align: center; color: #212529; font-weight: bold; font-size: 16px;">Podpis pracownika (Zrealizowano)</div></div></div></body></html>"""

# --- !!! NOWA FUNKCJA: ROZPISKA ZBIORCZA !!! ---
def generuj_rozpiske_zbiorcza(data_cel, lista_zlecen):
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>
    body{{font-family:sans-serif;padding:20px;color:#212529;}}
    .h1{{text-align:center;border-bottom:4px solid #000;padding-bottom:10px;margin-bottom:30px;text-transform:uppercase;}}
    .transport-block{{margin-bottom:40px; page-break-inside: avoid;}}
    .transport-title{{background:#f8f9fa;padding:12px;font-size:22px;font-weight:bold;border:2px solid #000;text-transform:uppercase;margin-bottom:10px;}}
    table{{width:100%;border-collapse:collapse;}}
    th, td{{border:1px solid #000;padding:10px;text-align:left;font-size:14px;}}
    th{{background:#e9ecef; font-weight:bold;}}
    .pilne{{color:#dc3545;font-weight:900;}}
    .check{{width:40px;text-align:center;font-weight:bold;font-size:20px;}}
    </style></head><body onload="window.print()">
    <div class="h1"><h1>PLAN TRANSPORTU - {data_cel}</h1></div>"""
    zlecenia_dnia = [z for z in lista_zlecen if z.get('termin') == data_cel]
    grupy = {}
    for z in zlecenia_dnia:
        key = (z.get('auto', 'Brak'), z.get('kurs', 1))
        if key not in grupy: grupy[key] = []
        grupy[key].append(z)
    if not zlecenia_dnia: html += "<h2 style='text-align:center;'>Brak zaplanowanych wysyłek na ten dzień.</h2>"
    else:
        for (tr, kr), items in grupy.items():
            label = f"{tr} / KURS NR {kr}" if tr in ["Auto 1", "Auto 2"] else tr
            html += f"""<div class="transport-block"><div class="transport-title">🚚 {label}</div>
            <table><tr><th class="check">OK</th><th>KLIENT</th><th>SPECYFIKACJA</th><th>ILOŚCI / SZCZEGÓŁY</th><th>STATUS</th></tr>"""
            for it in items:
                p_mark = '<span class="pilne">[🔥 PILNE]</span> ' if it.get('pilne') else ''
                st_mark = "✅ GOTOWE" if it.get('status') == "Gotowe" else "⏳ W PRODUKCJI"
                html += f"<tr><td class='check'>[ ]</td><td>{p_mark}<b>{it.get('klient')}</b></td><td>{it.get('opis','-')}</td><td>{it.get('szczegoly','-')}</td><td>{st_mark}</td></tr>"
            html += "</table></div>"
    html += "</body></html>"
    return html

# Zmienne sesyjne
if "print_order" not in st.session_state: st.session_state.print_order = None

# --- WIDOK DRUKOWANIA (TWOJA ORYGINALNA LOGIKA) ---
if st.session_state.print_order is not None:
    z = st.session_state.print_order
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;} header {display: none;} .stApp {background-color: white;} @media print { .no-print {display: none !important;} body {background-color: white;} } .print-card { border: 4px solid #212529; padding: 40px; margin: 20px auto; max-width: 900px; background: white; color: #212529; font-family: 'Arial', sans-serif; } .print-title { text-align: center; font-size: 36px; font-weight: 900; border-bottom: 4px solid #212529; padding-bottom: 15px; margin-bottom: 30px; text-transform: uppercase; } .print-row { display: flex; margin-bottom: 25px; } .print-col { flex: 1; padding-right: 20px;} .print-label { font-size: 14px; font-weight: 700; color: #6c757d; text-transform: uppercase; margin-bottom: 5px; } .print-val { font-size: 26px; font-weight: 800; } .print-val-text { font-size: 22px; white-space: pre-wrap; font-weight: 500; } .print-urgent { color: #dc3545; border: 5px solid #dc3545; font-size: 30px; font-weight: 900; text-align: center; padding: 15px; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 2px;}</style>""", unsafe_allow_html=True)
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("⬅️ Wróć do systemu"): st.session_state.print_order = None; st.rerun()
    with col_btn2: st.info("🖨️ Naciśnij Ctrl + P, aby wydrukować tę kartę.")
    st.markdown('</div>', unsafe_allow_html=True)
    pilne_html = '<div class="print-urgent">🔥 ZLECENIE PILNE 🔥</div>' if z.get('pilne') else ''
    auto_val = z.get('auto', 'Brak'); k_val = z.get('kurs', 1); transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    html_karta = f"""<div class="print-card">{pilne_html}<div class="print-title">Karta Zlecenia Produkcyjnego</div><div class="print-row"><div class="print-col"><div class="print-label">Klient / Firma</div><div class="print-val">{z.get('klient', '-')}</div></div><div class="print-col"><div class="print-label">Termin Realizacji</div><div class="print-val">{z.get('termin', '-')}</div></div></div><div class="print-row"><div class="print-col"><div class="print-label">Transport / Logistyka</div><div class="print-val">{transport_str}</div></div><div class="print-col"><div class="print-label">Data dodania</div><div class="print-val" style="font-size: 20px;">{z.get('data_p', '-')} ({z.get('autor', '-')})</div></div></div><hr style="border-top: 3px dashed #dee2e6; margin: 30px 0;"><div style="margin-bottom: 30px;"><div class="print-label">Specyfikacja Ogólna</div><div class="print-val-text">{z.get('opis', 'Brak specyfikacji')}</div></div><div><div class="print-label">Szczegóły Zamówienia</div><div class="print-val-text">{z.get('szczegoly', 'Brak szczegółów')}</div></div><div style="margin-top: 100px; text-align: right;"><div style="display: inline-block; width: 300px; border-top: 2px solid #000; padding-top: 10px; text-align: center; color: #212529; font-weight: bold; font-size: 16px;">Podpis pracownika</div></div></div>"""
    st.markdown(html_karta, unsafe_allow_html=True)
    st.stop()  

# --- 3. SYSTEM LOGOWANIA (TWOJA ORYGINALNA LOGIKA Z LOGO) ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        try: st.image("logo.png", use_container_width=True)
        except: st.warning("Ładowanie logo...")
        st.markdown("<p style='text-align: center; color: #6c757d; font-size: 16px; margin-top: 10px; margin-bottom: 25px; font-weight: 600;'>System Zarządzania Produkcją i Logistyką</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("👤 Login użytkownika")
            p = st.text_input("🔒 Hasło dostępu", type="password")
            if st.form_submit_button("Zaloguj się do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p: st.session_state.user = u; st.rerun()
                else: st.error("Błąd logowania.")
    st.stop()

# --- 4. PANEL BOCZNY (TWOJA ORYGINALNA LOGIKA) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    if st.session_state.user == "admin":
        with st.expander("👥 Zarządzanie użytkownikami"):
            with st.form("add_u_f", clear_on_submit=True):
                new_u = st.text_input("Login"); new_p = st.text_input("Hasło")
                if st.form_submit_button("Dodaj"):
                    if new_u: dane["uzytkownicy"][new_u] = new_p; zapisz_dane(dane); st.rerun()
            for usr in list(dane["uzytkownicy"].keys()):
                if usr != "admin":
                    if st.button(f"Usuń: {usr}", key=f"d_u_{usr}"): del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()
        st.divider()
    st.markdown('<div class="sidebar-header">➕ DODAJ NOWY WPIS</div>', unsafe_allow_html=True)
    typ = st.selectbox("Rodzaj:", ["Produkcja", "Dostawa (PZ)", "Dyspozycja"])
    with st.form("f_add", clear_on_submit=True):
        if typ == "Produkcja":
            kl = st.text_input("👤 Klient"); tm = st.text_input("📅 Termin (np. 31.03)"); op = st.text_area("📝 Specyfikacja"); sz = st.text_area("📦 Ilości"); auto = st.selectbox("Transport:", OPCJE_TRANSPORTU); kr = st.selectbox("Kurs:", [1,2,3,4,5]); p = st.checkbox("🔥 PILNE")
            if st.form_submit_button("💾 Zapisz"):
                dane["w_realizacji"].append({"klient": kl, "termin": tm, "opis": op, "szczegoly": sz, "auto": auto, "kurs": kr, "pilne": p, "status": "W produkcji", "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                zapisz_dane(dane); st.rerun()
        elif typ == "Dostawa (PZ)":
            ds = st.text_input("🏢 Dostawca"); tm = st.text_input("📅 Data"); op = st.text_area("📦 Towar")
            if st.form_submit_button("💾 Zapisz"):
                dane["przyjecia"].append({"dostawca": ds, "termin": tm, "towar": op, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()
        else:
            tyt = st.text_input("🎯 Tytuł"); tm = st.text_input("📅 Termin"); op = st.text_area("📝 Opis")
            if st.form_submit_button("💾 Zapisz"):
                dane["dyspozycje"].append({"tytul": tyt, "termin": tm, "opis": op, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}); zapisz_dane(dane); st.rerun()
    if st.session_state.user == "admin":
        st.divider()
        with st.expander("⚙️ System"):
            if st.button("🔥 RESETUJ WSZYSTKIE DANE"):
                for k in ["w_realizacji", "zrealizowane", "przyjecia", "przyjecia_historia", "dyspozycje", "dyspozycje_historia"]: dane[k] = []
                zapisz_dane(dane); st.rerun()

# --- 5. STATYSTYKI ---
st.markdown('<div class="section-header">Podsumowanie</div>', unsafe_allow_html=True)
c_s1, c_s2, c_s3 = st.columns(3)
c_s1.metric("📦 Zlecenia (Aktywne)", len(dane["w_realizacji"]))
c_s2.metric("🚚 Dostawy", len(dane["przyjecia"])); c_s3.metric("📋 Dyspozycje", len(dane["dyspozycje"]))

# --- 6. TERMINARZ TYGODNIOWY (TWOJA ORYGINALNA LOGIKA) ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "week_offset" not in st.session_state: st.session_state.week_offset = 0
c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1: 
    if st.button("← Poprzedni"): st.session_state.week_offset -= 7; st.rerun()
with c_nav3: 
    if st.button("Następny →"): st.session_state.week_offset += 7; st.rerun()
today = datetime.now(); start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=st.session_state.week_offset); dates_in_week = [(start_of_week + timedelta(days=i)) for i in range(7)]
def parse_d(txt):
    try: parts = str(txt).split("."); return int(parts[0]), int(parts[1])
    except: return None, None
cols = st.columns(7)
for i, date in enumerate(dates_in_week):
    with cols[i]:
        st.markdown(f"<div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{date.strftime('%d.%m')}</div></div>", unsafe_allow_html=True)
        dv, mv = date.day, date.month
        grupy_dnia = {}
        for z in dane["w_realizacji"]:
            zd, zm = parse_d(z.get('termin', ''))
            if zd == dv and zm == mv:
                key = (z.get('auto', 'Brak'), z.get('kurs', 1))
                if key not in grupy_dnia: grupy_dnia[key] = []
                grupy_dnia[key].append(z)
        for (tr, kr), items in grupy_dnia.items():
            if tr != "Brak":
                label = f"{tr} / K{kr}" if tr in ["Auto 1", "Auto 2"] else tr
                st.markdown(f'<div class="transport-group"><div class="transport-group-header">{label}</div>', unsafe_allow_html=True)
            for it in items:
                status = it.get('status','W produkcji'); css_class = "cal-entry-ready" if status == "Gotowe" else "cal-entry-out"
                tooltip = f"SPECYFIKACJA:&#10;{str(it.get('opis','')).replace('\"','&quot;')}&#10;&#10;SZCZEGÓŁY:&#10;{str(it.get('szczegoly','')).replace('\"','&quot;')}"
                st.markdown(f'<div class="{css_class}" title="{tooltip}">{"✅ " if status=="Gotowe" else ""}{it.get("klient","-")}</div>', unsafe_allow_html=True)
            if tr != "Brak": st.markdown('</div>', unsafe_allow_html=True)

# --- !!! NOWA SEKCJA W TWOIM KODZIE: DRUKOWANIE ROZPISKI !!! ---
st.markdown('<div class="section-header">Centrum Rozpiski Transportu</div>', unsafe_allow_html=True)
c_r1, c_r2 = st.columns([1, 2])
with c_r1:
    data_do_druku = st.text_input("Podaj datę do rozpiski (np. 31.03)", value=datetime.now().strftime("%d.%m"))
with c_r2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.download_button(label="🖨️ Pobierz ZBIORCZĄ ROZPISKĘ na ten dzień", data=generuj_rozpiske_zbiorcza(data_do_druku, dane["w_realizacji"]), file_name=f"Rozpiska_{data_do_druku}.html", mime="text/html"):
        st.success("Rozpiska gotowa do druku!")

# --- 7. TABELE REALIZACJI (TWOJA ORYGINALNA STRUKTURA KOLUMN) ---
st.markdown('<div class="section-header">Tabele Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Wyszukaj...", "").lower()
t_prod, t_log, t_dysp = st.tabs(["🏭 Produkcja", "🚚 Przyjęcia (PZ)", "📋 Dyspozycje"])

with t_prod:
    tp1, tp2 = st.tabs(["Aktywne Zlecenia", "Zrealizowane / Historia"])
    with tp1:
        if not dane["w_realizacji"]: st.info("Brak aktywnych zleceń.")
        else:
            hc = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
            hc[0].markdown('<div class="label-text">Klient</div>', unsafe_allow_html=True); hc[1].markdown('<div class="label-text">Termin</div>', unsafe_allow_html=True); hc[2].markdown('<div class="label-text">Dodano</div>', unsafe_allow_html=True); hc[3].markdown('<div class="label-text">Opcje / Druk</div>', unsafe_allow_html=True); hc[4].markdown('<div class="label-text">Status</div>', unsafe_allow_html=True)
            last_group = None
            for i, z in enumerate(dane["w_realizacji"]):
                if search and search not in str(z).lower(): continue
                curr_group = (z.get('termin'), z.get('auto', 'Brak'), z.get('kurs', 1))
                if curr_group != last_group:
                    t_label = z.get('auto', 'Brak') if z.get('auto', 'Brak') != "Brak" else "Bez transportu"
                    k_label = f" / Kurs {z.get('kurs', 1)}" if z.get('auto') in ["Auto 1", "Auto 2"] else ""
                    st.markdown(f'<div class="table-group-header">📅 {z.get("termin")} | {t_label}{k_label}</div>', unsafe_allow_html=True)
                    last_group = curr_group
                c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
                status = z.get('status', 'W produkcji'); b_status = '<span class="badge-status-ready">✅ GOTOWE</span>' if status == 'Gotowe' else '<span class="badge-status-prod">⏳ PRODUKCJA</span>'
                c[0].markdown(f"**{z.get('klient')}** {'🔥' if z.get('pilne') else ''} <br>{b_status}", unsafe_allow_html=True); c[1].write(f"{z.get('termin')}"); c[2].write(f"{z.get('data_p')}")
                with c[3].popover("Edytuj / Drukuj"):
                    st.download_button(label="🖨️ Pobierz Kartę", data=generuj_html_do_druku(z), file_name=f"Karta_{i}.html", mime="text/html", key=f"dl_{i}")
                    if st.button("👁️ Podgląd", key=f"pv_{i}"): st.session_state.print_order = z; st.rerun()
                    st.markdown("---")
                    nt = st.text_input("Data:", value=z.get('termin', ''), key=f"et_{i}")
                    na = st.selectbox("Transport:", OPCJE_TRANSPORTU, index=OPCJE_TRANSPORTU.index(z.get('auto', 'Brak')), key=f"ea_{i}")
                    nk = st.selectbox("Kurs:", [1,2,3,4,5], index=int(z.get('kurs', 1))-1, key=f"ek_{i}")
                    no = st.text_area("Specyfikacja", value=z.get('opis',''), key=f"eo_{i}")
                    ns = st.text_area("Ilości", value=z.get('szczegoly',''), key=f"es_{i}")
                    if st.button("Zapisz", key=f"eb_{i}"): dane["w_realizacji"][i].update({"termin":nt,"auto":na,"kurs":nk,"opis":no,"szczegoly":ns}); zapisz_dane(dane); st.rerun()
                if status != "Gotowe":
                    if c[4].button("ZROBIONE", key=f"zg{i}"): dane["w_realizacji"][i]['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
                else:
                    if c[4].button("WYŚLIJ", key=f"zw{i}"): z["zamknal"] = st.session_state.user; dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
                if c[5].button("X", key=f"zx{i}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
    with tp2:
        if dane["zrealizowane"]: st.dataframe(dane["zrealizowane"][::-1], use_container_width=True)

with t_log:
    for i, p in enumerate(dane["przyjecia"]):
        c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
        c[0].write(f"**{p.get('dostawca')}**"); c[1].write(f"{p.get('termin', '-')}"); c[2].write(f"{p.get('data_p')}")
        with c[3].popover("Szczegóły"):
            nt = st.text_input("Data:", value=p.get('termin', ''), key=f"lt_{i}"); no = st.text_area("Towar:", value=p.get('towar',''), key=f"lo_{i}")
            if st.button("Zapisz", key=f"ls_{i}"): dane["przyjecia"][i].update({"termin":nt,"towar":no}); zapisz_dane(dane); st.rerun()
        if c[4].button("OK", key=f"lg{i}"): dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"lx{i}"): dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()

with t_dysp:
    for i, d in enumerate(dane["dyspozycje"]):
        c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
        c[0].write(f"**{d.get('tytul')}**"); c[1].write(f"{d.get('termin', '-')}"); c[2].write(f"{d.get('data_p')}")
        with c[3].popover("Edytuj"):
            nt = st.text_input("Termin:", value=d.get('termin', ''), key=f"dt_{i}"); no = st.text_area("Opis:", value=d.get('opis',''), key=f"do_{i}")
            if st.button("Zapisz", key=f"ds_{i}"): dane["dyspozycje"][i].update({"termin":nt,"opis":no}); zapisz_dane(dane); st.rerun()
        if c[4].button("GOTOWE", key=f"dg{i}"): dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
        if c[5].button("X", key=f"dx{i}"): dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()
