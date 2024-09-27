import requests
import os

# Clé API et informations Airtable
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

# Fonction pour uploader le fichier sur un service temporaire (file.io)
def upload_to_temp_storage(file_path):
    with open(file_path, 'rb') as file_data:
        response = requests.post('https://file.io', files={'file': file_data})
        if response.status_code == 200:
            return response.json().get('link')  # Retourne le lien de téléchargement
        else:
            raise Exception(f"Erreur lors du téléchargement du fichier: {response.content}")

# Fonction pour télécharger les fichiers VCF sur Airtable via l'URL temporaire
def upload_vcf_to_airtable(record_id, vcf_public_url):
    json_data = {
        "fields": {
            "Fichier VCF": [
                {
                    "url": vcf_public_url  # URL publique temporaire
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

# Fonction pour récupérer les données depuis Airtable
def fetch_airtable_data():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['records']
        return records
    else:
        print(f"Erreur lors de la récupération des données : {response.content}")
        return []

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
        
        # Uploader sur un service temporaire et obtenir l'URL publique
        vcf_public_url = upload_to_temp_storage(vcf_file_path)
        
        # Télécharger le lien dans Airtable
        upload_vcf_to_airtable(record_id, vcf_public_url)

print("Les fichiers VCF ont été créés et ajoutés dans Airtable.")
