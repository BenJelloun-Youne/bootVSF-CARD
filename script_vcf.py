import os
import requests

# Token d'accès à Airtable
AIRTABLE_API_KEY = 'patJlXWVeHJo0FIlV.9928df26ace030f55b9fb482d70f6f19d7149fa960fcdc37b1a0e86cba9c6611'

# Base et table Airtable
BASE_ID = 'app7VeyHWjERCjVQK'
TABLE_ID = 'tblU6E3rHJ31FoMWO'

# URL de l'API Airtable pour la base et la table spécifiées
url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'

# En-têtes pour l'authentification via l'API token
headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# Répertoire local pour stocker les fichiers VCF dans GitHub Actions
vcf_directory = './Fichiers_VCF/'
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
    
    return file_name  # Retourne juste le nom du fichier

# Fonction pour récupérer les données depuis Airtable
def fetch_airtable_data():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['records']
        return records
    else:
        print(f"Erreur lors de la récupération des données : {response.content}")
        return []

# Fonction pour générer un lien public basé sur l'ID du fichier dans Google Drive
def generate_public_link(file_id):
    return f"https://drive.google.com/uc?export=download&id={file_id}"

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

# Créer les vCards pour chaque enregistrement et générer un lien public
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
        # Créer le fichier VCF localement
        vcf_file_name = create_vcf(contact)
        
        # Génère le lien de téléchargement basé sur l'ID du fichier
        print(f"Ajoute manuellement le fichier dans Google Drive : {vcf_file_name}")
        file_id = input(f"Entre l'ID Google Drive pour {vcf_file_name}: ")

        # Générer le lien public du fichier
        vcf_public_url = generate_public_link(file_id)
        
        # Télécharger le lien dans Airtable
        upload_vcf_to_airtable(record_id, vcf_public_url)

print(f"Les fichiers VCF ont été créés localement et les liens publics ont été ajoutés dans Airtable.")
