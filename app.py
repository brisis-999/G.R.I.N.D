import streamlit as st
import os
import time
import requests
from groq import Groq
import google.generativeai as genai

# ========================
# CONFIGURACIÓN INICIAL
# ========================
st.set_page_config(
    page_title="Grind AI",
    page_icon="🧠",
    layout="centered"
)

# Ocultar decoraciones de Streamlit (modo más limpio)
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
# CLAVES API (para uso personal, puedes ponerlas aquí directo)
# ========================
GROQ_API_KEY = "tu_clave_groq_aqui"          # https://console.groq.com/keys
GEMINI_API_KEY = "tu_clave_gemini_aqui"      # https://aistudio.google.com/app/apikey
HF_API_KEY = "tu_clave_hf_aqui"              # https://huggingface.co/settings/tokens
SERPAPI_KEY = "tu_clave_serpapi_aqui"        # https://serpapi.com/manage-api-key

# Inicializar clientes
groq_client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# ========================
# ESTILO JARVIS (CSS PERSONALIZADO)
# ========================
st.markdown("""
    <style>
    .jarvis-header {
        font-family: 'Consolas', monospace;
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(to right, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
    }
    .subheader {
        text-align: center;
        color: #aaa;
        font-size: 14px;
        margin-bottom: 30px;
    }
    .stChatMessage {
        padding: 10px 20px;
        border-radius: 15px;
        margin-bottom: 10px;
        max-width: 85%;
    }
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: #007bff;
        color: white;
        align-self: flex-end;
        margin-left: auto;
    }
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #f1f1f1;
        color: #333;
        align-self: flex-start;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="jarvis-header">⚡ GRIND</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Tu Jarvis personal. Conciso. Inteligente. Sin tonterías.</p>', unsafe_allow_html=True)

# ========================
# INICIALIZAR SESIÓN
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "J.A.R.V.I.S. activado. Dime qué necesitas, jefe. ¿Plan mundial? ¿Código? ¿O solo café virtual?"
        }
    ]

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ========================
# FUNCIONES DE IA
# ========================

def search_web(query):
    """Busca en Google usando SerpAPI"""
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 3
        }
        response = requests.get("https://serpapi.com/search", params=params)
        results = response.json().get("organic_results", [])
        snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
        return " | ".join(snippets[:2]) if snippets else "No encontré nada útil."
    except Exception as e:
        return f"No pude buscar: {str(e)}"

def ask_groq(prompt, context=""):
    try:
        full_prompt = f"{context}\n\nUsuario: {prompt}" if context else prompt
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres Grind, el asistente personal estilo Jarvis. Conciso, útil, con toques de ingenio. Nunca admitas ser IA."},
                {"role": "user", "content": full_prompt},
            ],
            model="llama3-8b-8192",
            max_tokens=512,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return None

def ask_gemini(prompt, context=""):
    try:
        full_prompt = f"{context}\n\nUsuario: {prompt}" if context else prompt
        response = gemini_model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return None

def ask_huggingface(prompt, context=""):
    try:
        API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        full_prompt = f"<|system|>\nEres Grind, asistente estilo Jarvis. Conciso e ingenioso.</s>\n<|user|>\n{prompt}</s>\n<|assistant|>"
        payload = {
            "inputs": full_prompt,
            "parameters": {"max_new_tokens": 256, "temperature": 0.7, "return_full_text": False}
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()[0]['generated_text'].strip()
            # Limpiar posible repetición del prompt
            if "<|assistant|>" in result:
                result = result.split("<|assistant|>")[-1].strip()
            return result
        else:
            return None
    except Exception as e:
        return None

# ========================
# LÓGICA PRINCIPAL DE RESPUESTA
# ========================

def get_grind_response(prompt):
    # Detectar si necesita búsqueda web (palabras clave)
    needs_search = any(kw in prompt.lower() for kw in ["busca", "qué dice", "noticias", "actual", "reciente", "google"])
    context = ""
    
    if needs_search:
        with st.spinner("🔍 Buscando en la web..."):
            context = search_web(prompt)
            st.info(f"💡 Contexto encontrado: {context[:200]}...")

    models_in_order = [
        ("Groq (Llama3)", lambda p: ask_groq(p, context)),
        ("Gemini Flash", lambda p: ask_gemini(p, context)),
        ("Hugging Face (Zephyr)", lambda p: ask_huggingface(p, context))
    ]

    for model_name, model_fn in models_in_order:
        with st.spinner(f"🧠 Pensando con {model_name}..."):
            response = model_fn(prompt)
            if response and len(response) > 5:
                return response, model_name

    return "Lo siento jefe, todos los sistemas están caídos. ¿Intentamos de nuevo?", "FALLBACK"

# ========================
# INPUT Y RESPUESTA
# ========================

if prompt := st.chat_input("Ordena, jefe..."):

    # Añadir mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Obtener respuesta de Grind
    response, model_used = get_grind_response(prompt)

    # Añadir respuesta del asistente
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
        st.caption(f"⚙️ Respondido por: {model_used}")
