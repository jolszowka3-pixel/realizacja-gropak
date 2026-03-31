import streamlit as st
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURACJA I STYLIZACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide", page_icon="📦")

st.markdown("""
<style>
    /* Globalne ustawienia czcionek i tła */
    .main { background-color: #f4f7f6; }
    
    /* Wspólne ustawienia przycisków */
    .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button { 
        width: 100%; border-radius: 8px; min-height: 35px !important; 
        font-size: 13px; font-weight: 600; transition: all 0.3s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* KOLORY PRZYCISKÓW */
    button:has(div p:contains("WYŚLIJ")), button:contains("WYŚLIJ") { background-color: #28a745 !important; color: white !important; border: none !important; }
    button:has(div p:contains("ZROBIONE")), button:contains("ZROBIONE") { background-color: #ffc107 !important; color: #212529 !important; border: none !important; }
    button:has(div p:contains("Zaloguj się")), button:contains("Zaloguj się") { background-color: #1e7e34 !important; color: white !important; height: 45px !important; }
    button:has(div p:contains("X")), button:contains("X") { background-color: #e9ecef !important; color: #dc3545 !important; border: 1px solid #dee2e6 !important; }
    button:has(div p:contains("X")):hover { background-color: #dc3545 !important; color: white !important; }
    
    /* TWARDE WYRÓWNANIE ELEMENTÓW W TABELI */
    div[data-testid="stHorizontalBlock"] { align-items: center !important; background: white; padding: 5px; border-radius: 5px; margin-bottom: 2px; }
    div[data-testid="stHorizontalBlock"] p { margin-bottom: 0 !important; }

    /* NAGŁÓWKI SEKCJI */
    .section-header { 
        background: white; padding: 15px; border-radius: 10px; margin-top: 20px;
        font-weight: 800; color: #1a1a1a; text-transform: uppercase; 
        border-left: 6px solid #1e7e34; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* KALENDARZ */
    .day-col { background: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px; padding: 12px; min-height: 180px; }
    .day-header { text-align: center; border-bottom: 2px solid #1e7e34; margin-bottom: 10px; padding-bottom: 5px; }
    .cal-entry-out { cursor: help; font-size: 11px; background: #e7f5ff; color: #0056b3; border-left: 4px solid #0056b3; padding: 6px; margin-bottom: 4px; border-radius: 4px; font-weight: 600; }
    .cal-entry-ready { cursor: help; font-size: 11px; background: #e6ffed; color: #1e7e34; border-left: 4px solid #28a745; padding: 6px; margin-bottom: 4px; border-radius: 4px; font-weight: 600; }
    
    /* BADGE STATUSÓW */
    .badge-status-prod { background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 5px; font-size: 10px; font-weight: bold; border: 1px solid #ffeeba; }
    .badge-status-ready { background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 5px; font-size: 10px; font-weight: bold; border: 1px solid #c3e6cb; }
    .table-group-header { background-color: #343a40; color: white; padding: 8px 15px; font-weight: 600; font-size: 13px; border-radius: 6px; margin: 15px 0 5px 0; }
</style>
""", unsafe_allow_html=True)

# --- 2. BAZA DANYCH ---
PLIK_DANYCH = "baza_gropak_v3.json"
OPCJE_TRANSPORTU = ["Brak", "Auto 1", "Auto 2", "Transport zewnętrzny", "Odbiór osobisty", "Kurier"]

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        status_score = 1 if item.get('status') == 'Gotowe' else 0 
        try:
            parts = str(item.get('termin', '')).strip().split('.')
            if len(parts) >= 2:
                d, m = int(parts[0]), int(parts[1])
                y = int(parts[2]) if len(parts) > 2 else datetime.now().year
                return (0, y, m, d, t_score, status_score, pilne)
            return (1, 9999, 99, 99, 99, 99, pilne) 
        except: return (1, 9999, 99, 99, 99, 99, pilne)
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

# --- FUNKCJA DRUKOWANIA ---
def generuj_html_do_druku(z):
    pilne_h = '<div style="color:red; border:4px solid red; padding:10px; text-align:center; font-size:24px; font-weight:bold;">🔥 ZLECENIE PILNE 🔥</div>' if z.get('pilne') else ''
    return f"""
    <!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>
    body{{font-family:sans-serif; padding:30px;}} .card{{border:5px solid black; padding:30px;}}
    .h1{{text-align:center; font-size:30px; border-bottom:3px solid black; padding-bottom:10px;}}
    .row{{display:flex; justify-content:space-between; margin-top:20px; font-size:20px;}}
    .box{{border:1px solid #666; padding:15px; margin-top:20px; min-height:150px; font-size:18px; white-space:pre-wrap;}}
    </style></head><body onload="window.print()">
    <div class="card">{pilne_h} <h1 class="h1">KARTA ZLECENIA: {z.get('klient')}</h1>
    <div class="row"><div><b>Termin:</b> {z.get('termin')}</div><div><b>Transport:</b> {z.get('auto')} (K{z.get('kurs')})</div></div>
    <p><b>Specyfikacja ogólna:</b></p><div class="box">{z.get('opis')}</div>
    <p><b>Szczegóły (ilości/wymiary):</b></p><div class="box">{z.get('szczegoly')}</div>
    <div style="margin-top:50px; text-align:right;">Podpis wykonawcy: __________________________</div>
    </div></body></html>"""

# --- 3. AUTH & LOGOWANIE ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, login_card, _ = st.columns([1, 1.5, 1])
    with login_card:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo.png", use_container_width=True)
        except: st.title("GROPAK ERP")
        with st.form("login_form"):
            u = st.text_input("👤 Login")
            p = st.text_input("🔒 Hasło", type="password")
            if st.form_submit_button("Zaloguj się do systemu"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p:
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Nieprawidłowe dane logowania")
    st.stop()

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<p style='text-align:center;'>Zalogowany: <b>{st.session_state.user}</b></p>", unsafe_allow_html=True)
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()

    # Zarządzanie użytkownikami (Admin)
    if st.session_state.user == "admin":
        with st.expander("👥 Zarządzanie pracownikami"):
            with st.form("new_user", clear_on_submit=True):
                nu, np = st.text_input("Login"), st.text_input("Hasło")
                if st.form_submit_button("Dodaj konto"):
                    if nu: dane["uzytkownicy"][nu] = np; zapisz_dane(dane); st.rerun()
            for usr in list(dane["uzytkownicy"].keys()):
                if usr != "admin":
                    if st.button(f"Usuń: {usr}", key=f"del_{usr}"):
                        del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()
        st.divider()

    st.markdown('<div class="sidebar-header">➕ NOWY WPIS</div>', unsafe_allow_html=True)
    typ = st.selectbox("Co dodajemy?", ["Produkcja", "Dostawa (PZ)", "Zadanie"])
    with st.form("main_add", clear_on_submit=True):
        if typ == "Produkcja":
            kl = st.text_input("Klient")
            tm = st.text_input("Termin (np. 31.03)")
            op = st.text_area("Specyfikacja")
            sz = st.text_area("Szczegóły / Ilości")
            tr = st.selectbox("Transport", OPCJE_TRANSPORTU)
            kr = st.selectbox("Kurs", [1,2,3,4,5])
            pi = st.checkbox("PILNE")
            if st.form_submit_button("💾 Zapisz Zlecenie"):
                if kl:
                    dane["w_realizacji"].append({"klient":kl,"termin":tm,"opis":op,"szczegoly":sz,"auto":tr,"kurs":kr,"pilne":pi,"status":"W produkcji","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                    zapisz_dane(dane); st.rerun()
        elif typ == "Dostawa (PZ)":
            ds = st.text_input("Dostawca")
            tm = st.text_input("Kiedy?")
            tow = st.text_area("Co przyjeżdża?")
            if st.form_submit_button("💾 Zapisz Dostawę"):
                dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":tow,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                zapisz_dane(dane); st.rerun()
        else:
            tyt = st.text_input("Tytuł zadania")
            tm = st.text_input("Na kiedy?")
            opis_d = st.text_area("Opis")
            if st.form_submit_button("💾 Zapisz Zadanie"):
                dane["dyspozycje"].append({"tytul":tyt,"termin":tm,"opis":opis_d,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                zapisz_dane(dane); st.rerun()

    if st.session_state.user == "admin":
        st.divider()
        with st.expander("⚠️ Opcje Krytyczne"):
            if st.button("🔥 RESETUJ WSZYSTKIE DANE"):
                for k in ["w_realizacji","zrealizowane","przyjecia","przyjecia_historia","dyspozycje","dyspozycje_historia"]: dane[k] = []
                zapisz_dane(dane); st.rerun()

# --- 5. WIDOK GŁÓWNY ---
st.markdown('<div class="section-header">Statystyki Produkcji</div>', unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)
s1.metric("📦 Aktywne Zlecenia", len(dane["w_realizacji"]))
s2.metric("🚚 Dzisiejsze Dostawy", len(dane["przyjecia"]))
s3.metric("📋 Zadania w toku", len(dane["dyspozycje"]))

# --- 6. KALENDARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
c_n1, _, c_n3 = st.columns([1,4,1])
if c_n1.button("← Poprzedni Tydzień"): st.session_state.wo -= 7; st.rerun()
if c_n3.button("Następny Tydzień →"): st.session_state.wo += 7; st.rerun()

start_w = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)
cols = st.columns(7)
for i in range(7):
    day = start_w + timedelta(days=i)
    with cols[i]:
        st.markdown(f"<div class='day-header'><b>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</b><br>{day.strftime('%d.%m')}</div>", unsafe_allow_html=True)
        for z in dane["w_realizacji"]:
            try:
                zd, zm = map(int, z.get('termin','').split('.')[:2])
                if zd == day.day and zm == day.month:
                    is_ready = z.get('status') == 'Gotowe'
                    op_safe = str(z.get('opis','')).replace('"', '&quot;').replace('\n', ' ')
                    st.markdown(f"<div class='{'cal-entry-ready' if is_ready else 'cal-entry-out'}' title='{op_safe}'>{'✅' if is_ready else ''}{z.get('klient')}</div>", unsafe_allow_html=True)
            except: pass

# --- 7. TABELA REALIZACJI ---
st.markdown('<div class="section-header">Lista Zleceń Produkcyjnych</div>', unsafe_allow_html=True)
szukaj = st.text_input("🔍 Filtruj zlecenia (klient, towar, specyfikacja)...", "").lower()

t_prod, t_log, t_dysp = st.tabs(["🏭 PRODUKCJA", "🚚 DOSTAWY (PZ)", "🎯 ZADANIA"])

with t_prod:
    tp1, tp2 = st.tabs(["Aktywne", "Historia (Zrealizowane)"])
    with tp1:
        if not dane["w_realizacji"]: st.info("Brak aktywnych zleceń.")
        else:
            hc = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
            hc[0].write("**Klient**"); hc[1].write("**Termin**"); hc[2].write("**Dodano**"); hc[3].write("**Opcje / Klonuj**"); hc[4].write("**Status**")
            last_g
