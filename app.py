import streamlit as st
from google.oauth2 import service_account

# Pobranie danych ze Streamlit Secrets
creds_dict = st.secrets["gcp_service_account"]

# Stworzenie obiektu credentials
credentials = service_account.Credentials.from_service_account_info(creds_dict)

# Przykład: Użycie credentials do połączenia np. z BigQuery lub Google Sheets
# client = bigquery.Client(credentials=credentials, project=creds_dict["project_id"])

st.write("Połączono pomyślnie z projektem:", creds_dict["project_id"])
