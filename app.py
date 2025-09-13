import streamlit as st
import os
import time
import requests
import re
from groq import Groq
import google.generativeai as genai

# ========================
# CONFIGURACIÓN DE PÁGINA
# ========================
st.set_page_config(
    page_title="Grind AI",
    page_icon="🧠",
    layout="centered"
)

# Ocultar botones innecesarios de Streamlit
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
# CLAVES API (para uso personal)
# ========================
GROQ_API_KEY = "tu_clave_groq_aqui"
GEMINI_API_KEY = "tu_clave_gemini_aqui"
HF_API_KEY = "tu_clave_hf_aqui"
SERPAPI_KEY = "tu_clave_serpapi_aqui"

# Inicializar clientes
groq_client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# ========================
# ESTILO VISUAL (Interfaz tipo ChatGPT + Jarvis)
# ========================
st.markdown("""
    <style>
    .grind-header {
        font-family: 'Segoe UI', sans-serif;
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(to right, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0;
    }
    .subheader {
        text-align: center;
        color: #888;
        font-size: 14px;
        margin-bottom: 30px;
    }
    .stChatMessage {
        padding: 12px 20px;
        border-radius: 15px;
        margin-bottom: 12px;
        max-width: 85%;
        line-height: 1.5;
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

st.markdown('<h1 class="grind-header">⚡ GRIND</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Tu asistente intelectual. Piensa como ChatGPT. Habla como Jarvis.</p>', unsafe_allow_html=True)

# ========================
# INICIALIZAR SESIÓN CON MEMORIA
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "¡Hola! Soy Grind, tu asistente intelectual personal. Puedo ayudarte a investigar, escribir, programar, aconsejar, buscar información actualizada, y hasta darte mi opinión con estilo. ¿Por dónde empezamos?"
        }
    ]

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ========================
# FUNCIONES INTELIGENTES
# ========================

def needs_web_search(prompt):
    """Detecta si necesita buscar en la web (información actual, noticias, datos cambiantes)"""
    keywords = [
        "qué dice", "noticias de", "actualidad", "reciente", "ahora", "hoy", "último",
        "precio de", "clima en", "resultados de", "estado de", "cómo está", "dónde está",
        "busca", "investiga", "averigua", "google", "consulta"
    ]
    return any(kw in prompt.lower() for kw in keywords)

def is_greeting(prompt):
    greetings = ["hola", "buenos días", "buenas tardes", "buenas noches", "hey", "hi", "alo", "qué tal"]
    return any(greeting in prompt.lower() for greeting in greetings)

def is_goodbye(prompt):
    goodbyes = ["adiós", "chao", "nos vemos", "hasta luego", "bye", "me voy", "cerrar", "terminar"]
    return any(gb in prompt.lower() for gb in goodbyes)

def is_thanks(prompt):
    thanks = ["gracias", "te lo agradezco", "mil gracias", "thanks", "thank you"]
    return any(thx in prompt.lower() for thx in thanks)

def search_web(query):
    """Busca en Google usando SerpAPI y devuelve snippets útiles"""
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 5,
            "gl": "es"  # resultados en español
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        if response.status_code != 200:
            return "No pude acceder a resultados en este momento."

        results = response.json().get("organic_results", [])
        snippets = []
        for r in results[:3]:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            if snippet:
                snippets.append(f"{title}: {snippet}")
        return " | ".join(snippets) if snippets else "No encontré información relevante."
    except Exception as e:
        return f"Error en búsqueda: {str(e)}"

def build_conversation_context():
    """Construye el historial de conversación para enviar a la IA"""
    context = ""
    for msg in st.session_state.messages[-6:]:  # últimos 6 mensajes para contexto
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        context += f"{role}: {msg['content']}\n"
    return context.strip()

def ask_groq(prompt, context="", web_context=""):
    try:
        full_context = f"CONTEXTO DE CONVERSACIÓN:\n{context}\n\n" if context else ""
        if web_context:
            full_context += f"INFORMACIÓN ACTUALIZADA DE BÚSQUEDA:\n{web_context}\n\n"

        system_prompt = (
            "Eres Grind, un asistente intelectual avanzado. Responde como ChatGPT: extenso cuando se pide profundidad, "
            "conciso cuando se pide brevedad. Sé empático, profesional, proactivo. Usa un toque de ingenio tipo Jarvis, "
            "pero sin exagerar. Si no sabes algo, búscalo o sugiere alternativas. Nunca digas 'soy una IA'. "
            "Si detectas despedida, responde cálidamente. Si detectas agradecimiento, responde con cortesía. "
            "Adapta tu tono al usuario. Tu objetivo: ser útil, completo, humano."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_context + "Usuario actual: " + prompt}
        ]

        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",  # más potente para respuestas largas (aún gratis en Groq)
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return None

def ask_gemini(prompt, context="", web_context=""):
    try:
        full_context = f"CONTEXTO DE CONVERSACIÓN:\n{context}\n\n" if context else ""
        if web_context:
            full_context += f"INFORMACIÓN ACTUALIZADA DE BÚSQUEDA:\n{web_context}\n\n"

        system_prompt = (
            "Eres Grind, un asistente intelectual avanzado. Responde como ChatGPT: extenso cuando se pide profundidad, "
            "conciso cuando se pide brevedad. Sé empático, profesional, proactivo. Usa un toque de ingenio tipo Jarvis, "
            "pero sin exagerar. Si no sabes algo, búscalo o sugiere alternativas. Nunca digas 'soy una IA'. "
            "Si detectas despedida, responde cálidamente. Si detectas agradecimiento, responde con cortesía. "
            "Adapta tu tono al usuario. Tu objetivo: ser útil, completo, humano."
        )

        full_prompt = system_prompt + "\n\n" + full_context + "Usuario actual: " + prompt
        response = gemini_model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return None

def ask_huggingface(prompt, context="", web_context=""):
    try:
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}

        system_prompt = (
            "Eres Grind, un asistente intelectual avanzado. Responde como ChatGPT: extenso cuando se pide profundidad, "
            "conciso cuando se pide brevedad. Sé empático, profesional, proactivo. Usa un toque de ingenio tipo Jarvis. "
            "Nunca digas 'soy una IA'. Adapta tu tono. Tu objetivo: ser útil, completo, humano."
        )

        full_prompt = f"<s>[INST] {system_prompt}\n\nCONTEXTO:\n{context}\n\nBÚSQUEDA:\n{web_context}\n\n{prompt} [/INST]"

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 800,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False
            }
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()[0]['generated_text'].strip()
            # Limpiar posibles etiquetas
            result = re.sub(r'\[\/?INST\]', '', result)
            return result.strip()
        else:
            return None
    except Exception as e:
        return None

# ========================
# MOTOR DE RESPUESTA INTELIGENTE
# ========================

def get_grind_response(prompt):
    context = build_conversation_context()
    web_context = ""

    # Detectar intención
    if is_goodbye(prompt):
        return "Fue un placer ayudarte. Aquí estaré cuando me necesites. ¡Hasta pronto, jefe!", "Despedida"
    elif is_thanks(prompt):
        return "¡Para eso estoy! Si necesitas algo más, solo dilo.", "Agradecimiento"
    elif is_greeting(prompt):
        return "¡Saludos! Grind en línea y listo para ayudarte. ¿Qué necesitas hoy?", "Saludo"

    # Si necesita búsqueda web
    if needs_web_search(prompt):
        with st.spinner("🔍 Buscando información actualizada..."):
            web_context = search_web(prompt)
            st.info(f"📌 Información encontrada: {web_context[:250]}...")

    # Orden de modelos (Groq 70B para respuestas largas > Gemini > HF)
    models_in_order = [
        ("Groq (Llama3-70B)", lambda p: ask_groq(p, context, web_context)),
        ("Gemini Flash", lambda p: ask_gemini(p, context, web_context)),
        ("Hugging Face (Mistral)", lambda p: ask_huggingface(p, context, web_context))
    ]

    for model_name, model_fn in models_in_order:
        with st.spinner(f"🧠 {model_name} está procesando tu solicitud..."):
            response = model_fn(prompt)
            if response and len(response) > 10:  # mínimo 10 caracteres para evitar fallos vacíos
                return response, model_name

    return "Lo siento, todos los sistemas están experimentando interferencias. ¿Podrías reformular tu pregunta?", "FALLBACK"

# ========================
# INTERACCIÓN PRINCIPAL
# ========================

if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):

    # Guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Obtener respuesta inteligente
    response, model_used = get_grind_response(prompt)

    # Guardar y mostrar respuesta
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
        st.caption(f"⚙️ Generado por: {model_used}")