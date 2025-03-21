import os
import time
import base64
import json
import shutil
import requests
import re
import hashlib
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

def genera_immagine_con_testo(testo, output_file="generated_image.jpg"):
    """Genera un'immagine 1080x1080 con un testo personalizzato."""
    img = Image.new('RGB', (1080, 1080), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        font = ImageFont.load_default()
    
    text_width, text_height = draw.textbbox((0, 0), testo, font=font)[2:]
    text_x = (1080 - text_width) // 2
    text_y = (1080 - text_height) // 2
    
    draw.text((text_x, text_y), testo, font=font, fill=(0, 0, 0))
    img.save(output_file)
    print(f"Immagine generata e salvata come {output_file}")

def estrai_testo_da_immagine(percorso_file, max_retries=3):
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

# Esempio di utilizzo
if __name__ == "__main__":
    testo_personalizzato = input("Inserisci il testo da includere nell'immagine: ")
    nome_file = input("Inserisci il nome del file di output (es. immagine): ") or "generated_image"
    
    # Assicuriamoci che il file abbia un'estensione
    if not nome_file.lower().endswith(('.jpg', '.jpeg', '.png')):
        nome_file += '.jpg'  # Aggiungiamo .jpg come estensione predefinita
        
    genera_immagine_con_testo(testo_personalizzato, nome_file)
