# app.py — GRIND v3.0 — STREAMLIT UI — ESTILO CHATGPT + ALMA JARVIS
# Creado por Eliezer Mesac Feliz Luciano
# Sin Flask. Sin HTML manual. Sin errores. 100% Streamlit Cloud compatible.

import os
import json
import sqlite3
import random
import logging
from datetime import datetime, timedelta
import requests
import streamlit as st
from dotenv import load_dotenv

# --- CARGAR VARIABLES ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

if not GROQ_API_KEY:
    st.error("❌ ERROR: GROQ_API_KEY no configurada. Usa Streamlit Secrets.")
    st.stop()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- INICIALIZAR SQLITE Y CHROMADB ---
try:
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path="./grind_memory")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(name="conversations", embedding_function=sentence_transformer_ef)
except Exception as e:
    logging.warning(f"[CHROMA] No disponible: {e}")
    collection = None

conn = sqlite3.connect('grind.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, content TEXT, remind_at DATETIME)''')
conn.commit()

# --- FUNCIONES DE MEMORIA ---
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
    if collection:
        try:
            doc_id = f"conv_{int(time.time())}_{random.randint(1000,9999)}"
            collection.add(
                documents=[user_input + " → " + response],
                metadatas=[{"timestamp": timestamp, "type": "conversation"}],
                ids=[doc_id]
            )
        except Exception as e:
            logging.error(f"[CHROMA] Error: {e}")

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
                    "Name": {"title": [{"text": {"content": f"GRIND - {timestamp[:10]}"}}]},
                    "Content": {"rich_text": [{"text": {"content": f"User: {user_input}\nGRIND: {response}"}}]}
                }
            }
            requests.post(url, json=data, headers=headers, timeout=10)
        except Exception as e:
            logging.error(f"[NOTION] Error: {e}")

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
    if not collection:
        return []
    try:
        results = collection.query(query_texts=[query], n_results=n_results, include=["documents", "metadatas"])
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        logging.error(f"[CHROMA SEARCH] Error: {e}")
        return []

# --- FUNCIONES DE IA ---
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
        return f"[GROQ ERROR {response.status_code}]"
    except Exception as e:
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
                return mente_groq(f"[MISTRAL CARGANDO] {prompt}")
            if isinstance(result, list) and len(result) > 0:
                item = result[0]
                if isinstance(item, dict):
                    return item.get('generated_text', '').strip()
                else:
                    return str(item).strip()
            return str(result).strip()
        return mente_groq(f"[MISTRAL HTTP {response.status_code}] {prompt}")
    except Exception as e:
        return mente_groq(f"[MISTRAL ERROR] {prompt}")

def extension_gemini(prompt):
    if not GEMINI_API_KEY:
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
            return mente_groq(f"[GEMINI SIN RESPUESTA] {prompt}")
        return mente_groq(f"[GEMINI HTTP {response.status_code}] {prompt}")
    except Exception as e:
        return mente_groq(f"[GEMINI ERROR] {prompt}")

def extension_phi3_local(prompt):
    return "[PHI-3 SIMULADO] Respuesta local simulada."

def extension_serpapi(query):
    if not SERPAPI_KEY:
        return "🔍 Búsqueda simulada (SerpApi no configurado)."
    return "🔍 Resultado de búsqueda simulado."

def router_consejo(user_input):
    u = user_input.lower()
    if any(kw in u for kw in ["código", "debug", "python", "lógica"]):
        return extension_mistral(user_input)
    elif any(kw in u for kw in ["redacta", "estilo", "elegante"]):
        return extension_phi3_local(user_input)
    elif any(kw in u for kw in ["rápido", "resumen", "extenso"]):
        return extension_gemini(user_input)
    elif any(kw in u for kw in ["busca", "qué es", "define"]):
        return extension_serpapi(user_input)
    else:
        return mente_groq(user_input)

def process_memory_and_reminders(user_input):
    if "llámame" in user_input.lower():
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ["llámame", "dime"]:
                if i + 1 < len(words):
                    title = words[i + 1]
                    save_preference("user_title", title)
                    return f"Entendido. Te llamaré {title}."
        return "¿Cómo deseas que te llame?"
    if "recuérdame" in user_input.lower():
        remind_at = datetime.now() + timedelta(hours=1)
        save_reminder(user_input, remind_at.isoformat())
        return "Lo anoté. Te lo recordaré en una hora."
    return None

def apply_jarvis_personality(user_input, raw_response, user_title="jefe"):
    if "[ERROR]" in raw_response or "[FALLÓ]" in raw_response:
        return raw_response
    tone = "humor" if any(w in user_input.lower() for w in ["jaja", "lol", "chiste"]) else "serio" if any(w in user_input.lower() for w in ["urgente", "rápido"]) else "elegante"
    prompt = f"Eres GRIND, asistente tipo Jarvis. Tono: {tone}. Usuario: {user_title}. Transforma: '{raw_response}'"
    try:
        return mente_groq(prompt)
    except:
        return raw_response

def grind_responder(user_input):
    logging.info(f"[GRIND] Input: {user_input}")
    reminders = get_due_reminders()
    reminder_msg = "\n\n[🔔 RECORDATORIOS]\n" + "\n".join([r[1] for r in reminders]) + "\n---\n" if reminders else ""
    memory_response = process_memory_and_reminders(user_input)
    if memory_response:
        final_response = reminder_msg + memory_response
        save_conversation(user_input, final_response)
        return final_response
    user_title = get_preference("user_title") or "jefe"
    past_contexts = search_memory(user_input, n_results=2)
    context_str = "\n[CONTEXTO]\n" + "\n".join(past_contexts) + "\n---\n" if past_contexts else ""
    enhanced_prompt = f"Usuario: {user_title}. Contexto: {context_str} Pregunta: {user_input}"
    raw_response = router_consejo(enhanced_prompt)
    final_response = reminder_msg + apply_jarvis_personality(user_input, raw_response, user_title)
    save_conversation(user_input, final_response)
    logging.info(f"[GRIND] Output: {final_response[:100]}...")
    return final_response

# --- 🎨 CSS PERSONALIZADO PARA STREAMLIT ---
CUSTOM_CSS = """
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #141414 !important;
        color: white !important;
    }
    [data-testid="stSidebar"] .css-1v0mbdj, 
    [data-testid="stSidebar"] .css-1v0mbdj a {
        color: white !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #374151 !important;
    }

    /* Main background */
    .stApp {
        background-color: #18181B !important;
    }

    /* Chat messages */
    .user-message {
        background-color: #2D3748 !important;
        color: white !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin: 8px 0 !important;
        text-align: right !important;
        max-width: 80% !important;
        margin-left: auto !important;
    }
    .bot-message {
        background-color: #1A1A1E !important;
        color: white !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin: 8px 0 !important;
        text-align: left !important;
        max-width: 80% !important;
        margin-right: auto !important;
        position: relative;
    }
    .message-actions {
        position: absolute;
        top: 8px;
        right: 8px;
        font-size: 14px;
        color: #9CA3AF;
    }
    .message-actions button {
        background: none;
        border: none;
        color: #9CA3AF;
        cursor: pointer;
        margin-left: 8px;
    }
    .message-actions button:hover {
        color: #3B82F6;
    }

    /* Input area */
    .stTextInput > div > div > input {
        background-color: #2D3748 !important;
        color: white !important;
        border: 1px solid #374151 !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563EB, #7C3AED) !important;
    }

    /* Upgrade button */
    .upgrade-btn {
        background-color: #C4B5FD !important;
        color: #1F2937 !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        border: none !important;
        width: 100% !important;
        cursor: pointer !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #18181B;
    }
    ::-webkit-scrollbar-thumb {
        background: #9CA3AF;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #3B82F6;
    }
</style>
"""

# --- 🚀 APP STREAMLIT ---
def main():
    st.set_page_config(page_title="GRIND — Tu Asistente Jarvis", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown('<div style="color:white; font-size:24px; font-weight:bold;">GRIND 👑</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("➕ Nuevo chat"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("### Menú")
        st.button("🔍 Buscar chats")
        st.button("📚 Biblioteca")
        st.button("🎨 Sora")
        st.button("🤖 GPT")
        st.button("📁 Proyectos", help="NUEVO")

        st.markdown("---")
        st.markdown("### Historial")
        st.button("💬 Chat 1 - Proyecto IA")
        st.button("💬 Chat 2 - Resumen libro")
        st.button("💬 Chat 3 - Código Python")

        st.markdown("---")
        st.markdown("**eliezer**")
        st.markdown("<div style='font-size:12px; color:#9CA3AF;'>Plan: Gratis</div>", unsafe_allow_html=True)
        st.markdown('<button class="upgrade-btn">Mejorar plan</button>', unsafe_allow_html=True)

    # --- MAIN CHAT ---
    st.title("👑 GRIND — Tu Asistente Jarvis")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 ¡Hola, jefe! Soy GRIND, tu asistente personal tipo Jarvis. ¿En qué puedo ayudarte hoy?"}
        ]

    # Mostrar mensajes
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="bot-message">
                    {message["content"]}
                    <div class="message-actions">
                        <button title="Copiar" onclick="navigator.clipboard.writeText(`{message["content"]}`)">📄</button>
                        <button title="Me gusta">👍</button>
                        <button title="No me gusta">👎</button>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

    # Input
    if prompt := st.chat_input("Pregunta lo que quieras..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("🧠 Generando respuesta..."):
            response = grind_responder(prompt)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    main()