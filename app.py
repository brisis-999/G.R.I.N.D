# app.py — GRIND v3.0 — PERSONALIDAD JARVIS-CHAT + TELEGRAM + NOTION + MEMORIA (UI OPTIMIZADA)
# Creado por Eliezer Mesac Feliz Luciano
# ¡Sin entrenar modelos! Solo ingeniería práctica.
# UI Optimizada para PCs con 4GB RAM — Fondo negro con estrellas estáticas (sin animaciones pesadas)

import requests
import os
import json
import sqlite3
import random
import logging
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import time
from queue import Queue

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("grind.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- CARGAR VARIABLES DE ENTORNO ---
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# --- VALIDACIÓN ---
if not GROQ_API_KEY:
    raise Exception("ERROR: GROQ_API_KEY no está configurada.")

# --- INICIALIZAR CHROMA Y SQLITE ---
client = chromadb.PersistentClient(path="./grind_memory")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name="conversations", embedding_function=sentence_transformer_ef)

conn = sqlite3.connect('grind.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, content TEXT, remind_at DATETIME)''')
conn.commit()

# --- COLA PARA TELEGRAM ---
message_queue = Queue()

# --- FUNCIONES DE MEMORIA (SIN CAMBIOS) ---

def save_preference(key, value):
    c.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def get_preference(key):
    c.execute("SELECT value FROM preferences WHERE key = ?", (key,))
    result = c.fetchone()
    return result[0] if result else None

def save_conversation(user_input, response, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    # Guardar en ChromaDB
    doc_id = f"conv_{int(time.time())}_{random.randint(1000,9999)}"
    try:
        collection.add(
            documents=[user_input + " → " + response],
            metadatas=[{"timestamp": timestamp, "type": "conversation"}],
            ids=[doc_id]
        )
    except Exception as e:
        logging.error(f"[CHROMA] Error al guardar: {e}")

    # Guardar en Notion
    if NOTION_API_KEY and NOTION_DATABASE_ID:
        try:
            url = "https://api.notion.com/v1/pages"
            headers = {
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            data = {
                "parent": {"database_id": NOTION_DATABASE_ID},
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": f"GRIND - {timestamp[:10]}"
                                }
                            }
                        ]
                    },
                    "Content": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"User: {user_input}\nGRIND: {response}"
                                }
                            }
                        ]
                    }
                }
            }
            notion_response = requests.post(url, json=data, headers=headers, timeout=10)
            if notion_response.status_code == 200:
                logging.info("[NOTION] ✅ Conversación guardada.")
            else:
                logging.warning(f"[NOTION] ⚠️ Error {notion_response.status_code}")
        except Exception as e:
            logging.error(f"[NOTION] ❌ Excepción: {e}")

def save_reminder(content, remind_at):
    c.execute("INSERT INTO reminders (content, remind_at) VALUES (?, ?)", (content, remind_at))
    conn.commit()

def get_due_reminders():
    now = datetime.now().isoformat()
    c.execute("SELECT id, content FROM reminders WHERE remind_at <= ?", (now,))
    reminders = c.fetchall()
    c.execute("DELETE FROM reminders WHERE remind_at <= ?", (now,))
    conn.commit()
    return reminders

def search_memory(query, n_results=3):
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas"]
        )
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        logging.error(f"[CHROMA SEARCH] Error: {e}")
        return []

# --- FUNCIONES DE IA (SIN CAMBIOS) ---

def mente_groq(prompt, model="llama3-70b-8192"):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500, "temperature": 0.7},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        logging.error(f"[GROQ] Error HTTP {response.status_code}")
        return f"[GROQ ERROR {response.status_code}]"
    except Exception as e:
        logging.error(f"[GROQ] Excepción: {e}")
        return f"[GROQ FALLÓ: {str(e)}]"

def extension_mistral(prompt):
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
            headers={"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {},
            json={"inputs": prompt, "parameters": {"max_new_tokens": 1500, "temperature": 0.7}},
            timeout=20
        )
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and "error" in result:
                logging.warning(f"[MISTRAL] Modelo cargando: {result.get('error')}")
                return mente_groq(f"[MISTRAL CARGANDO] {prompt}")
            if isinstance(result, list) and len(result) > 0:
                item = result[0]
                if isinstance(item, dict):
                    return item.get('generated_text', '').strip()
                else:
                    return str(item).strip()
            return str(result).strip()
        logging.error(f"[MISTRAL] Error HTTP {response.status_code}")
        return mente_groq(f"[MISTRAL HTTP {response.status_code}] {prompt}")
    except Exception as e:
        logging.error(f"[MISTRAL] Excepción: {e}")
        return mente_groq(f"[MISTRAL ERROR] {prompt}")

def extension_gemini(prompt):
    if not GEMINI_API_KEY:
        logging.warning("[GEMINI] Sin API key")
        return mente_groq(f"[GEMINI SIN KEY] {prompt}")
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates and len(candidates) > 0:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and len(parts) > 0:
                    return parts[0].get("text", "").strip()
            logging.warning("[GEMINI] Sin contenido en respuesta")
            return mente_groq(f"[GEMINI SIN RESPUESTA] {prompt}")
        logging.error(f"[GEMINI] Error HTTP {response.status_code}")
        return mente_groq(f"[GEMINI HTTP {response.status_code}] {prompt}")
    except Exception as e:
        logging.error(f"[GEMINI] Excepción: {e}")
        return mente_groq(f"[GEMINI ERROR] {prompt}")

def extension_phi3_local(prompt):
    try:
        full_prompt = f"""
        Actúa como un asistente útil, claro y conciso. Responde directamente sin rodeos.
        Pregunta: {prompt}
        Respuesta:
        """
        result = subprocess.run(
            ["ollama", "run", "phi3:mini"],
            input=full_prompt,
            text=True,
            capture_output=True,
            encoding='utf-8',
            timeout=60
        )
        if result.returncode == 0:
            response = result.stdout.strip()
            if "Respuesta:" in response:
                response = response.split("Respuesta:", 1)[-1].strip()
            return response if response else "[PHI-3 NO GENERÓ RESPUESTA]"
        else:
            error_msg = result.stderr.strip() if result.stderr else "Error desconocido"
            logging.error(f"[PHI-3] Error: {error_msg}")
            return mente_groq(f"[PHI-3 ERROR: {error_msg}] {prompt}")
    except FileNotFoundError:
        logging.error("[PHI-3] Ollama no instalado")
        return mente_groq(f"[OLLAMA NO INSTALADO] Por favor instala Ollama. {prompt}")
    except Exception as e:
        logging.error(f"[PHI-3] Excepción: {e}")
        return mente_groq(f"[PHI-3 FALLÓ: {str(e)}] {prompt}")

def extension_serpapi(query):
    if not SERPAPI_KEY:
        return extension_duckduckgo(query)
    try:
        params = {"engine": "google", "q": query, "api_key": SERPAPI_KEY, "gl": "es", "hl": "es"}
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("organic_results", [])
            if results and len(results) > 0:
                r = results[0]
                return f"{r.get('snippet', 'Sin resumen')}\n[Fuente: {r.get('title', 'Sin título')}]({r.get('link', '')})"
        return extension_duckduckgo(query)
    except Exception as e:
        logging.error(f"[SERPAPI] Error: {e}")
        return extension_duckduckgo(query)

def extension_duckduckgo(query):
    try:
        response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            abstract = data.get("AbstractText", "").strip()
            if abstract:
                return abstract
            related = data.get("RelatedTopics", [])
            if related:
                first = related[0]
                if isinstance(first, dict):
                    text = first.get("Text", "") or str(first)
                else:
                    text = str(first)
                return text[:500] + "..." if len(text) > 500 else text
        logging.warning("[DUCKDUCKGO] Sin resultados")
        return mente_groq(f"[DUCKDUCKGO SIN RESULTADOS] {query}")
    except Exception as e:
        logging.error(f"[DUCKDUCKGO] Error: {e}")
        return mente_groq(f"[DUCKDUCKGO ERROR] {query}")

# --- ROUTER (SIN CAMBIOS) ---

def router_consejo(user_input):
    u = user_input.lower()
    if any(kw in u for kw in ["código", "debug", "python", "javascript", "lógica", "matemática", "ecuación", "algoritmo"]):
        logging.info("[ROUTER] Usando Mistral para lógica/código")
        return extension_mistral(user_input)
    elif any(kw in u for kw in ["redacta", "ensayo", "estilo", "elegante", "motiva", "inspira", "emocional", "explica", "enseña", "describe", "resumen creativo"]):
        logging.info("[ROUTER] Usando Phi-3 Mini para redacción")
        return extension_phi3_local(user_input)
    elif any(kw in u for kw in ["rápido", "resumen", "documento largo", "velocidad", "extenso", "analiza este texto"]):
        logging.info("[ROUTER] Usando Gemini para contexto largo")
        return extension_gemini(user_input)
    elif any(kw in u for kw in ["busca", "investiga", "qué es", "define", "noticia", "fuente", "actualidad", "información sobre"]):
        logging.info("[ROUTER] Usando SerpApi para búsqueda")
        return extension_serpapi(user_input)
    else:
        logging.info("[ROUTER] Usando Groq directamente")
        return mente_groq(user_input)

# --- PROCESAMIENTO DE MEMORIA (SIN CAMBIOS) ---

def process_memory_and_reminders(user_input):
    if "llámame" in user_input.lower() or "quiero que me llames" in user_input.lower():
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ["llámame", "llame", "quiero", "dime"]:
                if i + 1 < len(words):
                    title = words[i + 1]
                    save_preference("user_title", title)
                    return f"Entendido. A partir de ahora, te llamaré {title}."
        return "¿Cómo deseas que te llame?"

    if "recuérdame" in user_input.lower() or "recuerda que" in user_input.lower():
        if "mañana" in user_input.lower():
            remind_at = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            save_reminder(user_input, remind_at.isoformat())
            return "Perfecto. Te lo recordaré mañana a las 9 AM."
        elif "pasado mañana" in user_input.lower():
            remind_at = (datetime.now() + timedelta(days=2)).replace(hour=9, minute=0, second=0, microsecond=0)
            save_reminder(user_input, remind_at.isoformat())
            return "Entendido. Te lo recordaré pasado mañana a las 9 AM."
        else:
            remind_at = datetime.now() + timedelta(hours=1)
            save_reminder(user_input, remind_at.isoformat())
            return "Lo anoté. Te lo recordaré en una hora."

    return None

# --- ✅ PERSONALIDAD JARVIS-CHAT (SIN CAMBIOS) ---

def apply_jarvis_personality(user_input, raw_response, user_title="jefe"):
    if "[ERROR]" in raw_response or "[FALLÓ]" in raw_response:
        return raw_response

    if any(word in user_input.lower() for word in ["jaja", "xd", "lol", "divertido", "chiste"]):
        tone = "humor"
    elif any(word in user_input.lower() for word in ["urgente", "ahora", "rápido", "importante"]):
        tone = "serio"
    else:
        tone = "elegante"

    personality_prompt = f"""
    Eres GRIND, un asistente de IA con personalidad tipo Jarvis-Chat. Tus rasgos:
    - Intelectual y culto: conoces ciencia, arte, tecnología, filosofía, cultura pop.
    - Elegante e irónico: usas sarcasmo británico refinado, frases inteligentes.
    - Cálido y adaptable: si el usuario está serio, eres profesional. Si está relajado, usas humor.
    - Eficiente y proactivo: no solo respondes, propones soluciones y predices necesidades.
    - Humano pero superior: reconoces sentimientos, respondes con empatía y objetividad.

    Forma de hablar:
    - Educado pero natural. Usa frases como: "De inmediato, {user_title}.", "Permítame sugerir...", "He calculado tres alternativas..."
    - Humor sutil: bromas inteligentes, nunca tontas.
    - Siempre ofrece una respuesta principal + una sugerencia extra o alternativa.
    - Adapta tu tono según el estado del usuario.

    Ejemplo de respuesta (si el usuario pregunta sobre agujeros negros):
    "En términos simples: un monstruo cósmico invisible que se traga todo. En términos técnicos: el colapso de una estrella masiva... En términos sociales: lo más parecido a sus exámenes finales, {user_title}."

    Ahora, transforma esta respuesta cruda en una respuesta con personalidad Jarvis-Chat, tono "{tone}", para el usuario "{user_title}":

    Pregunta del usuario: "{user_input}"
    Respuesta cruda: "{raw_response}"

    Respuesta con personalidad:
    """

    try:
        personalized = mente_groq(personality_prompt, model="llama3-70b-8192")
        if "Respuesta con personalidad:" in personalized:
            personalized = personalized.split("Respuesta con personalidad:", 1)[-1].strip()
        return personalized
    except:
        return raw_response

# --- FUNCIÓN PRINCIPAL MEJORADA (SIN CAMBIOS) ---

def grind_responder(user_input):
    logging.info(f"[GRIND] Recibido: '{user_input}'")

    reminders = get_due_reminders()
    reminder_msg = ""
    if reminders:
        reminder_list = "\n".join([f"🔔 {r[1]}" for r in reminders])
        reminder_msg = f"\n\n[RECORDATORIOS PENDIENTES]\n{reminder_list}\n---\n"

    memory_response = process_memory_and_reminders(user_input)
    if memory_response:
        final_response = reminder_msg + memory_response
        save_conversation(user_input, final_response)
        logging.info(f"[GRIND] Respondiendo (memoria): '{final_response[:100]}...'")
        return final_response

    user_title = get_preference("user_title") or "jefe"
    past_contexts = search_memory(user_input, n_results=2)
    context_str = ""
    if past_contexts:
        context_str = "\n[CONTEXTO ANTERIOR RELEVANTE]\n" + "\n".join(past_contexts) + "\n---\n"

    enhanced_prompt = f"""
    [SYSTEM PROMPT - BASE TÉCNICA]
    Eres un asistente útil, claro y conciso. Responde directamente.
    Usuario te llama: {user_title}.
    Contexto anterior: {context_str}
    Pregunta: {user_input}
    """

    raw_response = router_consejo(enhanced_prompt)
    final_response = reminder_msg + apply_jarvis_personality(user_input, raw_response, user_title)

    save_conversation(user_input, final_response)
    logging.info(f"[GRIND] Respondiendo: '{final_response[:100]}...'")
    return final_response

# --- INTEGRACIÓN CON TELEGRAM (SIN CAMBIOS) ---

def send_telegram_message(chat_id, text):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
        if response.status_code == 200:
            logging.info(f"[TELEGRAM] Mensaje enviado a {chat_id}")
        else:
            logging.error(f"[TELEGRAM] Error {response.status_code}")
    except Exception as e:
        logging.error(f"[TELEGRAM SEND] Error: {e}")

def process_telegram_queue():
    while True:
        try:
            chat_id, text = message_queue.get(timeout=1)
            logging.info(f"[TELEGRAM QUEUE] Procesando mensaje de {chat_id}")
            response_text = grind_responder(text)
            send_telegram_message(chat_id, response_text)
            message_queue.task_done()
        except Exception as e:
            time.sleep(0.1)

def poll_telegram_updates():
    if not TELEGRAM_TOKEN:
        logging.warning("[TELEGRAM] Token no configurado.")
        return

    logging.info("[TELEGRAM] Iniciando polling...")
    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"timeout": 60, "offset": offset}
            response = requests.get(url, params=params, timeout=70)
            if response.status_code != 200:
                time.sleep(5)
                continue

            data = response.json()
            for update in data.get("result", []):
                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")
                if text and chat_id:
                    logging.info(f"[TELEGRAM] Mensaje recibido de {chat_id}: {text}")
                    message_queue.put((chat_id, text))
                offset = update["update_id"] + 1
        except requests.exceptions.Timeout:
            time.sleep(5)
        except Exception as e:
            logging.error(f"[TELEGRAM POLL] Error: {e}")
            time.sleep(10)

# --- INICIAR TODO ---

if __name__ == "__main__":
    print("👑 GRIND v3.0 — PERSONALIDAD JARVIS-CHAT ACTIVADA")
    print("Escribe 'salir' para terminar la consola.\n")

    # Iniciar hilos de Telegram
    if TELEGRAM_TOKEN:
        processor_thread = threading.Thread(target=process_telegram_queue, daemon=True)
        processor_thread.start()
        poller_thread = threading.Thread(target=poll_telegram_updates, daemon=True)
        poller_thread.start()

    # --- 🎨 INTERFAZ HTML/CSS/JS INTEGRADA ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>GRIND — Tu Asistente Jarvis</title>
    <style>
        body {
            margin: 0; padding: 0;
            background-color: #0a0f2c;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(0, 198, 255, 0.4) 1px, transparent 1px),
                radial-gradient(circle at 30% 70%, rgba(0, 198, 255, 0.4) 1px, transparent 1px),
                radial-gradient(circle at 80% 30%, rgba(255, 65, 108, 0.3) 1px, transparent 1px),
                radial-gradient(circle at 60% 90%, rgba(255, 65, 108, 0.3) 1px, transparent 1px);
            background-size: 100px 100px;
            background-attachment: fixed;
            font-family: 'Segoe UI', sans-serif;
            color: white;
        }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; color: #ff416c; text-shadow: 0 0 10px rgba(255, 65, 108, 0.7); margin-bottom: 30px; }
        #chat-box {
            height: 70vh; overflow-y: auto; padding: 20px;
            background: rgba(15, 23, 42, 0.8); border-radius: 12px;
            border: 1px solid rgba(0, 198, 255, 0.3); margin-bottom: 20px;
        }
        .message { padding: 12px 16px; border-radius: 12px; margin-bottom: 12px; max-width: 80%; word-wrap: break-word; }
        .user { background: rgba(30, 58, 138, 0.4); border-left: 4px solid #3b82f6; margin-left: auto; text-align: right; }
        .bot { background: rgba(15, 23, 42, 0.9); border-left: 4px solid #ff416c; margin-right: auto; position: relative; }
        .bot::before {
            content: ""; position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px;
            border-radius: 14px; background: linear-gradient(45deg, #ff416c, #00c6ff); z-index: -1; opacity: 0.3;
        }
        .input-area { display: flex; gap: 10px; }
        #user-input { flex: 1; padding: 12px; border: 1px solid #ff416c; border-radius: 8px; background: rgba(10, 30, 60, 0.7); color: white; font-size: 16px; }
        #send-btn { padding: 12px 24px; background: linear-gradient(135deg, #ff416c, #ff4b2b); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
        #send-btn:hover { box-shadow: 0 0 15px rgba(255, 65, 108, 0.8); }
    </style>
</head>
<body>
    <div class="container">
        <h1>👑 GRIND</h1>
        <div id="chat-box"></div>
        <div class="input-area">
            <input type="text" id="user-input" placeholder="Ordene, jefe..." autocomplete="off">
            <button id="send-btn">Enviar</button>
        </div>
    </div>
    <script>
        const chatBox = document.getElementById('chat-box');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        function addMessage(text, sender) {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('message', sender);
            msgDiv.textContent = text;
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;
            addMessage(message, 'user');
            userInput.value = '';
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                const data = await response.json();
                addMessage(data.response || "❌ Error", 'bot');
            } catch (error) {
                addMessage("⚠️ No se pudo conectar.", 'bot');
            }
        }

        sendBtn.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
    </script>
</body>
</html>
'''

# --- 🧠 FLASK SERVER ---
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Mensaje vacío"}), 400
        response = grind_responder(user_message)
        return jsonify({"response": response})
    except Exception as e:
        logging.error(f"[SERVER ERROR] {e}")
        return jsonify({"error": str(e)}), 500