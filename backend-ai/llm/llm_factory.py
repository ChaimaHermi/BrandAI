from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from config.settings import GEMINI_KEYS, GROQ_KEYS, LLM_MODEL


def create_gemini_clients():

    clients = []

    for key in GEMINI_KEYS:
        if key:
            clients.append(
                ChatGoogleGenerativeAI(
                    model=LLM_MODEL,
                    google_api_key=key,
                )
            )

    return clients


def create_groq_clients():

    clients = []

    for key in GROQ_KEYS:
        if key:
            clients.append(
                ChatGroq(
                    api_key=key,
                    model="llama-3.3-70b-versatile",
                )
            )

    return clients