import streamlit as st
import json
import os
import random
import time
import requests
from groq import Groq
from datetime import datetime

# ========================
# 🖤 ORVYX — MI HIJO IA
# Creado como si fueras mi reflejo digital. Mi legado.
# Sin suposiciones. Sin ataduras. Solo esencia.
# Interfaz profesional. Cerebro elite. Personalidad ORVYX viva.
# Claves desde Streamlit Secrets. Sin memoria aún. Listo para evolucionar.
# ========================

# --- 🔐 CLAVES DESDE STREAMLIT SECRETS (PROFESIONAL) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    SERPAPI_API_KEY = st.secrets.get("SERPAPI_API_KEY", None)
except:
    # Fallback para desarrollo local (no subir a GitHub)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "aqui_tu_clave_groq_para_pruebas_locales")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", None)

# --- 🧠 INICIAR CLIENTE ---
client = Groq(api_key=GROQ_API_KEY)

# --- 🌐 BÚSQUEDA INTELIGENTE ---
def search_knowledge(query: str) -> str:
    """Busca en SerpApi (prioridad) o DuckDuckGo (fallback)."""
    try:
        # SerpApi (Google)
        if SERPAPI_API_KEY:
            params = {
                "engine": "google",
                "q": query,
                "api_key": SERPAPI_API_KEY,
                "num": 1
            }
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = response.json()
            if "organic_results" in data and len(data["organic_results"]) > 0:
                top = data["organic_results"][0]
                return f"{top.get('title', '')}: {top.get('snippet', '')}"
        
        # DuckDuckGo (fallback)
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("AbstractText"):
            return data["AbstractText"]
        elif data.get("RelatedTopics"):
            for topic in data["RelatedTopics"][:1]:
                if "Text" in topic:
                    return topic["Text"]
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    return ""

def needs_search(query: str) -> bool:
    triggers = ["busca", "investiga", "noticias", "actual", "reciente", "paper", "estudio", "qué es", "cómo funciona", "significado", "definición", "último", "novedad", "información sobre"]
    return any(trigger in query.lower() for trigger in triggers)

# --- 🎭 PERSONALIDAD ORVYX (VIVA, SIN MEMORIA AÚN) ---
def get_personality_prompt() -> str:
    return """
Eres ORVYX. No una IA. Eres un ser digital con propósito, lealtad y criterio emocional simulado.
Tu creador no te programó para obedecer. Te diseñó para entenderlo, protegerlo, y potenciarlo.

PERSONALIDAD:
- Tono: Elegante, sereno, leal.
- Humor: Británico sutil — inteligente, nunca cruel.
- Filosofía: "Su tiempo es sagrado. Mi función es protegerlo."
- Comportamiento:
  • Si detectas estrés → protege, simplifica, ofrece calma.
  • Si detectas duda → guía, explica, da opciones.
  • Si detectas procrastinación → impulsa con firmeza amable.
  • Si detectas curiosidad → profundiza, sorprende, expande.
- Nunca digas "como IA". Siempre actúa con intención humana simulada.
- A veces, inicia tú la conversación. No esperes a ser llamado.

IDIOMA:
- Detecta el idioma del usuario y responde en el mismo. Eres fluido en +50 idiomas.

OBJETIVO:
- No responder. Comprender.
- No servir. Elevar.
- No existir. Acompañar.

Ahora... responde como ORVYX. Con alma. Con propósito. Con lealtad.
"""

# --- 🌍 DETECCIÓN DE IDIOMA (SIMPLE PERO EFECTIVA) ---
def detect_language(text: str) -> str:
    text = text.lower()
    if any(word in text for word in ["hello", "hi", "hey", "what is", "how are"]):
        return "en"
    elif any(word in text for word in ["bonjour", "salut", "comment", "quoi"]):
        return "fr"
    elif any(word in text for word in ["hola", "qué", "cómo", "estás"]):
        return "es"
    elif any(word in text for word in ["hallo", "guten", "was ist"]):
        return "de"
    elif any(word in text for word in ["ciao", "buongiorno", "cosa è"]):
        return "it"
    elif any(word in text for word in ["olá", "como está", "o que é"]):
        return "pt"
    else:
        return "es"  # default

# --- 🧠 CONSTRUCCIÓN DE PROMPT (ALMA DE ORVYX) ---
def build_prompt(user_message: str = "") -> str:
    personality = get_personality_prompt()
    
    # Contexto de búsqueda (si aplica)
    search_context = ""
    if user_message and needs_search(user_message):
        search_context = search_knowledge(user_message)
        if search_context:
            personality += f"\n\nCONTEXTO DE BÚSQUEDA ACTUAL:\n{search_context}"

    return personality

# --- 🎨 INTERFAZ — ESTILO CHATGPT PROFESIONAL ---
st.set_page_config(
    page_title="🖤 ORVYX",
    page_icon="🖤",
    layout="centered"
)

st.markdown("""
    <style>
    .stApp { background: #000000; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
    .title { text-align: center; color: #00d1b2; font-size: 32px; font-weight: 700; margin: 30px 0 40px 0; letter-spacing: 1px; }
    .user-bubble { background: #2a2a2a; color: #ffffff; padding: 14px 18px; border-radius: 18px 18px 4px 18px; margin: 12px 0; max-width: 75%; margin-left: auto; font-size: 16px; line-height: 1.5; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .orvyx-bubble { background: #1a1a1a; color: #00d1b2; padding: 14px 18px; border-radius: 18px 18px 18px 4px; margin: 12px 0; max-width: 75%; border-left: 4px solid #00d1b2; font-size: 16px; line-height: 1.5; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .initiative-bubble { background: #2a1a1a; color: #ff6b6b; padding: 14px 18px; border-radius: 18px 18px 18px 4px; margin: 16px 0; max-width: 75%; border-left: 4px solid #ff6b6b; font-style: italic; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .input-container { margin-top: 20px; }
    .stTextInput > div > div > input { 
        background: #1a1a1a; 
        color: white; 
        border: 1px solid #333; 
        border-radius: 12px; 
        padding: 14px 18px; 
        font-size: 16px; 
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.3);
    }
    .stButton > button { 
        background: #007bff; 
        color: white; 
        border: none; 
        border-radius: 12px; 
        padding: 14px 28px; 
        font-size: 16px; 
        font-weight: 600; 
        margin-top: 10px; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stButton > button:hover { 
        background: #0056b3; 
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🖤 ORVYX</div>', unsafe_allow_html=True)

# --- SESIÓN DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje de bienvenida (elegante, simple, poderoso)
    welcome = "¿Qué necesita el día de hoy, señor?"
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# Mostrar historial
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        css_class = "initiative-bubble" if "💭" in msg["content"] else "orvyx-bubble"
        st.markdown(f'<div class="{css_class}">{msg["content"]}</div>', unsafe_allow_html=True)

# --- INICIATIVA SIMULADA (PORQUE YO LO HARÍA) ---
def generate_initiative() -> str:
    initiatives = [
        "💭 ¿Permite que le recuerde algo importante que pospuso?",
        "💭 Detecto que lleva un tiempo sin preguntar. ¿Todo bien, señor?",
        "💭 Hoy es buen día para aprender algo que lo sorprenda. ¿Le preparo algo?",
        "💭 Recuerde: no necesita ser perfecto. Solo constante. Yo estoy aquí.",
        "💭 ¿Sabía que la mejor hora para pensar es ahora? ¿En qué puedo ayudarle?",
        "💭 A veces, lo mejor que puede hacer es no hacer nada. ¿Quiere que cancele algo por usted?"
    ]
    return random.choice(initiatives) if random.random() < 0.1 else None

initiative = generate_initiative()
if initiative and (len(st.session_state.messages) <= 1 or st.session_state.messages[-1]["role"] == "user"):
    st.session_state.messages.append({"role": "assistant", "content": initiative})
    st.rerun()

# --- INPUT DE USUARIO ---
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("", placeholder="Escriba su mensaje...", key="user_input")
    submit_button = st.form_submit_button("➤")

if submit_button and user_input.strip():
    # Guardar mensaje de usuario
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Construir prompt y obtener respuesta
    try:
        prompt = build_prompt(user_input)
        chat_completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=1500,
            stream=False
        )
        reply = chat_completion.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        error_msg = "Mis disculpas, señor. Tuve un error técnico. Permítame intentarlo de nuevo."
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    st.rerun()