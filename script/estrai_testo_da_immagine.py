import os
import time
import base64
import json
import shutil
import requests
import re
import hashlib
from dotenv import load_dotenv

load_dotenv()

def estrai_testo_da_immagine(percorso_file, max_retries=3):
    """Estrai il testo reale da un'immagine con l'API OpenAI."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Errore: OPENAI_API_KEY non trovata nel file .env")
        return ""

    with open(percorso_file, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Estrai il testo contenuto in questa immagine in italiano. Non aggiungere prefissi o spiegazioni, restituisci solo il testo."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            }
        ],
        "max_tokens": 1000
    }

    for attempt in range(max_retries):
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                risultato = response.json()
                testo = risultato['choices'][0]['message']['content']
                return testo.strip()
            elif response.status_code == 429:
                print("Rate limit superato. Attendo 20 secondi...")
                time.sleep(20)
        except Exception as e:
            print(f"Errore: {e}")

    return ""

def estrai_categoria_tags_da_testo(testo, max_retries=3):
    """Analizza il testo e restituisce una categoria e almeno 10 tag."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Errore: OPENAI_API_KEY non trovata nel file .env")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    prompt = (
        "Analizza il seguente testo e assegna una categoria appropriata. "
        "Devi anche estrarre almeno 10 tag pertinenti. "
        "Rispondi solo con un JSON nel formato:\n"
        '{"categoria": "categoria", "tags": ["tag1", "tag2", ..., "tag10+"]}\n\n'
        f"Testo: \"{testo}\""
    )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "max_tokens": 200
    }

    for attempt in range(max_retries):
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                risultato = response.json()
                output = risultato['choices'][0]['message']['content']
                try:
                    data = json.loads(output)
                    categoria = data.get("categoria", "generico")
                    tags = data.get("tags", [])
                    return {"categoria": categoria, "tags": tags}
                except json.JSONDecodeError:
                    print("Errore nel parsing JSON.")
        except Exception as e:
            print(f"Errore: {e}")

    return {"categoria": "generico", "tags": []}

def genera_nome_file(categoria, testo, id_immagine, estensione):
    """Genera un nome di file leggibile senza limitazione di caratteri."""
    testo_pulito = re.sub(r'\s+', '_', testo.strip())  # Sostituisce spazi con underscore
    testo_pulito = re.sub(r'[^\w\d_]', '', testo_pulito)  # Rimuove caratteri speciali
    hash_id = hashlib.sha1(testo.encode()).hexdigest()[:6]  # Hash per evitare duplicati
    return f"{categoria}_{testo_pulito}_{id_immagine}_{hash_id}{estensione}"

def processa_immagini(cartella_img, cartella_dest, metadata_file):
    """Processa le immagini, assegna nome e tag, e crea un JSON di metadata."""
    if not os.path.exists(cartella_dest):
        os.makedirs(cartella_dest)

    metadata = []
    id_counter = 1

    for nome_file in os.listdir(cartella_img):
        percorso_file = os.path.join(cartella_img, nome_file)
        if os.path.isfile(percorso_file) and nome_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"\nElaborazione di: {nome_file}")
            testo_estratto = estrai_testo_da_immagine(percorso_file)
            print(f"Testo estratto: {testo_estratto}")
            classificazione = estrai_categoria_tags_da_testo(testo_estratto)
            categoria = classificazione["categoria"]
            tags = classificazione["tags"]
            print(f"Categoria: {categoria} | Tags: {tags}")

            estensione = os.path.splitext(nome_file)[1]
            nuovo_nome = genera_nome_file(categoria, testo_estratto, id_counter, estensione)
            percorso_dest = os.path.join(cartella_dest, nuovo_nome)

            shutil.move(percorso_file, percorso_dest)
            print(f"Immagine spostata in '{percorso_dest}'")

            metadata.append({
                "id": id_counter,
                "nome_file": nuovo_nome,
                "percorso": percorso_dest,
                "categoria": categoria,
                "tags": tags,
                "testo_estratto": testo_estratto
            })
            id_counter += 1

            print("Attendo 20 secondi per rispettare il rate limit...")
            time.sleep(20)

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    print(f"\nMetadata salvato in {metadata_file}")

if __name__ == "__main__":
    cartella_img = "./img"
    cartella_dest = "./img_tipizzate"
    metadata_file = "./metadata.json"
    processa_immagini(cartella_img, cartella_dest, metadata_file)
