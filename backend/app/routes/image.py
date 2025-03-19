from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from PIL import Image
import pytesseract
import os
from ..database import programma
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/utente_home")
async def utente_home(request: Request):
    try:
        user = get_current_user(request)
        if not user:
            print("Utente non autenticato, reindirizzamento al login")
            return RedirectResponse(url="/login", status_code=303)
        
        print(f"Utente autenticato: {user['username']}")
        immagini = programma._get_all_immagini()
        print(f"Immagini recuperate: {len(immagini)}")
        
        return templates.TemplateResponse(
            "utenti/dashboard_utenti.html", 
            {
                "request": request, 
                "user": user, 
                "immagini": immagini
            }
        )
    except Exception as e:
        print(f"Errore nel caricamento della dashboard: {str(e)}")
        return templates.TemplateResponse(
            "utenti/dashboard_utenti.html", 
            {
                "request": request, 
                "error": f"Errore nel caricamento della dashboard: {str(e)}"
            }
        )

@router.post("/upload")
async def upload_image(request: Request, 
                      image: UploadFile = File(...), 
                      tag: str = Form(...), 
                      descrizione: str = Form(...), 
                      titolo: str = Form(...)):
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Utente non autenticato")

        if not image.filename:
            raise HTTPException(status_code=400, detail="Nome del file immagine non valido")

        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Il file deve essere un'immagine")

        # Salva l'immagine
        image_path = os.path.join('app/images', image.filename)
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)

        # Esegui l'analisi del testo con Tesseract OCR
        text = estrai_testo_da_immagine(image_path)

        # Ottieni l'URL dell'immagine
        image_url = "/images/" + image.filename

        # Aggiungi le informazioni dell'immagine al database
        programma._add_immagine(user[0], image_url, tag, descrizione, titolo)

        # Rimuovi l'immagine dopo l'analisi
        os.remove(image_path)

        return JSONResponse({
            'filename': image.filename,
            'text': text,
            'url': image_url,
            'tag': tag,
            'descrizione': descrizione,
            'titolo': titolo
        }, status_code=200)

    except HTTPException as he:
        return JSONResponse({'error': he.detail}, status_code=he.status_code)
    except Exception as e:
        return JSONResponse({'error': f"Errore durante il caricamento: {str(e)}"}, status_code=500)

def estrai_testo_da_immagine(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='ita')
        return text
    except Exception as e:
        return f"Errore nell'estrazione del testo: {str(e)}" 