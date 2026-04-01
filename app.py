import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json

st.title("GROPAK ERP - TEST POŁĄCZENIA")

# Połączenie
conn = st.connection("gsheets", type=GSheetsConnection)

# Odczyt
df = conn.read(worksheet="Sheet1", usecols=[0], ttl=0)
dane = json.loads(df.iloc[0, 0])

st.success("Połączono z bazą!")
st.write("Aktualna liczba zleceń:", len(dane["w_realizacji"]))
