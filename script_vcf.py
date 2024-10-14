import requests
import os
import base64
import time
from requests.exceptions import RequestException

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

def encode_image_to_base64(image_url):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            encoded_image = base64.b64encode(response.content).decode('utf-8')
            return encoded_image
        else:
            print(f"Erreur lors du téléchargement de l'image : {response.status_code}")
            return None
    except Exception as e:
        print(f"Erreur lors de l'encodage de l'image : {e}")
        return None

def create_vcf(contact):
    vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact['nom']}
N:{contact['nom']};;;;
"""
    if contact.get('numero1'):
        vcf_content += f"TEL;TYPE=CELL:{contact['numero1']}\n"
    if contact.get('numero2'):
        vcf_content += f"TEL;TYPE=CELL:{contact['numero2']}\n"
    if contact.get('numero3'):
        vcf_content += f"TEL;TYPE=CELL:{contact['numero3']}\n"
    
    if contact.get('image_base64'):
        vcf_content += f"PHOTO;ENCODING=b;TYPE=JPEG:{contact['image_base64']}\n"

    vcf_content += "END:VCARD\n"

    file_name = f"{contact['nom']}.vcf"
    file_path = os.path.join(vcf_directory, file_name)
    
    with open(file_path, 'w') as vcf_file:
        vcf_file.write(vcf_content)
    
    return file_path

def upload_to_temp_storage(file_path, max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            with open(file_path, 'rb') as file_data:
                response = requests.post('https://file.io', 
                                         files={'file': ('vcard.vcf', file_data, 'text/vcard')})
            response.raise_for_status()
            return response.json().get('link')
        except RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Erreur lors du téléchargement du fichier après {max_retries} tentatives: {e}")
            print(f"Tentative {attempt + 1} échouée. Nouvelle tentative dans {delay} secondes...")
            time.sleep(delay)

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

def fetch_airtable_data():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['records']
        return records
    else:
        print(f"Erreur lors de la récupération des données : {response.content}")
        return []

def main():
    records = fetch_airtable_data()

    for record in records:
        fields = record['fields']
        record_id = record['id']
        
        if 'Nom' in fields and 'Numéro 1' in fields:
            try:
                contact = {
                    "nom": fields['Nom'],
                    "numero1": fields.get('Numéro 1', ''),
                    "numero2": fields.get('Numéro 2', ''),
                    "numero3": fields.get('Numéro 3', '')
                }
                
                if 'Image' in fields and len(fields['Image']) > 0:
                    image_url = fields['Image'][0]['url']
                    contact['image_base64'] = encode_image_to_base64(image_url)
                
                vcf_file_path = create_vcf(contact)
                
                vcf_public_url = upload_to_temp_storage(vcf_file_path)
                
                upload_vcf_to_airtable(record_id, vcf_public_url)
                
                # Nettoyage
                os.remove(vcf_file_path)
                
            except Exception as e:
                print(f"Erreur lors du traitement de l'enregistrement {record_id}: {e}")
                continue

    print("Les fichiers VCF ont été créés et ajoutés dans Airtable.")

if __name__ == "__main__":
    main()
