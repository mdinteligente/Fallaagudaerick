import streamlit as st
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import os

# Ámbito para la API de Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Autenticación con Google Drive
def authenticate_google_drive():
    """Autenticar usando OAuth 2.0 y guardar token en un archivo local."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

# Función para subir archivo a Google Drive
def upload_to_drive(file_name):
    service = authenticate_google_drive()
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_name, mimetype='text/csv')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    st.success(f"Archivo guardado en Google Drive con ID: {file.get('id')}")

# Interfaz de usuario de Streamlit
st.title("Formulario de Datos para Falla Cardíaca Aguda")

# Formulario de recolección de datos
with st.form("Datos Falla Cardíaca"):
    nombre = st.text_input("Nombre del paciente")
    edad = st.number_input("Edad", min_value=0, max_value=120, step=1)
    sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
    frecuencia_cardiaca = st.number_input("Frecuencia Cardiaca (lpm)", min_value=0)
    presion_arterial = st.text_input("Presión Arterial (mmHg)")
    saturacion_oxigeno = st.number_input("Saturación de Oxígeno (%)", min_value=0, max_value=100)
    diuresis = st.text_input("Diuresis (ml/24h)")
    fraccion_eyeccion = st.number_input("Fracción de Eyección (%)", min_value=0.0, max_value=100.0, step=0.1)
    troponina = st.number_input("Troponina (ng/L)", min_value=0.0, step=0.1)
    peptido_nat_t = st.number_input("Péptido Natriurético (BNP/NT-proBNP)", min_value=0.0)

    # Botón para enviar los datos
    submit_button = st.form_submit_button(label="Enviar datos")

# Si el usuario envía los datos
if submit_button:
    data = {
        'Nombre': [nombre],
        'Edad': [edad],
        'Sexo': [sexo],
        'Frecuencia Cardiaca': [frecuencia_cardiaca],
        'Presión Arterial': [presion_arterial],
        'Saturación de Oxígeno': [saturacion_oxigeno],
        'Diuresis': [diuresis],
        'Fracción de Eyección': [fraccion_eyeccion],
        'Troponina': [troponina],
        'Péptido Natriurético': [peptido_nat_t]
    }
    df = pd.DataFrame(data)
    
    # Guardar los datos en un archivo CSV local
    csv_file = 'falla_cardiaca_datos.csv'
    df.to_csv(csv_file, index=False)
    
    # Subir el archivo CSV a Google Drive
    upload_to_drive(csv_file)
