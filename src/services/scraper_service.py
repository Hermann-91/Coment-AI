import requests
from bs4 import BeautifulSoup
from src.utils.logger import setup_logger

logger = setup_logger("ScraperService")

class ScraperService:
    """
    Serviço encarregado de extrair e limpar o conteúdo textual de sites de produtos.
    """
    @staticmethod
    def scrape_website(url: str) -> str:
        """
        Acessa uma URL, extrai o texto visível da página e elimina scripts, estilos e menus.
        """
        if not url:
            return ""

        try:
            logger.info(f"Iniciando varredura no site: {url}")
            
            # Simulando cabeçalho de navegador comum para evitar bloqueios de scraping simples
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove tags irrelevantes que não contêm o conteúdo textual essencial
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                tag.decompose()

            # Extrai o texto restante
            raw_text = soup.get_text(separator=" ")
            
            # Remove quebras de linha duplicadas e espaços em branco desnecessários
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            cleaned_text = " ".join(lines)

            # Limita o tamanho do texto para economizar tokens na chamada do Gemini
            limite_caracteres = 6000
            if len(cleaned_text) > limite_caracteres:
                logger.warning(f"Texto do site longo ({len(cleaned_text)} caracteres). Limitado a {limite_caracteres}.")
                cleaned_text = cleaned_text[:limite_caracteres]

            logger.info("Varredura e extração de texto concluídas com sucesso.")
            return cleaned_text

        except Exception as e:
            logger.error(f"Erro ao tentar acessar ou analisar o site {url}: {e}")
            return ""
