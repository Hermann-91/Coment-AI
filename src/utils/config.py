import os
from dotenv import load_dotenv

# Carrega as chaves salvas no arquivo oculto .env na raiz do projeto
load_dotenv()

class Config:
    """
    Classe estática para centralizar e carregar as configurações do sistema.
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
    
    @classmethod
    def is_valid(cls) -> bool:
        """
        Valida se as configurações mínimas essenciais foram preenchidas.
        """
        return bool(cls.GEMINI_API_KEY)
