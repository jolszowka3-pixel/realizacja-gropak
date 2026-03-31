import streamlit as st
import json
import os
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

.stDownloadButton>button { border: 2px solid #212529 !important; background-color: #f8f9fa !important; color: #212529 !important; }

/* TWARDE WYRÓWNANIE DO ŚRODKA */
div[data-testid="stHorizontalBlock"] { align-items: center !important; }
div[data-testid="stHorizontalBlock"] p { margin-bottom: 0 !important; }

.section-header { background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px; font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; }
.sidebar-header { background: linear-gradient(90deg, #1e7e34, #28a745); color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: 700; }

.week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; margin-top: 15px; }
.day-col { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; min-height: 150px; }
.day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 12px; padding-bottom: 6px; }

.cal-entry-out { font-size: 10px; background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }
.cal-entry-ready { font-size: 10px; background: #d4edda; color: #155724; border-left: 3px solid #28a745; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }
.cal-entry-in { font-size: 10px; background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }
.cal-entry-task { font-size: 10px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 4px 6px; margin-bottom: 3px; border-radius: 3px; font-weight: 600; }

.table-group-header { background-color: #e9ecef; padding: 6px 12px; font-weight: 700; font-size: 12px; border-radius: 4px; margin: 15px 0 8px 0; border-left: 4px solid #007bff; }
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

# --- FUNKCJA GENERUJĄCA HTML DO DRUKU ---
def generuj_html_do_druku(z):
    pilne_html = '<div style="color: #dc3545; border: 5px solid #dc3545; font-size: 28px; font-weight: 900; text-align: center; padding: 15px; margin-bottom: 30px;">🔥 ZLECENIE PILNE 🔥</div>' if z.get('pilne') else ''
    auto_val = z.get('auto', 'Brak')
    k_val = z.get('kurs', 1)
    transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    
    return f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:Arial;padding:20px;}} .card{{border:4px solid #000;padding:40px;max-width:800px;margin:auto;}} h1{{text-align:center;text-transform:uppercase;border-bottom:4px solid #000;padding-bottom:10px;}} .row{{display:flex;margin-bottom:20px;}} .col{{flex:1;}} .label{{font-size:12px;color:grey;text-transform:uppercase;}} .val{{font-size:22px;font-weight:bold;}} .box{{border:1px solid #ccc;padding:15px;min-height:100px;white-space:pre-wrap;font-size:18px;}}</style></head>
    <body onload="window.print()"><div class="card">{pilne_html}<h1>Karta Zlecenia</h1><div class="row"><div class="col"><div class="label">Klient</div><div class="val">{z.get('klient','-')}</div></div><div class="col"><div class="label">Termin</div><div class="val">{z.get('termin','-')}</div></div></div><div class="row"><div class="col"><div class="label">Transport</div><div class="val">{transport_str}</div></div><div class="col"><div class="label">Dodano</div><div class="val">{z.get('data_p','-')}</div></div></div><div class="label">Specyfikacja</div><div class="box">{z.get('opis','-')}</div><br><div class="label">Szczegóły</div><div class="box">{z.get('szczegoly','-')}</div><div style="margin-top:80px;text-align:right;">Podpis: _________________</div></div></body></html>"""

# Zmienne sesyjne
if "print_order" not in st.session_state: st.session_state.print_order = None

# --- WIDOK DRUKOWANIA ---
if st.session_state.print_order is not None:
    z = st.session_state.print_order
    st.markdown('<style>[data-testid="stSidebar"] {display: none;} header {display: none;}</style>', unsafe_allow_html=True)
    if st.button("⬅️ Wróć do systemu"): st.session_state.print_order = None; st.rerun()
    st.info("🖨️ Naciśnij Ctrl + P, aby wydrukować.")
    st.markdown(f"<div style='border:3px solid black;padding:20px;'><h2>Zlecenie: {z.get('klient')}</h2><p>{z.get('opis')}</p></div>", unsafe_allow_html=True)
    st.stop()

# --- 3. LOGOWANIE ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.markdown('<style>[data-testid="stSidebar"] {display: none;}</style>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        try: st.image("logo.png", use_container_width=True)
        except: st.title("GROPAK ERP")
        with st.form("login"):
            u = st.text_input("Login"); p = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj się"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p: st.session_state.user = u; st.rerun()
                else: st.error("Błąd logowania")
    st.stop()

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()
    
    st.markdown('<div class="sidebar-header">➕ DODAJ NOWY WPIS</div>', unsafe_allow_html=True)
    typ = st.selectbox("Rodzaj:", ["Produkcja", "Dostawa (PZ)", "Dyspozycja"])
    with st.form("add_form", clear_on_submit=True):
        if typ == "Produkcja":
            kl = st.text_input("👤 Klient"); tm = st.text_input("📅 Termin"); op = st.text_area("📝 Specyfikacja"); sz = st.text_area("📦 Ilości"); auto = st.selectbox("Transport:", OPCJE_TRANSPORTU); kr = st.selectbox("Kurs:", [1,2,3,4,5]); p = st.checkbox("🔥 PILNE")
            if st.form_submit_button("💾 Zapisz"):
                dane["w_realizacji"].append({"klient":kl,"termin":tm,"opis":op,"szczegoly":sz,"auto":auto,"kurs":kr,"pilne":p,"status":"W produkcji","data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                zapisz_dane(dane); st.rerun()
        elif typ == "Dostawa (PZ)":
            ds = st.text_input("🏢 Dostawca"); tm = st.text_input("📅 Data"); op = st.text_area("📦 Co przyjeżdża?")
            if st.form_submit_button("💾 Zapisz"):
                dane["przyjecia"].append({"dostawca":ds,"termin":tm,"towar":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                zapisz_dane(dane); st.rerun()
        else:
            tyt = st.text_input("🎯 Tytuł"); tm = st.text_input("📅 Termin"); op = st.text_area("📝 Opis")
            if st.form_submit_button("💾 Zapisz"):
                dane["dyspozycje"].append({"tytul":tyt,"termin":tm,"opis":op,"data_p":datetime.now().strftime("%d.%m %H:%M"),"autor":st.session_state.user})
                zapisz_dane(dane); st.rerun()

    # --- SEKCYJNY RESET DLA ADMINA ---
    if st.session_state.user == "admin":
        st.divider()
        with st.expander("⚙️ Ustawienia Systemu"):
            st.warning("Ta akcja jest nieodwracalna!")
            if st.button("🔥 RESETUJ WSZYSTKIE DANE"):
                dane["w_realizacji"] = []
                dane["zrealizowane"] = []
                dane["przyjecia"] = []
                dane["przyjecia_historia"] = []
                dane["dyspozycje"] = []
                dane["dyspozycje_historia"] = []
                zapisz_dane(dane)
                st.success("Baza wyczyszczona!")
                st.rerun()

# --- 5. STATYSTYKI ---
st.markdown('<div class="section-header">Podsumowanie</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.metric("📦 Zlecenia", len(dane["w_realizacji"])); c2.metric("🚚 Dostawy", len(dane["przyjecia"])); c3.metric("📋 Dyspozycje", len(dane["dyspozycje"]))

# --- 6. TERMINARZ ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "offset" not in st.session_state: st.session_state.offset = 0
n1, n2, n3 = st.columns([1,4,1])
if n1.button("← Poprzedni"): st.session_state.offset -= 7; st.rerun()
if n3.button("Następny →"): st.session_state.offset += 7; st.rerun()
start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.offset)
days = [(start + timedelta(days=i)) for i in range(7)]
grid = st.columns(7)
for i, d in enumerate(days):
    with grid[i]:
        st.markdown(f"<div style='text-align:center;border-bottom:2px solid black;'><b>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</b><br>{d.strftime('%d.%m')}</div>", unsafe_allow_html=True)
        for z in dane["w_realizacji"]:
            try:
                zd, zm = z['termin'].split('.')[:2]
                if int(zd) == d.day and int(zm) == d.month:
                    st.markdown(f"<div class='{'cal-entry-ready' if z.get('status')=='Gotowe' else 'cal-entry-out'}'>{'✅' if z.get('status')=='Gotowe' else ''}{z['klient']}</div>", unsafe_allow_html=True)
            except: pass

# --- 7. TABELE ---
st.markdown('<div class="section-header">Tabele Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Szukaj...", "").lower()
t1, t2, t3 = st.tabs(["🏭 Produkcja", "🚚 Przyjęcia", "📋 Dyspozycje"])

with t1:
    ta1, ta2 = st.tabs(["Aktywne", "Historia"])
    with ta1:
        st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5]) # Header dummy
        last = None
        for i, z in enumerate(dane["w_realizacji"]):
            if search and search not in str(z).lower(): continue
            curr = (z['termin'], z['auto'], z['kurs'])
            if curr != last:
                st.markdown(f"<div class='table-group-header'>📅 {z['termin']} | {z['auto']} (K{z['kurs']})</div>", unsafe_allow_html=True)
                last = curr
            c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
            c[0].write(f"**{z['klient']}** {'🔥' if z['pilne'] else ''}")
            c[1].write(z['termin']); c[2].write(z['data_p'])
            with c[3].popover("Opcje"):
                st.download_button("🖨️ Pobierz Kartę", generuj_html_do_druku(z), f"Zlecenie_{i}.html", "text/html")
                nt = st.text_input("Data", z['termin'], key=f"t{i}"); na = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(z['auto']), key=f"a{i}")
                no = st.text_area("Spec", z['opis'], key=f"o{i}"); nsz = st.text_area("Ilości", z['szczegoly'], key=f"s{i}")
                if st.button("Zapisz", key=f"sv{i}"): z.update({"termin":nt,"auto":na,"opis":no,"szczegoly":nsz}); zapisz_dane(dane); st.rerun()
            if z['status'] != "Gotowe":
                if c[4].button("ZROBIONE", key=f"z{i}"): z['status']="Gotowe"; zapisz_dane(dane); st.rerun()
            else:
                if c[4].button("WYŚLIJ", key=f"w{i}"): dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"x{i}"): dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()
    with ta2: st.write(dane["zrealizowane"][::-1])

with t2:
    la1, la2 = st.tabs(["Aktywne", "Historia"])
    with la1:
        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
            c[0].write(f"**{p['dostawca']}**"); c[1].write(p['termin']); c[2].write(p['data_p'])
            with c[3].popover("Edytuj"):
                nt = st.text_input("Data", p['termin'], key=f"lt{i}"); no = st.text_area("Co?", p['towar'], key=f"lo{i}")
                if st.button("Zapisz", key=f"ls{i}"): p.update({"termin":nt,"towar":no}); zapisz_dane(dane); st.rerun()
            if c[4].button("OK", key=f"lg{i}"): dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"lx{i}"): dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()
    with la2: st.write(dane["przyjecia_historia"][::-1])

with t3:
    da1, da2 = st.tabs(["W toku", "Historia"])
    with da1:
        for i, d in enumerate(dane["dyspozycje"]):
            c = st.columns([1.6, 1.0, 1.0, 3.8, 1.1, 0.5])
            c[0].write(f"**{d['tytul']}**"); c[1].write(d['termin']); c[2].write(d['data_p'])
            with c[3].popover("Edytuj"):
                nt = st.text_input("Data", d['termin'], key=f"dt{i}"); no = st.text_area("Opis", d['opis'], key=f"do{i}")
                if st.button("Zapisz", key=f"ds{i}"): d.update({"termin":nt,"opis":no}); zapisz_dane(dane); st.rerun()
            if c[4].button("GOTOWE", key=f"dg{i}"): dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
            if c[5].button("X", key=f"dx{i}"): dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()
    with da2: st.write(dane["dyspozycje_historia"][::-1])
