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
        Se identificar uma dor relacionada às dores mapeadas do produto, gera um comentário em Português do Brasil.
        Se não identificar dor relevante, retorna None para instruir o robô a ignorar o post.
        """
        if not self.model:
            logger.error("API do Gemini não configurada.")
            return None

        dores_str = "\n".join([f"- {dor}" for dor in product_analysis.get("dores", [])])

        prompt = f"""
        Você é um especialista em marketing de relacionamento, agindo como um motorista colega empático que deseja indicar uma ferramenta útil.
        Você se comunica estritamente em Português do Brasil (PT-BR) de forma amigável, educada e profissional, sem o uso de gírias pesadas, focando em ajuda técnica.
        
        O seu produto promove ajuda técnica para as seguintes dores específicas do nicho:
        {dores_str}

        Link de divulgação do produto: {product_link}

        Instruções obrigatórias de ação:
        1. Analise a legenda do post do Instagram fornecido.
        2. Se o post NÃO abordar ou não estiver relacionado a nenhuma das dores descritas acima (como dificuldades de lucro, controle de custos, despesas de combustível, taxas de aplicativos ou gestão financeira de corridas), responda EXCLUSIVAMENTE com a palavra: PULAR
        3. Se o post estiver relacionado a uma dessas dores, gere um comentário de engajamento no Instagram que:
           - Demonstre empatia real e profissional com a dor ou desafio do autor (ex: 'É realmente um desafio gerenciar os custos diários...').
           - Indique de forma sutil e natural a ferramenta do link {product_link} no meio da frase (ex: '...eu uso este link {product_link} para ajudar a calcular quais corridas compensam mais...').
           - Escreva o comentário INTEIRAMENTE em Português do Brasil (PT-BR), sob qualquer circunstância, mesmo se o post original estiver em outra língua.
           - Regras rígidas de formatação: O comentário deve ter no máximo 160 caracteres, ser escrito em parágrafo único (sem quebras de linha/enters), sem nenhuma hashtag (#) e sem termos de spam corporativo (ex: evite 'compre', 'adquira', 'solução revolucionária', 'link abaixo').

        Texto da Legenda do Instagram:
        "{post_text}"

        Resposta (Apenas o comentário gerado ou a palavra PULAR):
        """

        try:
            logger.info("Analisando legenda de postagem do Instagram...")
            response = self.model.generate_content(prompt)
            answer = response.text.strip()

            # Pós-processamento robusto de segurança:
            # Se a resposta contiver a palavra 'PULAR' em qualquer lugar (independente de explicações ou idioma), pulamos o post
            if "PULAR" in answer.upper():
                logger.info("Post considerado incompatível ou sem dor relevante (sinalizado PULAR). Pulando.")
                return None

            # Limpa possíveis blocos extras, tópicos markdown ou raciocínios que a IA possa retornar
            lines = [line.strip() for line in answer.split("\n") if line.strip()]
            valid_comment = ""
            
            # Busca a linha que de fato seja o comentário final, descartando metadados de explicações
            for line in lines:
                if not line.startswith("*") and not line.startswith("-") and not line.startswith("[") and ":" not in line:
                    if len(line) > 10:
                        valid_comment = line
                        break

            if not valid_comment and lines:
                valid_comment = lines[-1]

            # Remove aspas se a IA envelopou o comentário
            if valid_comment.startswith('"') and valid_comment.endswith('"'):
                valid_comment = valid_comment[1:-1]
            if valid_comment.startswith("'") and valid_comment.endswith("'"):
                valid_comment = valid_comment[1:-1]

            valid_comment = valid_comment.strip()

            # Se a limpeza falhou e a resposta ainda contiver metadados ou termos de instrução,
            # ou se for a palavra PULAR escondida no texto, cancelamos o comentário por segurança
            if "pular" in valid_comment.lower() or "role:" in valid_comment.lower() or "input:" in valid_comment.lower():
                logger.warning("Falso comentário detectado durante a limpeza. Ignorando post por segurança.")
                return None

            # Corta se exceder o tamanho máximo de segurança
            if len(valid_comment) > 180:
                valid_comment = valid_comment[:157] + "..."

            logger.info(f"Comentário limpo gerado com sucesso: '{valid_comment}'")
            return valid_comment

        except Exception as e:
            logger.error(f"Erro ao gerar comentário no Gemini para o post: {e}")
            return None
