from llm.llm_factory import create_gemini_clients, create_groq_clients

class LLMRotator:

    def __init__(self):

        self.gemini = create_gemini_clients()
        self.groq = create_groq_clients()

        self.provider = "gemini"
        self.index = 0