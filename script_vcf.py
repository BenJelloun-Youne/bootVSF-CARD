import requests
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes pour l'API Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# Fonction pour créer le service Google Drive avec authentification
def create_drive_service():
    creds = None
    # Le fichier token.json stocke les tokens d'accès et de rafraîchissement de l'utilisateur
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Si les credentials ne sont pas valides, on procède à l'authentification
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Le fichier credentials.json doit être dans le même répertoire que ce script
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_console()
        # Sauvegarder les credentials pour la prochaine exécution
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('drive', 'v3', credentials=creds)
    return service

# Fonction pour rendre un fichier partageable sur Google Drive
def generate_public_url(file_id):
    drive_service = create_drive_service()
    
    # Changer les permissions pour rendre le fichier public
    drive_service.permissions().create(
        fileId=file_id,
        body={'role': 'reader', 'type': 'anyone'},
    ).execute()
    
    # Obtenir le lien partageable
    share_link = f"https://drive.google.com/uc?id={file_id}&export=download"
    return share_link

# Clé API et informations Airtable (en clair comme demandé)
AIRTABLE_API_KEY = 'pat5ROT69wWTzJh0z.33dd5edb3a06e3d274b3645653feed9f2da64cc93661e244bac7a9d57f3fcffd'
BASE_ID = 'app3bh6X0MpfH4Bql'
TABLE_ID = 'tbl45xlWKsSOvmKb5'

# URL de l'API Airtable pour la base et la table spécifiées
url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'

# En-têtes pour l'authentification via l'API token
headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# Répertoire pour stocker les fichiers VCF
vcf_directory = os.path.join(os.getcwd(), 'Fichiers VCF')
os.makedirs(vcf_directory, exist_ok=True)

# Fonction pour créer un fichier VCF avec plusieurs numéros de téléphone
def create_vcf(contact):
    vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact['nom']}
N:{contact['nom']};;;;
"""
    # Ajouter les numéros de téléphone disponibles
    if contact.get('numero1'):
        vcf_content += f"TEL;TYPE=CELL:{contact['numero1']}\n"
    if contact.get('numero2'):
        vcf_content += f"TEL;TYPE=CELL:{contact['numero2']}\n"
    if contact.get('numero3'):
        vcf_content += f"TEL;TYPE=CELL:{contact['numero3']}\n"

    vcf_content += "END:VCARD\n"

    # Génère le nom du fichier VCF
    file_name = f"{contact['nom']}.vcf"
    file_path = os.path.join(vcf_directory, file_name)
    
    # Enregistre le fichier VCF
    with open(file_path, 'w') as vcf_file:
        vcf_file.write(vcf_content)
    
    return file_path

# Fonction pour récupérer les données depuis Airtable
def fetch_airtable_data():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['records']
        return records
    else:
        print(f"Erreur lors de la récupération des données : {response.content}")
        return []

# Fonction pour télécharger les fichiers VCF sur Google Drive et obtenir le lien public
def upload_to_drive_and_get_link(file_path):
    drive_service = create_drive_service()
    file_name = os.path.basename(file_path)
    
    # Télécharger le fichier sur Google Drive
    file_metadata = {'name': file_name, 'mimeType': 'text/vcard'}
    media = MediaFileUpload(file_path, mimetype='text/vcard')
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    # Rendre le fichier public et obtenir l'URL
    file_id = uploaded_file.get('id')
    public_url = generate_public_url(file_id)
    
    return public_url

# Fonction pour mettre à jour Airtable avec l'URL du fichier VCF
def upload_vcf_to_airtable(record_id, vcf_public_url):
    json_data = {
        "fields": {
            "Fichier VCF": [
                {
                    "url": vcf_public_url
                }
            ]
        }
    }
    
    airtable_upload_url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}/{record_id}'
    response = requests.patch(airtable_upload_url, headers=headers, json=json_data)
    
    if response.status_code == 200:
        print(f"VCF ajouté pour l'enregistrement {record_id}")
    else:
        print(f"Erreur lors de l'ajout du VCF pour l'enregistrement {record_id}: {response.content}")

# Récupérer les données depuis Airtable
records = fetch_airtable_data()

# Créer les vCards pour chaque enregistrement et les télécharger sur Drive, puis les attacher dans Airtable
for record in records:
    fields = record['fields']
    record_id = record['id']
    
    if 'Nom' in fields and 'Numéro 1' in fields:
        contact = {
            "nom": fields['Nom'],
            "numero1": fields.get('Numéro 1', ''),
            "numero2": fields.get('Numéro 2', ''),
            "numero3": fields.get('Numéro 3', '')
        }
        # Créer le fichier VCF
        vcf_file_path = create_vcf(contact)
        
        # Télécharger sur Google Drive et obtenir l'URL publique
        vcf_public_url = upload_to_drive_and_get_link(vcf_file_path)
        
        # Télécharger le lien dans Airtable
        upload_vcf_to_airtable(record_id, vcf_public_url)

print("Les fichiers VCF ont été créés, téléchargés sur Google Drive, et ajoutés dans Airtable.")
