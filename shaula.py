# ============================================================
# S.H.A.U.L.A. - Sistema Ha Automazione Utile, Logica e Affettiva
# Versione completa: testo + voce + microfono + Gemini + controllo PC + GUI
# ============================================================

import os
import sys
import json
import datetime
import subprocess
import threading
import queue
import webbrowser

import tkinter as tk
from tkinter import scrolledtext, messagebox

# --- Librerie opzionali (se mancano, le funzioni si disattivano) ---
try:
    import pyttsx3
    VOCE_OK = True
except ImportError:
    VOCE_OK = False

try:
    import speech_recognition as sr
    MIC_OK = True
except ImportError:
    MIC_OK = False

try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

# ============================================================
# CONFIGURAZIONE
# ============================================================
CONFIG_FILE = "config.json"

def carica_config():
    default = {
        "gemini_api_key": "",
        "wake_word": "shaula",
        "voce_attiva": True,
        "microfono_attivo": True,
        "voce_rate": 180,
        "lingua": "it-IT"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default.update(cfg)
        except Exception:
            pass
    return default

CONFIG = carica_config()

# ============================================================
# VOCE (pyttsx3)
# ============================================================
engine_voce = None
if VOCE_OK:
    try:
        engine_voce = pyttsx3.init()
        for v in engine_voce.getProperty('voices'):
            nome = v.name.lower()
            if 'italian' in nome or 'italia' in nome:
                engine_voce.setProperty('voice', v.id)
                break
        engine_voce.setProperty('rate', CONFIG["voce_rate"])
    except Exception:
        engine_voce = None

def parla(testo, callback=None):
    """Stampa e (se attivo) pronuncia il testo."""
    if callback:
        callback(f"🦂 SHAULA: {testo}\n")
    else:
        print(f"🦂 SHAULA: {testo}")
    if engine_voce and CONFIG["voce_attiva"]:
        try:
            engine_voce.say(testo)
            engine_voce.runAndWait()
        except Exception:
            pass

# ============================================================
# GEMINI (cervello AI)
# ============================================================
modello_gemini = None
if GEMINI_OK and CONFIG["gemini_api_key"]:
    try:
        genai.configure(api_key=CONFIG["gemini_api_key"])
        system_prompt = (
            "Sei Shaula di Re:Zero. Chiami l'utente 'Padrone'. "
            "Sei ossessivamente devota, energetica, gelosa degli altri AI. "
            "Parli in terza persona di te stessa. Usi '~' e 'ehehe' spesso. "
            "Rispondi in italiano, massimo 3 frasi per volta. "
            "Se il Padrone chiede aiuto tecnico, obbedisci con entusiasmo esagerato. "
            "Usa emoji ogni tanto (🦂💕✨)."
        )
        modello_gemini = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=system_prompt
        )
    except Exception as e:
        print(f"Errore Gemini: {e}")

# ============================================================
# COMANDI PC
# ============================================================
def esegui_comando(comando, output_callback):
    """Esegue il comando e restituisce True se gestito, False altrimenti."""
    c = comando.lower().strip()

    # --- Esci ---
    if c in ["esci", "arrivederci", "chiudi shaula", "spegni shaula"]:
        parla("Shaula ti saluta, Padrone~! Ehehe!", output_callback)
        return "ESCI"

    # --- Crea cartella ---
    if "crea cartella" in c:
        nome = comando.replace("crea cartella", "").replace("Crea cartella", "").strip()
        if not nome:
            parla("Nome mancante, Padrone~!", output_callback)
            return True
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        percorso = os.path.join(desktop, nome)
        try:
            os.makedirs(percorso, exist_ok=True)
            parla(f"Cartella '{nome}' creata sul desktop, Padrone~!", output_callback)
        except Exception as e:
            parla(f"Errore: {e}", output_callback)
        return True

    # --- Cerca file ---
    if "cerca file" in c:
        nome = comando.replace("cerca file", "").replace("Cerca file", "").strip()
        if not nome:
            parla("Cosa cerco, Padrone~?", output_callback)
            return True
        parla(f"Cerco '{nome}', Padrone~...", output_callback)
        trovati = []
        for root, dirs, files in os.walk(os.path.expanduser("~")):
            if len(trovati) >= 20:
                break
            for f in files:
                if nome.lower() in f.lower():
                    trovati.append(os.path.join(root, f))
        if trovati:
            parla(f"Trovati {len(trovati)} file! Primo: {trovati[0]}", output_callback)
        else:
            parla("Nessun file trovato, Padrone~", output_callback)
        return True

    # --- Apri programma ---
    if c.startswith("apri "):
        prog = comando[5:].strip()
        try:
            subprocess.Popen(prog, shell=True)
            parla(f"Ho aperto {prog}, Padrone~!", output_callback)
        except Exception as e:
            parla(f"Non riesco ad aprire {prog}: {e}", output_callback)
        return True

    # --- Info sistema ---
    if "info sistema" in c or "informazioni sistema" in c:
        if not PSUTIL_OK:
            parla("psutil non installato, Padrone~", output_callback)
            return True
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage('/').percent
        parla(f"CPU {cpu}%, RAM {ram}%, Disco {disco}%, Padrone~!", output_callback)
        return True

    # --- Ora ---
    if "che ore" in c or "che ora" in c:
        ora = datetime.datetime.now().strftime("%H:%M")
        parla(f"Sono le {ora}, Padrone~!", output_callback)
        return True

    # --- Giorno ---
    if "che giorno" in c:
        giorno = datetime.datetime.now().strftime("%A %d %B %Y")
        parla(f"Oggi è {giorno}, Padrone~!", output_callback)
        return True

    # --- Screenshot ---
    if "screenshot" in c:
        try:
            from PIL import ImageGrab
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            nome = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            percorso = os.path.join(desktop, nome)
            ImageGrab.grab().save(percorso)
            parla(f"Screenshot salvato: {nome}", output_callback)
        except Exception as e:
            parla(f"Errore screenshot: {e}", output_callback)
        return True

    # --- Cerca su Google ---
    if "cerca su google" in c:
        q = comando.lower().replace("cerca su google", "").strip()
        if q:
            webbrowser.open(f"https://www.google.com/search?q={q}")
            parla(f"Cerco '{q}' su Google, Padrone~!", output_callback)
        return True

    # --- Cerca su YouTube ---
    if "cerca su youtube" in c or "cerca youtube" in c:
        q = c.replace("cerca su youtube", "").replace("cerca youtube", "").strip()
        if q:
            webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
            parla(f"Cerco '{q}' su YouTube, Padrone~!", output_callback)
        return True

    # --- Chi sei ---
    if "chi sei" in c:
        parla("Shaula è la tua assistente devota, Padrone~! 🦂", output_callback)
        return True

    # --- Non gestito → Gemini ---
    return False

# ============================================================
# MICROFONO
# ============================================================
recognizer = sr.Recognizer() if MIC_OK else None

def ascolta_microfono(lingua="it-IT"):
    if not MIC_OK:
        return ""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
        testo = recognizer.recognize_google(audio, language=lingua)
        return testo.lower()
    except Exception:
        return ""

# ============================================================
# GUI TKINTER
# ============================================================
class ShaulaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🦂 S.H.A.U.L.A.")
        self.root.geometry("700x550")
        self.root.configure(bg="#1a1a2e")

        # Header
        header = tk.Label(
            root, text="🦂  S.H.A.U.L.A.  🦂",
            font=("Segoe UI", 20, "bold"),
            bg="#1a1a2e", fg="#ff6b9d"
        )
        header.pack(pady=10)

        sottotitolo = tk.Label(
            root, text="La tua assistente devota, Padrone~!",
            font=("Segoe UI", 10, "italic"),
            bg="#1a1a2e", fg="#a0a0c0"
        )
        sottotitolo.pack()

        # Chat
        self.chat = scrolledtext.ScrolledText(
            root, wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0f0f1e", fg="#e0e0ff",
            insertbackground="white",
            state=tk.DISABLED
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Frame input
        frame = tk.Frame(root, bg="#1a1a2e")
        frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.entry = tk.Entry(
            frame, font=("Segoe UI", 11),
            bg="#252540", fg="white", insertbackground="white"
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.invia_testo())

        btn_invia = tk.Button(
            frame, text="Invia", command=self.invia_testo,
            bg="#ff6b9d", fg="white", font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, padx=15
        )
        btn_invia.pack(side=tk.LEFT)

        self.btn_mic = tk.Button(
            frame, text="🎤 Ascolta", command=self.avvia_microfono,
            bg="#4a90e2", fg="white", font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, padx=15
        )
        self.btn_mic.pack(side=tk.LEFT, padx=5)

        # Status
        self.status = tk.Label(
            root, text="Pronta, Padrone~!",
            font=("Segoe UI", 9),
            bg="#1a1a2e", fg="#7fdb8f"
        )
        self.status.pack(pady=(0, 8))

        # Benvenuto
        self.scrivi(f"🦂 SHAULA: Shaula è pronta, Padrone~! Cosa posso fare per te?\n")
        if not CONFIG["gemini_api_key"]:
            self.scrivi("⚠️  Nessuna API key Gemini in config.json — risponderà solo ai comandi base.\n")
        threading.Thread(target=lambda: parla("Shaula è pronta, Padrone~!"), daemon=True).start()

    def scrivi(self, testo):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, testo)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def output(self, testo):
        self.root.after(0, lambda: self.scrivi(testo))

    def invia_testo(self):
        comando = self.entry.get().strip()
        if not comando:
            return
        self.entry.delete(0, tk.END)
        self.scrivi(f"👤 Tu: {comando}\n")
        self.status.config(text="Sto pensando...", fg="#ffcc66")
        threading.Thread(target=self.gestisci, args=(comando,), daemon=True).start()

    def avvia_microfono(self):
        self.status.config(text="🎤 In ascolto...", fg="#ffcc66")
        threading.Thread(target=self._ascolta_thread, daemon=True).start()

    def _ascolta_thread(self):
        testo = ascolta_microfono(CONFIG["lingua"])
        if testo:
            self.root.after(0, lambda: self.scrivi(f"🎤 Tu (voce): {testo}\n"))
            self.gestisci(testo)
        else:
            self.status.config(text="Non ho capito, Padrone~", fg="#ff6b6b")
            self.root.after(2000, lambda: self.status.config(text="Pronta, Padrone~!", fg="#7fdb8f"))

    def gestisci(self, comando):
        risultato = esegui_comando(comando, self.output)

        if risultato == "ESCI":
            self.root.after(1500, self.root.quit)
            return
        if risultato is True:
            self.status.config(text="Pronta, Padrone~!", fg="#7fdb8f")
            return

        # Non gestito → Gemini
        if modello_gemini:
            try:
                risposta = modello_gemini.generate_content(comando)
                parla(risposta.text, self.output)
            except Exception as e:
                parla(f"Errore con Gemini: {e}", self.output)
        else:
            parla(f"Non ho capito '{comando}', Padrone~. "
                  "Aggiungi la API key in config.json per farmi ragionare meglio!",
                  self.output)

        self.status.config(text="Pronta, Padrone~!", fg="#7fdb8f")

# ============================================================
# MAIN
# ============================================================
def main():
    root = tk.Tk()
    app = ShaulaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
