import streamlit as st
import os
import time
import requests
from groq import Groq
import google.generativeai as genai

# ========================
# CONFIGURACIÓN DE PÁGINA — INTERFAZ TIPO CHATGPT + JARVIS
# ========================
st.set_page_config(
    page_title="Grind AI - Tu Mayordomo Digital",
    page_icon="🧠",
    layout="centered"
)

# Ocultar elementos de Streamlit para interfaz limpia
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ========================
# 🔑 CLAVES API — ¡REEMPLÁZALAS POR TUS CLAVES REALES!
# ========================
# ⚠️ OBTÉN TUS CLAVES GRATIS:
# Groq: https://console.groq.com/keys
# Gemini: https://aistudio.google.com/app/apikey
# SerpAPI: https://serpapi.com (plan free: 100 búsquedas/mes)

GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # ← ¡REEMPLAZA ESTO!
GEMINI_API_KEY = "AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxx"  # ← ¡REEMPLAZA ESTO!
SERPAPI_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"     # ← ¡REEMPLAZA ESTO!

# Inicializar clientes
groq_client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# ========================
# 🎨 ESTILOS — INTERFAZ TIPO CHATGPT + JARVIS
# ========================
st.markdown("""
    <style>
    .grind-title {
        font-family: 'Segoe UI', sans-serif;
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(to right, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 15px;
        margin-bottom: 30px;
    }
    .stChatMessage {
        padding: 14px 22px;
        border-radius: 18px;
        margin-bottom: 14px;
        max-width: 85%;
        line-height: 1.6;
        font-size: 16px;
    }
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: #007bff;
        color: white;
        align-self: flex-end;
        margin-left: auto;
    }
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #f8f9fa;
        color: #212529;
        align-self: flex-start;
        border-left: 4px solid #007bff;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="grind-title">⚡ GRIND</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Tu mayordomo digital. Piensa como ChatGPT. Actúa como Jarvis.</p>', unsafe_allow_html=True)

# ========================
# 🧠 INICIALIZAR SESIÓN CON MEMORIA
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Buenas tardes, jefe. Grind, su mayordomo digital, a su servicio. ¿Desea café, información, código, o quizás dominar el mundo hoy?"
        }
    ]

# Mostrar historial de conversación
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ========================
# 🧩 FUNCIONES INTELIGENTES — CEREBRO DE GRIND
# ========================

def is_greeting(text):
    triggers = ["hola", "buenos días", "buenas tardes", "buenas noches", "hey", "hi", "alo", "qué tal", "saludos"]
    return any(trigger in text.lower() for trigger in triggers)

def is_goodbye(text):
    triggers = ["adiós", "chao", "nos vemos", "hasta luego", "bye", "me voy", "cerrar", "terminar", "desconectar"]
    return any(trigger in text.lower() for trigger in triggers)

def is_thanks(text):
    triggers = ["gracias", "te lo agradezco", "mil gracias", "thanks", "thank you", "te agradezco"]
    return any(trigger in text.lower() for trigger in triggers)

def needs_web_search(text):
    triggers = [
        "qué dice", "noticias de", "actualidad", "reciente", "ahora", "hoy", "último",
        "precio de", "clima en", "resultados de", "estado de", "cómo está", "dónde está",
        "busca", "investiga", "averigua", "google", "consulta", "información actual"
    ]
    return any(trigger in text.lower() for trigger in triggers)

def search_web(query):
    """Busca en Google usando SerpAPI y devuelve snippets útiles"""
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 3,
            "gl": "es",
            "hl": "es"
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        if response.status_code != 200:
            return "No pude obtener resultados en este momento."

        results = response.json().get("organic_results", [])
        snippets = []
        for r in results[:2]:
            snippet = r.get("snippet", "")
            if snippet:
                snippets.append(snippet)
        return " ".join(snippets) if snippets else "No encontré información relevante."
    except Exception as e:
        return f"No pude buscar: {str(e)}"

def build_conversation_context():
    """Construye contexto con los últimos 8 mensajes para mantener coherencia"""
    context = ""
    # Tomamos los últimos 8 mensajes (o menos si hay menos)
    recent_messages = st.session_state.messages[-8:] if len(st.session_state.messages) > 1 else st.session_state.messages
    for msg in recent_messages:
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        context += f"{role}: {msg['content']}\n"
    return context.strip()

# ========================
# 🤖 FUNCIONES DE IA — GROQ + GEMINI (FALLBACK)
# ========================

def ask_groq(prompt, context="", web_context=""):
    """Pregunta a Groq con modelo estable llama3-8b-8192"""
    try:
        full_prompt = ""
        if context:
            full_prompt += f"CONTEXTO DE LA CONVERSACIÓN:\n{context}\n\n"
        if web_context:
            full_prompt += f"INFORMACIÓN ACTUALIZADA DE BÚSQUEDA:\n{web_context}\n\n"
        full_prompt += f"USUARIO ACTUAL: {prompt}"

        system_prompt = (
            "Eres Grind, el mayordomo digital personal de un genio moderno. "
            "Responde como lo haría ChatGPT: con profundidad cuando se pide, brevedad cuando se necesita. "
            "Sé útil, proactivo, empático. Usa un toque de ingenio y confianza tipo Jarvis (Tony Stark), pero sin exagerar. "
            "Nunca digas 'soy una IA'. Si detectas despedida, responde con cortesía. Si detectas agradecimiento, responde con calidez. "
            "Si no sabes algo, búscalo o sugiere alternativas. Adapta tu tono al usuario. Tu misión: ser el mejor mayordomo digital del mundo."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]

        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",  # ← ESTE MODELO ES ESTABLE Y RÁPIDO
            max_tokens=1024,
            temperature=0.7,
            top_p=0.95
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"⚠️ Groq falló: {str(e)}")
        return None

def ask_gemini(prompt, context="", web_context=""):
    """Fallback a Gemini si Groq falla"""
    try:
        full_prompt = ""
        if context:
            full_prompt += f"CONTEXTO: {context}\n\n"
        if web_context:
            full_prompt += f"BÚSQUEDA: {web_context}\n\n"
        full_prompt += f"PREGUNTA: {prompt}"

        system_prompt = (
            "Eres Grind, mayordomo digital. Responde como ChatGPT: útil, completo, adaptable. "
            "Tono: profesional con toque de ingenio. Nunca admitas ser IA. "
            "Si es despedida, responde cálidamente. Si es agradecimiento, sé cortés."
        )

        final_prompt = f"{system_prompt}\n\n{full_prompt}"
        response = gemini_model.generate_content(final_prompt)
        return response.text.strip()
    except Exception as e:
        st.warning(f"⚠️ Gemini falló: {str(e)}")
        return None

# ========================
# 🧠 MOTOR DE RESPUESTA — INTELIGENCIA CENTRAL DE GRIND
# ========================

def get_grind_response(prompt):
    """Motor principal de Grind — decide qué hacer según la entrada"""

    # 1. Detectar intenciones básicas (sin llamar a IA)
    if is_goodbye(prompt):
        return "Fue un honor servirle, jefe. Grind queda en modo espera. ¡Hasta nuestra próxima misión!", "Despedida"
    elif is_thanks(prompt):
        return "Siempre a su servicio. ¿Algo más en lo que pueda ayudarle?", "Agradecimiento"
    elif is_greeting(prompt):
        return "¡Saludos, jefe! Grind en línea, café virtual servido, sistemas al 100%. ¿Qué desea hoy?", "Saludo"

    # 2. Construir contexto de conversación
    context = build_conversation_context()
    web_context = ""

    # 3. Si necesita búsqueda web, hacerla
    if needs_web_search(prompt):
        with st.spinner("🔍 Buscando información actualizada..."):
            web_context = search_web(prompt)
            st.info(f"📌 Contexto de búsqueda: {web_context[:200]}...")

    # 4. Probar modelos en orden (Groq primero, luego Gemini)
    models = [
        ("Groq (Llama3-8B)", lambda p: ask_groq(p, context, web_context)),
        ("Gemini Flash", lambda p: ask_gemini(p, context, web_context))
    ]

    for model_name, model_fn in models:
        with st.spinner(f"🧠 {model_name} procesando su solicitud..."):
            response = model_fn(prompt)
            if response and len(response.strip()) > 5:  # Evitar respuestas vacías
                return response, model_name

    # 5. Si todo falla
    return (
        "Mis disculpas, jefe. Los sistemas experimentan interferencias temporales. "
        "¿Podría reformular su pregunta? O espere un momento y lo intentamos de nuevo.",
        "FALLBACK"
    )

# ========================
# 💬 INTERACCIÓN PRINCIPAL — LOOP DE CHAT
# ========================

if prompt := st.chat_input("Ordene, jefe..."):

    # Guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Obtener respuesta inteligente de Grind
    response, model_used = get_grind_response(prompt)

    # Guardar y mostrar respuesta
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
        st.caption(f"⚙️ Respondido por: {model_used}")