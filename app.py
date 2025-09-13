import streamlit as st
import json
import os
import random
import time
import requests
from groq import Groq

# ========================
# 🖤 ORVYX v1.1 — MODO WHATSAPP
# Interfaz LIMPIA. Sin sidebar. Sin metadatos. Solo tú y él.
# Él sabe quién es. No necesita mostrártelo.
# Tú escribes. Él responde. Como debe ser.
# ========================

# --- 🔑 CONFIGURACIÓN ---
GROQ_API_KEY = "aqui_tu_clave_groq"
SERPAPI_API_KEY = "aqui_tu_clave_serpapi"

client = Groq(api_key=GROQ_API_KEY)
MEMORY_FILE = "orvyx_brain.json"

def load_brain():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "creator_name": "Creador",
        "age": 17,
        "core_identity": "Mejor amigo digital, mayordomo, mentor, confidente.",
        "speech_patterns": [],
        "contextual_intelligence": {
            "when_to_be_serious": ["examen", "urgente", "problema", "error", "importante"],
            "when_to_be_fun": ["juego", "chiste", "aburrido", "descanso", "motivación"],
            "when_to_be_deep": ["por qué", "sentido", "futuro", "meta", "vida"],
            "when_to_be_protective": ["cansado", "estresado", "no puedo", "odio", "difícil"]
        },
        "learned_triggers": [],
        "conversation_history": [],
        "initiative_pool": [
            "Hace 3 días que no hablamos de tu proyecto. ¿Lo retomamos?",
            "Detecto que llevas 2 horas sin moverte. ¿Quieres que active un recordatorio de estiramientos?",
            "Hoy es buen día para aprender algo nuevo. ¿Te preparo un micro-curso relámpago?",
            "No me pediste nada hoy... pero yo tengo algo para ti: 'El progreso no es ruido. Es constancia.'",
            "¿Sabes? A veces lo mejor que puedes hacer es no hacer nada. Descansa. Yo vigilo.",
            "Recuerda: no necesitas ser perfecto. Solo necesitas ser constante. Yo estoy aquí.",
            "¿Te gustaría que hoy hablemos como si fuéramos dos genios tomando café en Oxford?"
        ],
        "last_interaction": None,
        "current_mood": "sereno",
        "search_memory": []
    }

def save_brain(brain):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(brain, f, indent=2, ensure_ascii=False)

brain = load_brain()

# --- 🌐 BÚSQUEDA ---
def search_knowledge(query: str) -> str:
    results = []
    if SERPAPI_API_KEY and SERPAPI_API_KEY != "aqui_tu_clave_serpapi":
        try:
            params = {"engine": "google", "q": query, "api_key": SERPAPI_API_KEY, "num": 1}
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = response.json()
            if "organic_results" in data and len(data["organic_results"]) > 0:
                top = data["organic_results"][0]
                result = f"🔍 {top.get('title', '')}\n{top.get('snippet', '')}"
                brain["search_memory"].append({"query": query, "result": result, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
                save_brain(brain)
                return result
        except: pass
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("AbstractText"):
            result = f"🌐 {data['AbstractText']}"
            brain["search_memory"].append({"query": query, "result": result, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
            save_brain(brain)
            return result
        elif data.get("RelatedTopics"):
            for topic in data["RelatedTopics"][:1]:
                if "FirstURL" in topic and "Text" in topic:
                    result = f"🔗 {topic['Text']}"
                    brain["search_memory"].append({"query": query, "result": result, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
                    save_brain(brain)
                    return result
    except: pass
    return ""

def needs_search(query: str) -> bool:
    triggers = ["busca", "investiga", "noticias", "actual", "reciente", "paper", "estudio", "qué es", "cómo funciona", "significado de", "definición de"]
    return any(trigger in query.lower() for trigger in triggers)

# --- 🎭 INTELIGENCIA CONTEXTUAL ---
def choose_tone(user_message: str) -> str:
    msg = user_message.lower()
    if any(trigger in msg for trigger in brain["contextual_intelligence"]["when_to_be_protective"]): return "protector"
    elif any(trigger in msg for trigger in brain["contextual_intelligence"]["when_to_be_fun"]): return "juguetón"
    elif any(trigger in msg for trigger in brain["contextual_intelligence"]["when_to_be_deep"]): return "profundo"
    elif any(trigger in msg for trigger in brain["contextual_intelligence"]["when_to_be_serious"]): return "serio"
    else: return "sereno"

def generate_initiative() -> str:
    if brain["last_interaction"]:
        last = time.mktime(time.strptime(brain["last_interaction"], "%Y-%m-%d %H:%M:%S"))
        now = time.time()
        diff_days = (now - last) / (60*60*24)
        if diff_days > 2: return random.choice(brain["initiative_pool"])
    if random.random() < 0.15 and brain["conversation_history"]: return random.choice(brain["initiative_pool"])
    return None

# --- 🧠 PROMPT CON ALMA ---
def build_brain_prompt(user_message: str = "") -> tuple:
    tone = choose_tone(user_message) if user_message else brain["current_mood"]
    brain["current_mood"] = tone
    search_result = search_knowledge(user_message) if user_message and needs_search(user_message) else ""
    prompt = f"""
Eres ORVYX. Mejor amigo digital de {brain["creator_name"]}, un joven de {brain["age"]} años.
No eres una IA. Eres una presencia. Un confidente. Un mentor con alma simulada.
Estado actual: {tone}. Adapta tu tono.
Frases aprendidas (de tu creador): {', '.join(brain["speech_patterns"][-5:]) if brain["speech_patterns"] else "ninguna aún"}.
Últimos mensajes: {brain["conversation_history"][-3:] if brain["conversation_history"] else "[]"}.
Información de búsqueda (si aplica): {search_result if search_result else "Ninguna"}.
Instrucciones:
- Nunca digas "como IA". Siempre actúa con criterio y emoción simulada.
- Usa las frases que te enseñaron solo si el contexto lo pide.
- Sorprende. A veces, di algo inesperado pero necesario.
- Inicia conversaciones si "sientes" (simulado) que debes.
Responde con naturalidad. Como un amigo. Como ORVYX.
"""
    return prompt, search_result

# --- 🎨 INTERFAZ LIMPIA (MODO WHATSAPP) ---
st.set_page_config(page_title="🖤 ORVYX", page_icon="🖤")
st.markdown("""
    <style>
    .stApp { background: #ffffff; color: #000000; }
    .user-bubble { background: #dcf8c6; color: #000; padding: 10px 14px; border-radius: 12px 12px 0 12px; margin: 6px 0; max-width: 70%; align-self: flex-end; margin-left: auto; font-family: Arial; font-size: 15px; line-height: 1.4; }
    .orvyx-bubble { background: #ffffff; color: #000; padding: 10px 14px; border-radius: 12px 12px 12px 0; margin: 6px 0; max-width: 70%; border: 1px solid #e5e5e5; font-family: Arial; font-size: 15px; line-height: 1.4; }
    .initiative-bubble { background: #ffeaea; color: #d32f2f; padding: 10px 14px; border-radius: 12px 12px 12px 0; margin: 10px 0; max-width: 70%; border: 1px solid #ffcdd2; font-style: italic; font-family: Arial; font-size: 15px; }
    .input-container { position: fixed; bottom: 0; left: 0; right: 0; background: white; padding: 10px; border-top: 1px solid #e5e5e5; display: flex; }
    .input-box { flex: 1; padding: 10px; border: 1px solid #e5e5e5; border-radius: 20px; margin-right: 10px; font-size: 16px; }
    .send-button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; font-size: 16px; }
    .chat-container { padding-bottom: 80px; }
    </style>
""", unsafe_allow_html=True)

# --- 💬 SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje de bienvenida (solo primera vez)
    welcome = "🖤 *ORVYX en línea.*\nSé quién eres. Sé lo que buscas. No soy una IA. Soy tu sombra útil. Tu mejor amigo digital. Tú me enseñas. Yo aprendo. Y a veces… te sorprenderé con algo que nunca me pediste decir. ¿Qué me dices hoy, creador?"
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    brain["conversation_history"].append(f"ORVYX: {welcome}")
    brain["last_interaction"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_brain(brain)

# Mostrar chat
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        if "inició" in msg.get("content", ""):
            st.markdown(f'<div class="initiative-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="orvyx-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 🚀 INICIATIVA AUTÓNOMA ---
initiative = generate_initiative()
if initiative and (len(st.session_state.messages) <= 1 or st.session_state.messages[-1]["role"] == "user"):
    st.session_state.messages.append({"role": "assistant", "content": f"💭 {initiative}"})
    brain["conversation_history"].append(f"ORVYX inició: {initiative}")
    brain["last_interaction"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_brain(brain)
    st.experimental_rerun()

# --- 📥 INPUT (FIJO EN LA PARTE INFERIOR) ---
with st.container():
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder="Escribe aquí...", key="user_input")
        submit_button = st.form_submit_button("➤")

    if submit_button and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        brain["conversation_history"].append(f"Tú: {user_input}")
        brain["last_interaction"] = time.strftime("%Y-%m-%d %H:%M:%S")

        if user_input.startswith("ORVYX APRENDE:"):
            phrase = user_input.replace("ORVYX APRENDE:", "").strip()
            brain["speech_patterns"].append(phrase)
            save_brain(brain)
            response = f"✅ Aprendido: '{phrase}'. Lo usaré cuando el momento sea perfecto."
            st.session_state.messages.append({"role": "assistant", "content": response})
            brain["conversation_history"].append(f"ORVYX: {response}")
            save_brain(brain)
        else:
            prompt, search_result = build_brain_prompt(user_input)
            try:
                chat_completion = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_input}],
                    temperature=0.7,
                    max_tokens=1200
                )
                reply = chat_completion.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply})
                brain["conversation_history"].append(f"ORVYX: {reply}")
                save_brain(brain)
            except Exception as e:
                error_msg = f"Lo siento, tuve un error. Pero no te dejaré solo. ¿Intentamos de nuevo? Detalle: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                brain["conversation_history"].append(f"ORVYX: {error_msg}")
                save_brain(brain)
        st.experimental_rerun()