import os
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
import pytesseract
from programma import Programma
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
import uvicorn

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret",  # Cambia questo con una chiave segreta sicura
)

app.mount("/static", StaticFiles(directory="templates/static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

templates = Jinja2Templates(directory="templates")

# Configura il percorso di Tesseract (potrebbe essere necessario modificarlo)
pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'  # Esempio per Windows

# Inizializza la classe Programma per la gestione del database
programma = Programma()

# Percorso per salvare le immagini caricate
UPLOAD_FOLDER = 'images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_current_user(request: Request):
    try:
        username = request.session.get("username")
        if username:
            user_id = programma._get_user_id(username)
            if user_id:
                user = programma._get_user_by_id(user_id)
                return user
        return None
    except Exception as e:
        print(f"Errore nel recupero dell'utente: {str(e)}")
        return None

@app.get("/")
async def index(request: Request):
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        if username and password:
            if programma._verifica_accesso(username, password):
                request.session["username"] = username
                return RedirectResponse(url="/utente_home", status_code=303)
            else:
                return templates.TemplateResponse("login.html", {"request": request, "error": "Credenziali non valide"})
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Dati mancanti"})
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Errore durante il login: {str(e)}"})

@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), nome: str = Form(...), cognome: str = Form(...)):
    try:
        if username and password and nome and cognome:
            success, message = programma._add_user(username, password, nome, cognome)
            if success:
                return templates.TemplateResponse("register.html", {
                    "request": request,
                    "success": message,
                    "show_login_link": True
                })
            else:
                return templates.TemplateResponse("register.html", {
                    "request": request,
                    "error": message
                })
        else:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Dati mancanti"
            })
    except Exception as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": f"Errore durante la registrazione: {str(e)}"
        })

@app.get("/register")
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    try:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        return JSONResponse({"error": f"Errore durante il logout: {str(e)}"}, status_code=500)

@app.get("/utente_home")
async def utente_home(request: Request):
    try:
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/login", status_code=303)
        
        immagini = programma._get_all_immagini()
        return templates.TemplateResponse("utenti/dashboard_utenti.html", {"request": request, "user": user, "immagini": immagini})
    except Exception as e:
        return templates.TemplateResponse("utenti/dashboard_utenti.html", {"request": request, "error": f"Errore nel caricamento della dashboard: {str(e)}"})

@app.post("/upload")
async def upload_image(request: Request, image: UploadFile = File(...), tag: str = Form(...), descrizione: str = Form(...), titolo: str = Form(...)):
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Utente non autenticato")

        if not image.filename:
            raise HTTPException(status_code=400, detail="Nome del file immagine non valido")

        # Verifica il tipo di file
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Il file deve essere un'immagine")

        # Salva l'immagine
        image_path = os.path.join(UPLOAD_FOLDER, image.filename)
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)

        # Esegui l'analisi del testo con Tesseract OCR
        text = estrai_testo_da_immagine(image_path)

        # Ottieni l'URL dell'immagine
        image_url = "/images/" + image.filename

        # Aggiungi le informazioni dell'immagine al database
        programma._add_immagine(user.id, image_url, tag, descrizione, titolo)

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

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000) 