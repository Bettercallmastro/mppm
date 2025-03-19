import sqlite3
import bcrypt
import os

class User:
    def __init__(self, id, username, nome, cognome, email, data_nascita):
        self.id = id
        self.username = username
        self.nome = nome
        self.cognome = cognome
        self.email = email
        self.data_nascita = data_nascita

class Programma:
    def __init__(self, db_name='programma.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        nome TEXT NOT NULL,
                        cognome TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        data_nascita DATE NOT NULL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS immagini (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        url TEXT NOT NULL,
                        tag TEXT,
                        descrizione TEXT,
                        titolo TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interazioni (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        immagine_id INTEGER NOT NULL,
                        like INTEGER DEFAULT 0,
                        preferiti INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (immagine_id) REFERENCES immagini (id)
                    )
                ''')
                conn.commit()
            print(f"Tabelle 'users', 'immagini' e 'interazioni' create con successo nel database '{self.db_name}'.")
        except sqlite3.Error as e:
            print(f"Errore durante la creazione delle tabelle: {e}")

    def _add_user(self, username, password, nome, cognome, email, data_nascita):
        try:
            print(f"Tentativo di registrazione per l'utente: {username}")
            # Verifica se l'utente esiste già
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users WHERE username = ? OR email = ?', (username, email))
                if cursor.fetchone():
                    print(f"Username o email già esistente")
                    return False, "Username o email già in uso"

            # Converti la password in bytes e genera il salt
            password_bytes = password.encode('utf-8')
            print(f"Password originale in bytes: {password_bytes}")
            salt = bcrypt.gensalt()
            print(f"Salt generato: {salt}")
            hashed_password = bcrypt.hashpw(password_bytes, salt)
            print(f"Password hashata: {hashed_password}")
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password, nome, cognome, email, data_nascita) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, hashed_password.decode('utf-8'), nome, cognome, email, data_nascita))
                conn.commit()
                print(f"Utente {username} registrato con successo")
            return True, "Utente registrato con successo"
        except sqlite3.Error as e:
            print(f"Errore durante la registrazione: {e}")
            return False, f"Errore durante la registrazione: {str(e)}"
        except Exception as e:
            print(f"Errore imprevisto durante la registrazione: {e}")
            return False, f"Errore imprevisto durante la registrazione: {str(e)}"

    def _verifica_accesso(self, username, password):
        try:
            print(f"Verifica accesso per l'utente: {username}")
            with sqlite3.connect(self.db_name) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                
                if user:
                    print(f"Utente trovato nel database: {username}")
                    # Recupera la password hashata dal database
                    stored_password = user['password']
                    
                    # Converti la password inserita in bytes
                    password_bytes = password.encode('utf-8')
                    
                    # La password nel database è già in formato stringa, quindi dobbiamo convertirla in bytes
                    stored_password_bytes = stored_password.encode('utf-8')
                    
                    # Verifica la password
                    is_valid = bcrypt.checkpw(password_bytes, stored_password_bytes)
                    print(f"Verifica password per {username}: {'valida' if is_valid else 'non valida'}")
                    
                    if is_valid:
                        # Converti l'utente in un dizionario
                        return {
                            'id': user['id'],
                            'username': user['username'],
                            'nome': user['nome'],
                            'cognome': user['cognome'],
                            'email': user['email']
                        }
                    
                    return None
                
                print(f"Utente non trovato nel database: {username}")
                return None
        
        except Exception as e:
            print(f"Errore durante la verifica dell'accesso: {e}")
            return None

    def _get_user_id(self, username):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                return user['id']
            return None

    def _get_user_by_id(self, user_id):
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row  # Usa Row factory per accesso per nome
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user:
                # Converti esplicitamente in dizionario
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'nome': user['nome'],
                    'cognome': user['cognome'],
                    'email': user['email'],
                    'data_nascita': user['data_nascita']
                }
            return None

    def _get_all_users(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()
            return users

    def _add_immagine(self, user_id, url, tag, descrizione, titolo):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO immagini (user_id, url, tag, descrizione, titolo)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, url, tag, descrizione, titolo))
            conn.commit()

    def _get_immagine_by_id(self, immagine_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM immagini WHERE id = ?', (immagine_id,))
            immagine = cursor.fetchone()
            return immagine

    def _get_all_immagini(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM immagini')
            immagini = cursor.fetchall()
            return immagini

    def _add_interazione(self, user_id, immagine_id, like, preferiti):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO interazioni (user_id, immagine_id, like, preferiti)
                VALUES (?, ?, ?, ?)
            ''', (user_id, immagine_id, like, preferiti))
            conn.commit()

    def _get_interazione_by_id(self, interazione_id):
         with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM interazioni WHERE id = ?', (interazione_id,))
            interazione = cursor.fetchone()
            return interazione

    def _get_interazioni_by_user_id(self, user_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM interazioni WHERE user_id = ?', (user_id,))
            interazioni = cursor.fetchall()
            return interazioni

    def _get_interazioni_by_immagine_id(self, immagine_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM interazioni WHERE immagine_id = ?', (immagine_id,))
            interazioni = cursor.fetchall()
            return interazioni

    def _update_interazione(self, interazione_id, like, preferiti):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE interazioni
                SET like = ?,
                    preferiti = ?
                WHERE id = ?
            ''', (like, preferiti, interazione_id))
            conn.commit()
