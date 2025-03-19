from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from ..database import programma

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_current_user(request: Request):
    try:
        username = request.session.get("username")
        print(f"Username dalla sessione: {username}")
        if username:
            user_id = programma._get_user_id(username)
            print(f"User ID trovato: {user_id}")
            if user_id:
                user = programma._get_user_by_id(user_id)
                print(f"Utente trovato: {user}")
                return user
        print("Nessun utente trovato")
        return None
    except Exception as e:
        print(f"Errore nel recupero dell'utente: {str(e)}")
        return None

@router.get("/")
async def index(request: Request):
    return RedirectResponse(url="/login", status_code=303)

@router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        print(f"Tentativo di login per l'utente: {username}")
        if username and password:
            if programma._verifica_accesso(username, password):
                print(f"Login riuscito per l'utente: {username}")
                request.session["username"] = username
                return RedirectResponse(url="/utente_home", status_code=303)
            else:
                print(f"Login fallito per l'utente: {username} - Credenziali non valide")
                return templates.TemplateResponse("login.html", {"request": request, "error": "Credenziali non valide"})
        else:
            print("Login fallito - Dati mancanti")
            return templates.TemplateResponse("login.html", {"request": request, "error": "Dati mancanti"})
    except Exception as e:
        print(f"Errore durante il login: {str(e)}")
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Errore durante il login: {str(e)}"})

@router.get("/register")
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(request: Request, 
                  username: str = Form(...), 
                  password: str = Form(...), 
                  nome: str = Form(...), 
                  cognome: str = Form(...),
                  email: str = Form(...),
                  data_nascita: str = Form(...)):
    try:
        if username and password and nome and cognome and email and data_nascita:
            success, message = programma._add_user(username, password, nome, cognome, email, data_nascita)
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

@router.get("/logout")
async def logout(request: Request):
    try:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        return {"error": f"Errore durante il logout: {str(e)}"} 