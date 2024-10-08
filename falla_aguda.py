import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pandas as pd
import os

# Función para autenticar usando la cuenta de servicio
def authenticate_google_drive():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["service_account"],
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

# Función para verificar si un archivo ya existe en Google Drive
def file_exists_in_drive(file_name):
    try:
        service = authenticate_google_drive()
        query = f"name='{file_name}' and trashed=false"
        results = service.files().list(q=query, spaces='drive').execute()
        files = results.get('files', [])
        if len(files) > 0:
            return True, files[0]['id']
        else:
            return False, None
    except Exception as e:
        st.error(f"Error al verificar si el archivo existe en Google Drive: {e}")
        return False, None

# Función para subir o actualizar un archivo en Google Drive
def upload_to_drive(file_name):
    try:
        service = authenticate_google_drive()
        file_exists, file_id = file_exists_in_drive(file_name)

        if file_exists:
            # Actualiza el archivo existente
            media = MediaFileUpload(file_name, mimetype='text/csv')
            service.files().update(fileId=file_id, media_body=media).execute()
            st.success(f"Archivo actualizado en Google Drive: {file_name}")
        else:
            # Crea un archivo nuevo
            file_metadata = {'name': file_name}
            media = MediaFileUpload(file_name, mimetype='text/csv')
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            st.success(f"Archivo guardado en Google Drive: {file_name}")

    except Exception as e:
        st.error(f"Error al subir el archivo a Google Drive: {e}")

# Solicitar credenciales al usuario
def login():
    user = st.text_input("Usuario", type="default")
    password = st.text_input("Contraseña", type="password")
    if user == "falla_aguda" and password == "erick":
        st.success("Inicio de sesión exitoso")
        return True
    else:
        st.error("Usuario o contraseña incorrectos")
        return False

# Crear o actualizar archivo CSV
def save_data_to_csv(data, file_name='falla_cardiaca_datos.csv'):
    if os.path.exists(file_name):
        existing_data = pd.read_csv(file_name)
        combined_data = pd.concat([existing_data, data], ignore_index=True)
    else:
        combined_data = data
    
    combined_data.to_csv(file_name, index=False)
    st.write("Datos guardados en el archivo CSV.")
    return file_name

# Interfaz de Streamlit
if login():
    st.title("Registro de datos para pacientes con falla cardiaca aguda")

    # Entradas del formulario
    nombre = st.text_input("Nombre del paciente")
    edad = st.number_input("Edad", min_value=0, max_value=120)
    genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
    presion_arterial = st.text_input("Presión arterial")
    frecuencia_cardiaca = st.number_input("Frecuencia cardíaca (lpm)", min_value=0)
    frecuencia_respiratoria = st.number_input("Frecuencia respiratoria (rpm)", min_value=0)
    saturacion_oxigeno = st.number_input("Saturación de oxígeno (%)", min_value=0, max_value=100)
    ntproBNP = st.number_input("NT-proBNP", min_value=0)
    creatinina = st.number_input("Creatinina (mg/dL)", min_value=0.0, format="%.2f")
    comentario = st.text_area("Comentarios adicionales")

    # Crear un DataFrame con los datos ingresados
    data = pd.DataFrame({
        'Nombre': [nombre],
        'Edad': [edad],
        'Género': [genero],
        'Presión Arterial': [presion_arterial],
        'Frecuencia Cardíaca': [frecuencia_cardiaca],
        'Frecuencia Respiratoria': [frecuencia_respiratoria],
        'Saturación de Oxígeno': [saturacion_oxigeno],
        'NT-proBNP': [ntproBNP],
        'Creatinina': [creatinina],
        'Comentarios': [comentario]
    })

    if st.button("Guardar datos"):
        file_name = save_data_to_csv(data)
        upload_to_drive(file_name)

