import streamlit as st
import pandas as pd
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import os
import pickle
import io

# Ámbito para la API de Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Autenticación con Google Drive
def authenticate_google_drive():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        # Cargar las credenciales desde los secretos de Streamlit
        client_secret = {
            "installed": {
                "client_id": st.secrets["client_secret"]["client_id"],
                "client_secret": st.secrets["client_secret"]["client_secret"],
                "auth_uri": st.secrets["client_secret"]["auth_uri"],
                "token_uri": st.secrets["client_secret"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["client_secret"]["auth_provider_x509_cert_url"],
                "redirect_uris": [st.secrets["client_secret"]["redirect_uris"]]
            }
        }

        # Guardar temporalmente el archivo client_secret.json
        with open("client_secret.json", "w") as f:
            json.dump(client_secret, f)

        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json', SCOPES)
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

# Verificar si el archivo ya existe en Google Drive
def file_exists_in_drive(file_name):
    service = authenticate_google_drive()
    results = service.files().list(q=f"name='{file_name}'", spaces='drive', fields="files(id, name)").execute()
    files = results.get('files', [])
    if not files:
        return False, None
    return True, files[0]['id']

# Descargar archivo existente de Google Drive
def download_file_from_drive(file_id, file_name):
    service = authenticate_google_drive()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.close()

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
    # Crear un dataframe con los datos ingresados
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
    df_new = pd.DataFrame(data)
    
    # Verificar si el archivo ya existe en Google Drive
    file_name = 'falla_cardiaca_datos.csv'
    file_exists, file_id = file_exists_in_drive(file_name)
    
    if file_exists:
        # Descargar el archivo existente y cargarlo en un DataFrame
        download_file_from_drive(file_id, file_name)
        df_existing = pd.read_csv(file_name)
        # Combinar los datos existentes con los nuevos datos
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        # Si no existe, usar solo los nuevos datos
        df_combined = df_new

    # Guardar el DataFrame combinado en un archivo CSV
    df_combined.to_csv(file_name, index=False)
    
    # Subir el archivo CSV actualizado a Google Drive
    upload_to_drive(file_name)

