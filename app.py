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
    .stButton>button, .stFormSubmitButton>button { 
        width: 100%; border-radius: 6px; min-height: 32px !important; height: 32px !important; 
        font-size: 12px; font-weight: 600; transition: all 0.2s ease-in-out;
        border: 1px solid #ced4da; padding: 0 10px; line-height: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* ZIELONE / CZERWONE / NIEBIESKIE PRZYCISKI */
    button:has(div p:contains("GOTOWE")), button:has(div p:contains("OK")), button:contains("GOTOWE"), button:contains("OK") {
        border: none !important; color: white !important; background-color: #28a745 !important;
    }
    button:has(div p:contains("GOTOWE")):hover, button:has(div p:contains("OK")):hover {
        background-color: #218838 !important; box-shadow: 0 2px 5px rgba(40, 167, 69, 0.4); transform: translateY(-1px);
    }
    
    button:has(div p:contains("X")), button:contains("X") {
        border: none !important; color: white !important; background-color: #dc3545 !important; padding: 0 !important;
    }
    button:has(div p:contains("X")):hover, button:contains("X"):hover {
        background-color: #c82333 !important; box-shadow: 0 2px 5px rgba(220, 53, 69, 0.4); transform: translateY(-1px);
    }
    
    button:has(div p:contains("Zapisz")), button:contains("Zapisz") {
        border: none !important; color: white !important; background-color: #007bff !important;
    }
    button:has(div p:contains("Zapisz")):hover, button:contains("Zapisz"):hover {
        background-color: #0056b3 !important; box-shadow: 0 2px 5px rgba(0, 123, 255, 0.4); transform: translateY(-1px);
    }
    
    div[data-testid="stHorizontalBlock"] { align-items: center !important; padding: 4px 0; }
    .stTextInput input { min-height: 32px !important; height: 32px !important; font-size: 12px !important; border-radius: 6px !important; }
    div[data-testid="stPopover"] > button { min-height: 32px !important; height: 32px !important; border: 1px solid #ced4da !important; background: white !important; text-align: left !important; color: #495057 !important; }

    .main .block-container { padding-top: 2rem; }
    .section-header {
        background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px;
        font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    .sidebar-header {
        background: linear-gradient(90deg, #1e7e34, #28a745);
        color: white; padding: 12px; border-radius: 6px; text-align: center;
        font-weight: 700; font-size: 14px; margin-bottom: 15px; letter-spacing: 1px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; align-items: stretch; margin-top: 15px; margin-bottom: 25px; }
    .day-col { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; flex-direction: column; min-height: 120px; }
    .day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 12px; padding-bottom: 6px; }
    .day-name { font-weight: 700; font-size: 13px; color: #495057; }
    .day-date { font-size: 11px; color: #868e96; }
    
    .cal-entry-out { cursor: help; font-size: 10.5px; background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; padding: 5px 6px; margin-bottom: 5px; border-radius: 4px; font-weight: 600; line-height: 1.2;}
    .cal-entry-in { cursor: help; font-size: 10.5px; background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; padding: 5px 6px; margin-bottom: 5px; border-radius: 4px; font-weight: 600; line-height: 1.2;}
    .cal-entry-task { cursor: help; font-size: 10.5px; background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; padding: 5px 6px; margin-bottom: 5px; border-radius: 4px; font-weight: 600; line-height: 1.2;}
    
    .badge-urgent { background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 5px; }
    .car-badge { background-color: #343a40; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9.5px; margin-right: 5px; }
    .label-text { font-size: 11px; color: #6c757d; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    button[data-baseweb="tab"] { font-size: 16px !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA BAZY DANYCH I SORTOWANIE ---
PLIK_DANYCH = "baza_gropak_v3.json"

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        try:
            parts = str(item.get('termin', '')).strip().split('.')
            if len(parts) >= 2:
                d, m = int(parts[0]), int(parts[1])
                y = int(parts[2]) if len(parts) > 2 else datetime.now().year
                return (0, y, m, d, pilne)
            return (1, 9999, 99, 99, pilne) 
        except:
            return (1, 9999, 99, 99, pilne)

    if "w_realizacji" in dane: dane["w_realizacji"].sort(key=sort_key)
    if "przyjecia" in dane: dane["przyjecia"].sort(key=sort_key)
    if "dyspozycje" in dane: dane["dyspozycje"].sort(key=sort_key)
    return dane

def wczytaj_dane():
    default_dane = {
        "w_realizacji": [], "zrealizowane": [], 
        "przyjecia": [], "przyjecia_historia": [],
        "dyspozycje": [], "dyspozycje_historia": [],
        "uzytkownicy": {"admin": "gropak2026"}
    }
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
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- 3. SYSTEM LOGOWANIA ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.subheader("GROPAK ERP - Logowanie")
    c1, _ = st.columns([1, 2])
    with c1:
        with st.form("login_form"):
            u = st.text_input("Użytkownik")
            p = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj"):
                if u in dane["uzytkownicy"] and dane["uzytkownicy"][u] == p:
                    st.session_state.user = u
                    st.rerun()
                else: 
                    st.error("Błąd logowania")
    st.stop()

# --- 4. PANEL BOCZNY (TRANSPORT) ---
with st.sidebar:
    st.write(f"Zalogowany: **{st.session_state.user}**")
    if st.button("🚪 Wyloguj"): st.session_state.user = None; st.rerun()
    st.divider()

    if st.session_state.user == "admin":
        with st.expander("🛠️ Zarządzanie kontami"):
            with st.form("dodaj_konta"):
                nu = st.text_input("Nowy login")
                nh = st.text_input("Nowe hasło")
                if st.form_submit_button("Dodaj pracownika") and nu: 
                    dane["uzytkownicy"][nu] = nh; zapisz_dane(dane); st.rerun()
            st.write("Lista kont:")
            for usr in list(dane["uzytkownicy"].keys()):
                if usr != "admin":
                    if st.button(f"Usuń {usr}", key=f"del_{usr}"):
                        del dane["uzytkownicy"][usr]; zapisz_dane(dane); st.rerun()
    st.divider()
    
    st.markdown('<div class="sidebar-header">➕ DODAJ NOWY WPIS</div>', unsafe_allow_html=True)
    typ = st.selectbox("Wybierz rodzaj operacji:", ["🏭 Zlecenie Produkcji", "🚚 Dostawa (PZ)", "📋 Dyspozycja Dodatkowa"], label_visibility="collapsed")
    
    if typ == "🏭 Zlecenie Produkcji":
        with st.form("form_prod", clear_on_submit=True):
            kl = st.text_input("👤 Klient (Nazwa / Firma)")
            tm = st.text_input("📅 Termin (np. 31.03)")
            op = st.text_area("📝 Specyfikacja ogólna")
            sz = st.text_area("📦 Szczegółowe zamówienie (ilości itp.)")
            
            st.markdown("**🚛 Logistyka Wyjazdowa:**")
            col_a, col_k = st.columns(2)
            auto = col_a.selectbox("Wybierz auto:", ["Brak", "Auto 1", "Auto 2"])
            kurs = col_k.selectbox("Numer kursu:", [1, 2, 3, 4, 5])
            
            p = st.checkbox("🔥 Oznacz jako PILNE")
            if st.form_submit_button("💾 Zapisz Zlecenie"):
                if kl: 
                    dane["w_realizacji"].append({
                        "klient": kl, "termin": tm, "opis": op, "szczegoly": sz, 
                        "auto": auto, "kurs": kurs, "pilne": p, 
                        "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user
                    })
                    zapisz_dane(dane); st.rerun()
                    
    elif typ == "🚚 Dostawa (PZ)":
        with st.form("form_log", clear_on_submit=True):
            ds = st.text_input("🏢 Dostawca")
            tm = st.text_input("📅 Data dostawy (np. 31.03)")
            op = st.text_area("📦 Co przyjeżdża? (Zawartość)")
            p = st.checkbox("🔥 Oznacz jako PILNE")
            if st.form_submit_button("💾 Zapisz Dostawę"):
                if ds: 
                    dane["przyjecia"].append({"dostawca": ds, "termin": tm, "towar": op, "pilne": p, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                    zapisz_dane(dane); st.rerun()
                    
    else:
        with st.form("form_dysp", clear_on_submit=True):
            tyt = st.text_input("🎯 Tytuł zadania")
            tm = st.text_input("📅 Na kiedy? (np. 31.03)")
            op = st.text_area("📝 Opis / Instrukcje")
            p = st.checkbox("🔥 Oznacz jako PILNE")
            if st.form_submit_button("💾 Zapisz Zadanie"):
                if tyt: 
                    dane["dyspozycje"].append({"tytul": tyt, "termin": tm, "opis": op, "pilne": p, "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                    zapisz_dane(dane); st.rerun()

# --- 5. STATYSTYKI ---
st.markdown('<div class="section-header">Podsumowanie</div>', unsafe_allow_html=True)
c_s1, c_s2, c_s3 = st.columns(3)
c_s1.metric("📦 Aktywne Zlecenia", len(dane["w_realizacji"]))
c_s2.metric("🚚 Oczekujące Dostawy", len(dane["przyjecia"]))
c_s3.metric("📋 Dyspozycje w toku", len(dane["dyspozycje"]))

# --- 6. TERMINARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "week_offset" not in st.session_state: st.session_state.week_offset = 0

c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1: 
    if st.button("← Poprzedni tydzień"): st.session_state.week_offset -= 7; st.rerun()
with c_nav3: 
    if st.button("Następny tydzień →"): st.session_state.week_offset += 7; st.rerun()

today = datetime.now()
start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=st.session_state.week_offset)
dates_in_week = [(start_of_week + timedelta(days=i)) for i in range(7)]

with c_nav2:
    st.markdown(f"<h5 style='text-align: center; margin: 0;'>{dates_in_week[0].strftime('%d.%m')} - {dates_in_week[6].strftime('%d.%m.%Y')}</h5>", unsafe_allow_html=True)

def parse_d(txt):
    try:
        parts = str(txt).split(".")
        return int(parts[0]), int(parts[1])
    except: return None, None

day_names = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]

html_calendar = '<div class="week-grid">'
for i, date in enumerate(dates_in_week):
    html_calendar += f'<div class="day-col">'
    html_calendar += f'<div class="day-header"><div class="day-name">{day_names[i]}</div><div class="day-date">{date.strftime("%d.%m")}</div></div>'
    
    d_val, m_val = date.day, date.month
    
    # PRODUKCJA - Zabezpieczone Tooltipy i Auta
    for z in dane["w_realizacji"]:
        zd, zm = parse_d(z.get('termin', ''))
        if zd == d_val and zm == m_val:
            p_mark = "🔥 " if z.get('pilne') else ""
            
            # Bezpieczne pobieranie auta (obsługa starych wpisów)
            auto_val = str(z.get('auto', 'Brak'))
            if auto_val in ["Auto 1", "Auto 2"]:
                a_mark = f'<span class="car-badge">🚗 {auto_val[-1]}/{z.get("kurs", 1)}</span>'
            else:
                a_mark = ""
                
            opis_safe = str(z.get('opis', '')).replace('"', '&quot;')
            szczegoly_safe = str(z.get('szczegoly', '')).replace('"', '&quot;')
            
            tooltip = f"Specyfikacja: {opis_safe}&#10;"
            if szczegoly_safe: tooltip += f"Szczegóły zam.: {szczegoly_safe}&#10;"
            tooltip += f"Dodano: {z.get('data_p', '-')} ({z.get('autor', '-')})"
            
            html_calendar += f'<div class="cal-entry-out" title="{tooltip}">{a_mark}{p_mark}W: {z.get("klient", "-")}</div>'
    
    # LOGISTYKA
    for p in dane["przyjecia"]:
        pd, pm = parse_d(p.get('termin', ''))
        if pd == d_val and pm == m_val:
            p_mark = "🔥 " if p.get('pilne') else ""
            towar_safe = str(p.get('towar', 'Brak szczegółów')).replace('"', '&quot;')
            tooltip = f"Towar: {towar_safe}&#10;Dodano: {p.get('data_p', '-')} ({p.get('autor', '-')})"
            html_calendar += f'<div class="cal-entry-in" title="{tooltip}">{p_mark}P: {p.get("dostawca", "-")}</div>'
    
    # DYSPOZYCJE
    for ds in dane["dyspozycje"]:
        dd, dm = parse_d(ds.get('termin', ''))
        if dd == d_val and dm == m_val:
            p_mark = "🔥 " if ds.get('pilne') else ""
            opis_safe = str(ds.get('opis', 'Brak opisu')).replace('"', '&quot;')
            tooltip = f"Zadanie: {opis_safe}&#10;Dodano: {ds.get('data_p', '-')} ({ds.get('autor', '-')})"
            html_calendar += f'<div class="cal-entry-task" title="{tooltip}">{p_mark}D: {ds.get("tytul", "-")}</div>'
            
    html_calendar += '</div>' 
html_calendar += '</div>' 

st.markdown(html_calendar, unsafe_allow_html=True)

# --- 7. TABELE REALIZACJI ---
st.markdown('<div class="section-header">Tabele Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Wyszukaj (klient, dostawca, wymiar, opis...)", "").lower()

tab_prod, tab_log, tab_dysp = st.tabs(["🏭 Zlecenia Produkcyjne", "🚚 Przyjęcia Towaru (PZ)", "📋 Dyspozycje Dodatkowe"])

# 7.1 PRODUKCJA
with tab_prod:
    tp1, tp2 = st.tabs(["Aktywne Zlecenia", "Zrealizowane / Historia"])
    with tp1:
        if not dane["w_realizacji"]: st.info("Brak aktywnych zleceń.")
        else:
            st.markdown('<div style="display: flex; padding-left: 5px;"><div class="label-text" style="width: 16%;">Klient / Auto</div><div class="label-text" style="width: 13%;">Termin</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Więcej informacji / Edycja</div></div>', unsafe_allow_html=True)
            for i, z in enumerate(dane["w_realizacji"]):
                klient = str(z.get('klient', 'Brak'))
                opis = str(z.get('opis', ''))
                szczegoly = str(z.get('szczegoly', ''))
                
                if search and search not in klient.lower() and search not in opis.lower() and search not in szczegoly.lower(): continue
                
                c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
                
                # Etykieta pilne i auto
                b_pilne = '<span class="badge-urgent">PILNE</span>' if z.get('pilne') else ''
                auto_val = str(z.get('auto', 'Brak'))
                b_auto = f'<span class="car-badge">🚗 {auto_val[-1]}/{z.get("kurs", 1)}</span>' if auto_val in ["Auto 1", "Auto 2"] else ''
                
                c[0].markdown(f"**{klient}**<br>{b_auto} {b_pilne}", unsafe_allow_html=True)
                
                nt = c[1].text_input("T", value=z.get('termin', ''), key=f"zt{i}", label_visibility="collapsed")
                if nt != z.get('termin', ''): dane["w_realizacji"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
                
                c[2].write(f"{z.get('data_p', '-')} ({z.get('autor', 'brak')})")
                
                with c[3].popover("Pokaż / Edytuj szczegóły"):
                    st.markdown("**🚛 Edycja Transportu:**")
                    c_a, c_k = st.columns(2)
                    na = c_a.selectbox("Auto:", ["Brak", "Auto 1", "Auto 2"], index=["Brak", "Auto 1", "Auto 2"].index(auto_val) if auto_val in ["Brak", "Auto 1", "Auto 2"] else 0, key=f"na{i}")
                    
                    # Bezpieczny kurs
                    k_val = z.get('kurs', 1)
                    try: k_val = int(k_val)
                    except: k_val = 1
                    if k_val not in [1, 2, 3, 4, 5]: k_val = 1
                    
                    nk = c_k.selectbox("Kurs:", [1, 2, 3, 4, 5], index=k_val-1, key=f"nk{i}")
                    
                    st.markdown("**📝 Edycja Opisów:**")
                    no = st.text_area("Specyfikacja ogólna", value=opis, key=f"zo{i}")
                    nsz = st.text_area("Szczegóły zamówienia (ilości, itp.)", value=szczegoly, key=f"zsz{i}")
                    
                    if st.button("Zapisz wszystkie zmiany", key=f"zs{i}"): 
                        dane["w_realizacji"][i]['auto'] = na
                        dane["w_realizacji"][i]['kurs'] = nk
                        dane["w_realizacji"][i]['opis'] = no
                        dane["w_realizacji"][i]['szczegoly'] = nsz
                        zapisz_dane(dane)
                        st.rerun()
                
                if c[4].button("GOTOWE", key=f"zg{i}"):
                    z["data_k"] = datetime.now().strftime("%d.%m %H:%M"); z["zamknal"] = st.session_state.user
                    dane["zrealizowane"].append(dane["w_realizacji"].pop(i)); zapisz_dane(dane); st.rerun()
                if c[5].button("X", key=f"zx{i}"): 
                    dane["w_realizacji"].pop(i); zapisz_dane(dane); st.rerun()

    with tp2: 
        if dane["zrealizowane"]: st.dataframe(pd.DataFrame(dane["zrealizowane"]).iloc[::-1], use_container_width=True)
        else: st.info("Brak historii.")

# 7.2 LOGISTYKA
with tab_log:
    tl1, tl2 = st.tabs(["Zaplanowane", "Historia"])
    with tl1:
        if not dane["przyjecia"]: st.info("Brak dostaw.")
        else:
            st.markdown('<div style="display: flex; padding-left: 5px;"><div class="label-text" style="width: 16%;">Dostawca</div><div class="label-text" style="width: 13%;">Termin</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Szczegóły</div></div>', unsafe_allow_html=True)
            for i, p in enumerate(dane["przyjecia"]):
                dostawca = str(p.get('dostawca', 'Brak'))
                towar = str(p.get('towar', ''))
                if search and search not in dostawca.lower() and search not in towar.lower(): continue
                
                c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
                b = '<span class="badge-urgent">PILNE</span>' if p.get('pilne') else ''
                c[0].markdown(f"**{dostawca}** {b}", unsafe_allow_html=True)
                
                nt = c[1].text_input("T", value=p.get('termin', ''), key=f"lt{i}", label_visibility="collapsed")
                if nt != p.get('termin', ''): dane["przyjecia"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
                
                c[2].write(f"{p.get('data_p', '-')} ({p.get('autor', 'brak')})")
                
                with c[3].popover("Co w dostawie?"):
                    no = st.text_area("Edytuj", value=towar, key=f"lo{i}")
                    if st.button("Zapisz", key=f"ls{i}"): dane["przyjecia"][i]['towar'] = no; zapisz_dane(dane); st.rerun()
                
                if c[4].button("OK", key=f"lg{i}"):
                    p["data_k"] = datetime.now().strftime("%d.%m %H:%M"); p["odebral"] = st.session_state.user
                    dane["przyjecia_historia"].append(dane["przyjecia"].pop(i)); zapisz_dane(dane); st.rerun()
                if c[5].button("X", key=f"lx{i}"): 
                    dane["przyjecia"].pop(i); zapisz_dane(dane); st.rerun()

    with tl2: 
        if dane["przyjecia_historia"]: st.dataframe(pd.DataFrame(dane["przyjecia_historia"]).iloc[::-1], use_container_width=True)
        else: st.info("Brak historii.")

# 7.3 DYSPOZYCJE
with tab_dysp:
    td1, td2 = st.tabs(["W toku", "Historia"])
    with td1:
        if not dane["dyspozycje"]: st.info("Brak zadań.")
        else:
            st.markdown('<div style="display: flex; padding-left: 5px;"><div class="label-text" style="width: 16%;">Tytuł / Cel</div><div class="label-text" style="width: 13%;">Termin</div><div class="label-text" style="width: 13%;">Dodano</div><div class="label-text">Opis zadania</div></div>', unsafe_allow_html=True)
            for i, d in enumerate(dane["dyspozycje"]):
                tytul = str(d.get('tytul', 'Brak'))
                opis = str(d.get('opis', ''))
                if search and search not in tytul.lower() and search not in opis.lower(): continue
                
                c = st.columns([1.5, 1.2, 1.2, 4.5, 0.8, 0.4])
                b = '<span class="badge-urgent">PILNE</span>' if d.get('pilne') else ''
                c[0].markdown(f"**{tytul}** {b}", unsafe_allow_html=True)
                
                nt = c[1].text_input("T", value=d.get('termin', ''), key=f"dt{i}", label_visibility="collapsed")
                if nt != d.get('termin', ''): dane["dyspozycje"][i]['termin'] = nt; zapisz_dane(dane); st.rerun()
                
                c[2].write(f"{d.get('data_p', '-')} ({d.get('autor', 'brak')})")
                
                with c[3].popover("Szczegóły"):
                    no = st.text_area("Edytuj", value=opis, key=f"do{i}")
                    if st.button("Zapisz", key=f"ds{i}"): dane["dyspozycje"][i]['opis'] = no; zapisz_dane(dane); st.rerun()
                
                if c[4].button("GOTOWE", key=f"dg{i}"):
                    d["data_k"] = datetime.now().strftime("%d.%m %H:%M"); d["zamknal"] = st.session_state.user
                    dane["dyspozycje_historia"].append(dane["dyspozycje"].pop(i)); zapisz_dane(dane); st.rerun()
                if c[5].button("X", key=f"dx{i}"): 
                    dane["dyspozycje"].pop(i); zapisz_dane(dane); st.rerun()

    with td2: 
        if dane["dyspozycje_historia"]: st.dataframe(pd.DataFrame(dane["dyspozycje_historia"]).iloc[::-1], use_container_width=True)
        else: st.info("Brak historii.")
