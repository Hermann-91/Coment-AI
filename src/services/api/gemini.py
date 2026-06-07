import google.generativeai as genai
import json
from src.utils.logger import setup_logger
from src.utils.config import Config

logger = setup_logger("GeminiService")

class GeminiService:
    """
    Serviço responsável por conectar-se ao Google Gemini para análise de persona,
    mapeamento de dores e geração de comentários de engajamento direcionados.
    """
    def __init__(self, api_key: str = "", model_name: str = "models/gemma-4-31b-it"):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model_name = model_name
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"API Gemini inicializada com sucesso usando o modelo: {self.model_name}")
        else:
            self.model = None
            logger.warning("Chave de API do Gemini não configurada. Algumas funções de IA estarão indisponíveis.")

    def analyze_product(self, product_description: str, website_text: str) -> dict:
        """
        Usa o modelo para ler a descrição e o texto extraído do site do produto,
        mapeando quem é a persona e quais são as dores que o produto resolve.
        Retorna um dicionário JSON estruturado.
        """
        if not self.model:
            logger.error("API do Gemini não configurada.")
            return {"persona": "Não configurada", "dores": []}

        prompt = f"""
        Você é um especialista em Marketing Digital e copywriter profissional.
        Analise as informações abaixo sobre um produto digital e defina:
        1. A Persona principal (público-alvo).
        2. Uma lista de 3 a 5 dores/problemas específicos que essa persona enfrenta no cotidiano e que o produto ajuda a resolver.

        Descrição rápida do produto:
        "{product_description}"

        Texto extraído do site do produto:
        "{website_text}"

        Retorne as informações EXCLUSIVAMENTE em formato JSON estrito, conforme o exemplo de estrutura abaixo (responda APENAS o JSON válido, sem tags markdown ```json ou introduções):
        {{
            "persona": "Breve descrição sobre quem é o cliente ideal do produto.",
            "dores": [
                "Exemplo de dor 1",
                "Exemplo de dor 2",
                "Exemplo de dor 3"
            ]
        }}
        """

        try:
            logger.info("Enviando dados do produto para análise semântica da IA...")
            response = self.model.generate_content(prompt)
            
            # Limpa possíveis blocos extras de formatação que a IA possa retornar
            content = response.text.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            logger.info("Mapeamento do produto e persona concluído com sucesso.")
            return result

        except Exception as e:
            logger.error(f"Erro ao realizar análise do produto no Gemini: {e}")
            return {
                "persona": "Persona definida por descrição rápida",
                "dores": [product_description] if product_description else ["Problemas de gestão/custos gerais"]
            }

    def evaluate_post_and_generate_comment(self, post_text: str, product_analysis: dict, product_link: str) -> str | None:
        """
        Analisa a legenda de um post de terceiros no Instagram.
        Se identificar uma dor relacionada às dores mapeadas do produto, gera um comentário.
        Se não identificar dor relevante, retorna None para instruir o robô a ignorar o post.
        """
        if not self.model:
            logger.error("API do Gemini não configurada.")
            return None

        dores_str = "\n".join([f"- {dor}" for dor in product_analysis.get("dores", [])])

        prompt = f"""
        Você é um assistente de inteligência de marketing empático e natural.
        O seu produto promove soluções para as seguintes dores específicas:
        {dores_str}

        Link de divulgação do produto: {product_link}

        Instruções:
        1. Analise o post do Instagram abaixo.
        2. Se a pessoa NÃO estiver demonstrando nenhuma das dores acima, responda exatamente com a palavra: PULAR
        3. Se a pessoa estiver demonstrando, reclamando ou falando de algo ligado a uma dessas dores, gere um comentário de Instagram que:
           - Demonstre empatia direta e humana com o problema abordado no post (seja amigável e evite tom corporativo/robótico ou spam óbvio).
           - Aponte brevemente como o produto com o link {product_link} ajuda a resolver exatamente aquela dor apontada por ela.
           - Seja sucinto: limite o comentário a no máximo 250 caracteres.

        Texto do Post do Instagram:
        "{post_text}"

        Resposta (Comentário gerado ou a palavra PULAR):
        """

        try:
            logger.info("Analisando legenda de postagem do Instagram...")
            response = self.model.generate_content(prompt)
            answer = response.text.strip()

            if answer.upper() == "PULAR":
                logger.info("Post considerado incompatível ou sem dor relevante. Pulando.")
                return None

            logger.info("Comentário inteligente gerado com sucesso.")
            return answer

        except Exception as e:
            logger.error(f"Erro ao gerar comentário no Gemini para o post: {e}")
            return None
