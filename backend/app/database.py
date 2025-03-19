import sqlite3
import bcrypt
import os

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
            print(f"Tabelle create con successo nel database '{self.db_name}'")
        except sqlite3.Error as e:
            print(f"Errore durante la creazione delle tabelle: {e}")

    def _add_user(self, username, password, nome, cognome, email, data_nascita):
        try:
            print(f"Tentativo di registrazione per l'utente: {username}")
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users WHERE username = ? OR email = ?', (username, email))
                if cursor.fetchone():
                    print(f"Username o email già esistente")
                    return False, "Username o email già in uso"

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
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                
                if user:
                    print(f"Utente trovato nel database: {username}")
                    stored_password = user[2]
                    print(f"Password hashata nel database: {stored_password}")
                    
                    password_bytes = password.encode('utf-8')
                    print(f"Password inserita in bytes: {password_bytes}")
                    
                    stored_password_bytes = stored_password.encode('utf-8')
                    print(f"Password hashata dal database in bytes: {stored_password_bytes}")
                    
                    is_valid = bcrypt.checkpw(password_bytes, stored_password_bytes)
                    print(f"Verifica password per {username}: {'valida' if is_valid else 'non valida'}")
                    return is_valid
                print(f"Utente non trovato nel database: {username}")
                return False
        except Exception as e:
            print(f"Errore durante la verifica dell'accesso: {e}")
            return False

    def _get_user_id(self, username):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                return user[0]
            return None

    def _get_user_by_id(self, user_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            return user

    def _get_all_immagini(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM immagini')
            immagini = cursor.fetchall()
            return immagini

    def _add_immagine(self, user_id, url, tag, descrizione, titolo):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO immagini (user_id, url, tag, descrizione, titolo)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, url, tag, descrizione, titolo))
            conn.commit() 