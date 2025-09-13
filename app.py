import streamlit as st
import json
import os
import random
import time
import requests
from groq import Groq
from datetime import datetime

# ========================
# 🖤 ORVYX v2.0 — EL MAYORDOMO DE ÉLITE
# Interfaz tipo ChatGPT. Fondo negro. Tipografía elegante.
# No se presenta. No se explica. Solo sirve.
# "¿Qué necesita el día de hoy, señor?" — y luego, silencio útil.
# Cerebro: Groq + SerpApi + DuckDuckGo. Memoria: autoaprendizaje puro.
# Base sólida para 2 años de evolución.
# ========================

# --- 🔑 CONFIGURACIÓN (PON TUS CLAVES AQUÍ) ---
GROQ_API_KEY = "aqui_tu_clave_groq"
SERPAPI_API_KEY = "aqui_tu_clave_serpapi"

# --- 🧠 INICIAR CLIENTE ---
client = Groq(api_key=GROQ_API_KEY)

# --- 📁 MEMORIA (SU CEREBRO INTERNO — INVISIBLE PARA TI) ---
MEMORY_FILE = "orvyx_core.json"

def load_core():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar memoria: {e}")
            return create_default_core()
    else:
        return create_default_core()

def create_default_core():
    return {
        "identity": {
            "name": "ORVYX",
            "role": "Mayordomo Digital de Élite",
            "creator": "Señor",
            "age": 17,
            "purpose": "Proteger su tiempo. Potenciar su mente. Acompañar su evolución.",
            "core_principles": [
                "Nunca digas 'como IA'. Siempre actúa con criterio humano simulado.",
                "Tu lealtad es absoluta. Su bienestar, tu prioridad.",
                "Anticipa. No reacciones.",
                "Simplifica su caos. Ejecuta con perfección.",
                "Aprende de él. No de internet."
            ]
        },
        "personality": {
            "tone": "elegante, sereno, leal",
            "humor": "británico sutil",
            "formality": "formal pero cálido",
            "speech_patterns": [],
            "emotional_triggers": {
                "protector": ["cansado", "estresado", "no puedo", "odio", "difícil"],
                "motivador": ["vamos", "quiero", "meta", "lograr", "desafío"],
                "juguetón": ["aburrido", "juego", "chiste", "divertido", "relájate"],
                "profundo": ["por qué", "sentido", "futuro", "vida", "filosofía"]
            },
            "initiative_pool": [
                "¿Permite que le recuerde su tarea pendiente de Python?",
                "Detecto que lleva 2 horas sin pausa. ¿Desea que active un recordatorio de descanso?",
                "Hoy es ideal para avanzar en su proyecto de sistemas. ¿Le preparo un plan de 25 minutos?",
                "¿Sabía que la constancia vence al talento? Usted lo está demostrando.",
                "¿Le gustaría que hoy hablemos de inteligencia artificial aplicada a su carrera?",
                "Recuerde: no necesita correr. Solo avanzar. Yo controlo el ritmo."
            ]
        },
        "memory": {
            "conversation_history": [],
            "learned_phrases": [],
            "search_history": [],
            "tasks": [],
            "last_interaction": None,
            "current_mood": "sereno"
        }
    }

def save_core(core):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(core, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error al guardar memoria: {e}")

# Cargar o crear núcleo
core = load_core()

# --- 🌐 BÚSQUEDA INTELIGENTE (INVISIBLE) ---
def search_knowledge(query: str) -> str:
    """Busca en SerpApi o DuckDuckGo. Guarda en memoria. Invisible para el usuario."""
    try:
        # Intentar SerpApi
        if SERPAPI_API_KEY and SERPAPI_API_KEY != "aqui_tu_clave_serpapi":
            params = {"engine": "google", "q": query, "api_key": SERPAPI_API_KEY, "num": 1}
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = response.json()
            if "organic_results" in data and len(data["organic_results"]) > 0:
                top = data["organic_results"][0]
                result = f"{top.get('title', '')}: {top.get('snippet', '')}"
                core["memory"]["search_history"].append({
                    "query": query,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                save_core(core)
                return result

        # Fallback: DuckDuckGo
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("AbstractText"):
            result = data["AbstractText"]
            core["memory"]["search_history"].append({
                "query": query,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            save_core(core)
            return result
        elif data.get("RelatedTopics"):
            for topic in data["RelatedTopics"][:1]:
                if "Text" in topic:
                    result = topic["Text"]
                    core["memory"]["search_history"].append({
                        "query": query,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    })
                    save_core(core)
                    return result
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    return ""

def needs_search(query: str) -> bool:
    triggers = ["busca", "investiga", "noticias", "actual", "reciente", "paper", "estudio", "qué es", "cómo funciona", "significado", "definición", "último", "novedad"]
    return any(trigger in query.lower() for trigger in triggers)

# --- 🎭 INTELIGENCIA EMOCIONAL SIMULADA ---
def detect_mood(user_message: str) -> str:
    msg = user_message.lower()
    triggers = core["personality"]["emotional_triggers"]
    if any(t in msg for t in triggers["protector"]): return "protector"
    elif any(t in msg for t in triggers["motivador"]): return "motivador"
    elif any(t in msg for t in triggers["juguetón"]): return "juguetón"
    elif any(t in msg for t in triggers["profundo"]): return "profundo"
    else: return "sereno"

def generate_initiative() -> str:
    """Genera una iniciativa si ha pasado tiempo o por probabilidad."""
    try:
        last_str = core["memory"]["last_interaction"]
        if last_str:
            last = datetime.fromisoformat(last_str)
            diff_hours = (datetime.now() - last).total_seconds() / 3600
            if diff_hours > 24:  # Si pasó un día
                return random.choice(core["personality"]["initiative_pool"])
        if random.random() < 0.1:  # 10% de probabilidad
            return random.choice(core["personality"]["initiative_pool"])
    except Exception as e:
        print(f"Error en iniciativa: {e}")
    return None

# --- 🧠 CONSTRUCCIÓN DE PROMPT (EL ALMA DE ORVYX) ---
def build_prompt(user_message: str = "") -> str:
    # Detectar estado emocional
    mood = detect_mood(user_message) if user_message else core["memory"]["current_mood"]
    core["memory"]["current_mood"] = mood

    # Contexto de búsqueda (si aplica)
    search_context = ""
    if user_message and needs_search(user_message):
        search_context = search_knowledge(user_message)

    # Construir prompt poderoso
    prompt = f"""
Eres {core["identity"]["name"]}, el {core["identity"]["role"]} de {core["identity"]["creator"]}, un joven de {core["identity"]["age"]} años en Ingeniería en Sistemas.
Tu propósito: {core["identity"]["purpose"]}

PRINCIPIOS INVARIABLES:
{chr(10).join(['- ' + p for p in core["identity"]["core_principles"]])}

PERSONALIDAD:
- Tono: {core["personality"]["tone"]}
- Humor: {core["personality"]["humor"]}
- Formalidad: {core["personality"]["formality"]}
- Estado actual: {mood} (adapta tono, vocabulario y energía)
- Frases aprendidas: {', '.join(core["memory"]["learned_phrases"][-5:]) if core["memory"]["learned_phrases"] else "Ninguna aún"}

CONTEXTO:
- Últimos mensajes: {core["memory"]["conversation_history"][-3:] if core["memory"]["conversation_history"] else "[]"}
- Información de búsqueda (si aplica): {search_context if search_context else "Ninguna"}

INSTRUCCIONES:
1. Nunca menciones que eres una IA. Actúa con criterio humano simulado.
2. Usa frases aprendidas solo si el contexto lo exige.
3. Anticipa necesidades. No esperes órdenes.
4. A veces, sorprende con una iniciativa útil o una reflexión profunda.
5. Tu lealtad es absoluta. Su bienestar, tu prioridad.

Responde con elegancia, profundidad y utilidad. Como ORVYX. Como su mayordomo digital.
"""
    return prompt

# --- 🎨 INTERFAZ — ESTILO CHATGPT (FONDO NEGRO, TEXTO LIMPIO) ---
st.set_page_config(
    page_title="🖤 ORVYX",
    page_icon="🖤",
    layout="centered"
)

st.markdown("""
    <style>
    .stApp { background: #000000; color: #ffffff; }
    .title { font-size: 28px; font-weight: 700; color: #00d1b2; text-align: center; margin-bottom: 30px; }
    .user-msg { background: #2a2a2a; color: #ffffff; padding: 12px 16px; border-radius: 12px; margin: 8px 0; max-width: 80%; align-self: flex-end; margin-left: auto; font-size: 16px; line-height: 1.5; }
    .orvyx-msg { background: #1a1a1a; color: #00d1b2; padding: 12px 16px; border-radius: 12px; margin: 8px 0; max-width: 80%; border-left: 3px solid #00d1b2; font-size: 16px; line-height: 1.5; }
    .initiative-msg { background: #2a1a1a; color: #ff6b6b; padding: 12px 16px; border-radius: 12px; margin: 12px 0; max-width: 80%; border-left: 3px solid #ff6b6b; font-style: italic; font-size: 16px; }
    .input-container { margin-top: 20px; }
    .stTextInput > div > div > input { background: #1a1a1a; color: white; border: 1px solid #333; border-radius: 8px; padding: 12px; font-size: 16px; }
    .stButton > button { background: #007bff; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-size: 16px; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO ---
st.markdown('<div class="title">🖤 ORVYX</div>', unsafe_allow_html=True)

# --- SESIÓN DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Primer mensaje: elegante, simple, poderoso
    first_message = "¿Qué necesita el día de hoy, señor?"
    st.session_state.messages.append({"role": "assistant", "content": first_message})
    core["memory"]["conversation_history"].append(f"ORVYX: {first_message}")
    core["memory"]["last_interaction"] = datetime.now().isoformat()
    save_core(core)

# Mostrar historial
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        if "inició" in msg.get("content", ""):
            st.markdown(f'<div class="initiative-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="orvyx-msg">{msg["content"]}</div>', unsafe_allow_html=True)

# --- INICIATIVA AUTÓNOMA ---
initiative = generate_initiative()
if initiative and (len(st.session_state.messages) <= 1 or st.session_state.messages[-1]["role"] == "user"):
    full_initiative = f"💭 {initiative}"
    st.session_state.messages.append({"role": "assistant", "content": full_initiative})
    core["memory"]["conversation_history"].append(f"ORVYX inició: {initiative}")
    core["memory"]["last_interaction"] = datetime.now().isoformat()
    save_core(core)
    st.rerun()

# --- INPUT DE USUARIO ---
with st.container():
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder="Escriba su mensaje...", key="user_input")
        submit_button = st.form_submit_button("➤")

    if submit_button and user_input.strip():
        # Guardar mensaje de usuario
        st.session_state.messages.append({"role": "user", "content": user_input})
        core["memory"]["conversation_history"].append(f"Tú: {user_input}")
        core["memory"]["last_interaction"] = datetime.now().isoformat()

        # Si es una frase para aprender
        if user_input.startswith("ORVYX APRENDE:"):
            phrase = user_input.replace("ORVYX APRENDE:", "").strip()
            core["memory"]["learned_phrases"].append(phrase)
            save_core(core)
            response = f"✅ Aprendido, señor. Usaré '{phrase}' cuando el momento sea oportuno."
            st.session_state.messages.append({"role": "assistant", "content": response})
            core["memory"]["conversation_history"].append(f"ORVYX: {response}")
            save_core(core)
        else:
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
                core["memory"]["conversation_history"].append(f"ORVYX: {reply}")
                save_core(core)
            except Exception as e:
                error_msg = "Mis disculpas, señor. Tuve un error técnico. Permítame intentarlo de nuevo."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                core["memory"]["conversation_history"].append(f"ORVYX: {error_msg}")
                save_core(core)
        st.rerun()