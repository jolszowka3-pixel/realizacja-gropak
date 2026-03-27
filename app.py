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
    .section-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-weight: bold;
        color: #1f77b4;
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
                if "przyjecia_historia" not in d: d["przyjecia_historia"] = []
                return d
        except: pass
    return {"w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": []}

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
        if st.button("Zatwierdź Przyjęcie"):
            if p_dostawca and p_towar:
                dane["przyjecia"].append({
                    "dostawca": p_dostawca, 
                    "towar": p_towar, 
                    "data_p": datetime.now().strftime("%d.%m %H:%M"),
                    "data_k": "-"
                })
                zapisz_dane(dane)
                st.rerun()

# --- 5. WIDOK GŁÓWNY ---
st.header("📊 System GROPAK Online")
st.write("---")

# --- SEKCJA A: PRODUKCJA I WYDANIA ---
st.markdown('<div class="section-header">📦 ZAMÓWIENIA I REALIZACJA PRODUKCJI</div>', unsafe_allow_html=True)
tab_prod, tab_hist_prod = st.tabs(["🚀 Bieżąca Produkcja", "✅ Historia Wydań"])

with tab_prod:
    if not dane["w_realizacji"]:
        st.info("Brak aktywnych zleceń produkcyjnych.")
    else:
        c_h = st.columns([2, 1.5, 5.5, 1, 1])
        c_h[0].write("**Klient**"); c_h[1].write("**Data**"); c_h[2].write("**Produkty**"); c_h[3].write("**Status**"); c_h[4].write("")
        st.divider()
        for i, z in enumerate(dane["w_realizacji"]):
            c = st.columns([2, 1.5, 5.5, 1, 1])
            c[0].write(z['klient'])
            c[1].write(z['data_p'])
            
            p_prev = (z['opis'][:65] + '...') if len(z['opis']) > 65 else z['opis']
            with c[2].popover(f"📋 {p_prev if p_prev else 'Edytuj'}"):
                nowe_p = st.text_area("Edycja", value=z['opis'], key=f"p_edit_{i}")
                if st.button("Zapisz", key=f"p_save_{i}"):
                    dane["w_realizacji"][i]['opis'] = nowe_p
                    zapisz_dane(dane); st.rerun()
            
            if c[3].button("GOTOWE", key=f"p_done_{i}"):
                z["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["zrealizowane"].append(dane["w_realizacji"].pop(i))
                zapisz_dane(dane); st.rerun()
            
            if c[4].button("❌", key=f"p_del_{i}"):
                dane["w_realizacji"].pop(i)
                zapisz_dane(dane); st.rerun()

with tab_hist_prod:
    if not dane["zrealizowane"]:
        st.write("Brak historii wydań.")
    else:
        df_z = pd.DataFrame(dane["zrealizowane"])
        df_v = df_z[["klient", "data_p", "data_k", "opis"]].copy()
        df_v.columns = ["Klient", "Przyjęto", "Wydano", "Produkty"]
        st.dataframe(df_v.iloc[::-1], use_container_width=True)

st.write("")

# --- SEKCJA B: LOGISTYKA I PRZYJĘCIA ---
st.markdown('<div class="section-header">📥 LOGISTYKA I PRZYJĘCIA TOWARU</div>', unsafe_allow_html=True)
tab_pz_plan, tab_pz_hist = st.tabs(["🚚 Zaplanowane Dostawy", "✅ Historia Przyjęć"])

with tab_pz_plan:
    if not dane["przyjecia"]:
        st.info("Brak zaplanowanych przyjęć.")
    else:
        c_h2 = st.columns([2, 1.5, 5.5, 1, 1])
        c_h2[0].write("**Dostawca**"); c_h2[1].write("**Data**"); c_h2[2].write("**Towar**"); c_h2[3].write("**Status**"); c_h2[4].write("")
        st.divider()
        for i, p in enumerate(dane["przyjecia"]):
            c = st.columns([2, 1.5, 5.5, 1, 1])
            c[0].write(p['dostawca'])
            c[1].write(p['data_p'])
            
            t_prev = (p['towar'][:65] + '...') if len(p['towar']) > 65 else p['towar']
            with c[2].popover(f"🚚 {t_prev if t_prev else 'Edytuj'}"):
                nowe_t = st.text_area("Edycja PZ", value=p['towar'], key=f"pz_edit_{i}")
                if st.button("Zapisz", key=f"pz_s_{i}"):
                    dane["przyjecia"][i]['towar'] = nowe_t
                    zapisz_dane(dane); st.rerun()
            
            if c[3].button("✅", key=f"pz_ok_{i}"):
                p["data_k"] = datetime.now().strftime("%d.%m %H:%M")
                dane["przyjecia_historia"].append(dane["przyjecia"].pop(i))
                zapisz_dane(dane); st.rerun()
                
            if c[4].button("❌", key=f"pz_del_{i}"):
                dane["przyjecia"].pop(i)
                zapisz_dane(dane); st.rerun()

with tab_pz_hist:
    if not dane["przyjecia_historia"]:
        st.write("Brak historii przyjęć.")
    else:
        df_pz_h = pd.DataFrame(dane["przyjecia_historia"])
        # Wybieramy i nazywamy kolumny tak, by pasowały do danych
        df_pz_v = df_pz_h[["dostawca", "data_p", "data_k", "towar"]].copy()
        df_pz_v.columns = ["Dostawca", "Zaplanowano", "Odebrano", "Towar / Uwagi"]
        st.dataframe(df_pz_v.iloc[::-1], use_container_width=True)
