import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="GROPAK ERP", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 2px; height: 1.9em; line-height: 1; padding: 2px; font-size: 14px; }
    .main .block-container { padding-top: 1.5rem; }
    thead tr th { background-color: #f8f9fa !important; color: #333 !important; }
    div[data-testid="stPopover"] > button { 
        border: 1px solid #dcdcdc !important; 
        background: white !important; 
        text-align: left !important; 
        color: #1f77b4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGOWANIE ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "gropak2026": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Logowanie GROPAK ERP", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if not check_password():
    st.stop()

# --- 3. BAZA DANYCH ---
PLIK_DANYCH = "baza_gropak_v3.json"

def wczytaj_dane():
    if os.path.exists(PLIK_DANYCH):
        try:
            with open(PLIK_DANYCH, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "w_realizacji" not in d: d["w_realizacji"] = []
                if "zrealizowane" not in d: d["zrealizowane"] = []
                if "przyjecia" not in d: d["przyjecia"] = []
                return d
        except: pass
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": []}

def zapisz_dane(dane):
    with open(PLIK_DANYCH, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

dane = wczytaj_dane()

# --- 4. PANEL BOCZNY ---
with st.sidebar:
    st.title("⚙️ OPERACJE")
    opcja = st.selectbox("Typ dokumentu", ["Zlecenie Produkcji", "Przyjęcie Towaru (PZ)"])
    st.divider()
    
    if opcja == "Zlecenie Produkcji":
        k_klient = st.text_input("Klient")
        k_produkty = st.text_area("Produkty")
        if st.button("Zatwierdź Zlecenie"):
            if k_klient:
                dane["w_realizacji"].append({
                    "klient": k_klient, 
                    "opis": k_produkty,
                    "data_p": datetime.now().strftime("%d.%m %H:%M"), 
                    "data_k": "-"
                })
                zapisz_dane(dane)
                st.rerun()
    else:
        p_dostawca = st.text_input("Dostawca")
        p_towar = st.text_area("Towar")
        p_ilosc = st.text_input("Ilość")
        if st.button("Zatwierdź Przyjęcie"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({
                    "dostawca": p_dostawca, 
                    "towar": p_towar, 
                    "ilosc": p_ilosc,
                    "data": datetime.now().strftime("%d.%m %H:%M")
                })
                zapisz_dane(dane)
                st.rerun()

# --- 5. WIDOK GŁÓWNY ---
st.header("📊 System GROPAK Online")

tab1, tab2, tab3 = st.tabs(["🚀 PRODUKCJA", "✅ HISTORIA WYDAŃ", "📥 PRZYJĘCIA (PZ)"])

# --- TAB 1: PRODUKCJA ---
with tab1:
    if not dane["w_realizacji"]:
        st.info("Brak aktywnych zleceń.")
    else:
        col_h = st.columns([2, 1.5, 5.5, 1, 1])
        col_h[0].write("**Klient**")
        col_h[1].write("**Data**")
        col_h[2].write("**Produkty**")
        col_h[3].write("**Status**")
        col_h[4].write("")
        st.divider()

        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([2, 1.5, 5.5, 1, 1])
            c[0].write(z['klient'])
            c[1].write(z['data_p'])
            
            prod_preview = (z['opis'][:65] + '...') if len(z['opis']) > 65 else z['opis']
            with c[2].popover(f"📦 {prod_preview if prod_preview else 'Brak opisu'}"):
                st.write("**Edytuj produkty:**")
                nowe_produkty = st.text_area("Treść", value=z['opis'], key=f"prod_{i}", label_visibility="collapsed")
                if st.button("Zapisz", key=f"save_{i}"):
                    dane["w_realizacji"][i]['opis'] = nowe_produkty
                    zapisz_dane(dane)
                    st.rerun()
            
            if c[3].button("GOTOWE", key=f"z_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                item = dane["w_realizacji"].pop(i)
                dane["zrealizowane"].append(item)
                zapisz_dane(dane)
                st.rerun()
            
            if c[4].button("❌", key=f"u_{i}"):
                dane["w_realizacji"].pop(i)
                zapisz_dane(dane)
                st.rerun()

# --- TAB 2: HISTORIA ---
with tab2:
    if not dane["zrealizowane"]:
        st.write("Brak historii.")
    else:
        df_z = pd.DataFrame(dane["zrealizowane"])
        istniejace = [col for col in ["klient", "data_p", "data_k", "opis"] if col in df_z.columns]
        df_wyswietl = df_z[istniejace].copy()
        df_wyswietl.columns = ["Klient", "Przyjęto", "Wydano", "Produkty"]
        st.dataframe(df_wyswietl.iloc[::-1], use_container_width=True)

# --- TAB 3: PRZYJĘCIA (PZ) - TERAZ JAK REALIZACJA ---
with tab3:
    if not dane["przyjecia"]:
        st.info("Brak zarejestrowanych dostaw.")
    else:
        col_pz = st.columns([2, 1.5, 4.5, 1, 1])
        col_pz[0].write("**Dostawca**")
        col_pz[1].write("**Data**")
        col_pz[2].write("**Towar**")
        col_pz[3].write("**Ilość**")
        col_pz[4].write("")
        st.divider()

        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([2, 1.5, 4.5, 1, 1])
            c[0].write(p['dostawca'])
            c[1].write(p['data'])
            
            towar_preview = (p['towar'][:50] + '...') if len(p['towar']) > 50 else p['towar']
            with c[2].popover(f"🚚 {towar_preview if towar_preview else 'Brak opisu'}"):
                st.write("**Edytuj szczegóły towaru:**")
                nowy_towar = st.text_area("Treść PZ", value=p['towar'], key=f"pz_t_{i}", label_visibility="collapsed")
                if st.button("Zapisz", key=f"pz_save_{i}"):
                    dane["przyjecia"][i]['towar'] = nowy_towar
                    zapisz_dane(dane)
                    st.rerun()
            
            c[3].write(p['ilosc'])
            
            if c[4].button("❌", key=f"pz_u_{i}"):
                dane["przyjecia"].pop(i)
                zapisz_dane(dane)
                st.rerun()

        st.divider()
        if st.button("WYCZYŚĆ CAŁY REJESTR PZ"):
            dane["przyjecia"] = []
            zapisz_dane(dane)
            st.rerun()
