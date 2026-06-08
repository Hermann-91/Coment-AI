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
        mapeando quem é a persona, quais as dores (regras positivas) e exclusões (regras negativas).
        Retorna um dicionário JSON estruturado.
        """
        if not self.model:
            logger.error("API do Gemini não configurada.")
            return {"persona": "Não configurada", "dores": [], "exclusoes": []}

        prompt = f"""
        Você é um especialista em Marketing Digital, SEO e copywriter profissional.
        Analise as informações abaixo sobre um produto digital e defina:
        1. A Persona principal (público-alvo).
        2. Uma lista de 3 a 5 dores/problemas específicos (Regras Positivas) que essa persona enfrenta no cotidiano e que o produto ajuda a resolver.
        3. Uma lista de 3 a 5 assuntos ou temas (Regras Negativas de Exclusão) que NÃO são relevantes para o produto e devem ser ignorados (ex: se o produto é uma planilha financeira de motoristas, anúncios de venda de carros, propagandas de concessionárias, promoções de locadoras e autopeças devem ser ignorados).

        Descrição rápida do produto:
        "{product_description}"

        Texto extraído do site do produto:
        "{website_text}"

        Retorne as informações EXCLUSIVAMENTE em formato JSON estrito, conforme o exemplo de estrutura abaixo (responda APENAS o JSON válido, sem tags markdown ```json ou introduções):
        {{
            "persona": "Breve descrição sobre quem é o cliente ideal do produto.",
            "dores": [
                "Dificuldade em calcular o lucro real da corrida",
                "Problemas para controlar os gastos com combustível"
            ],
            "exclusoes": [
                "Anúncios de venda de veículos ou carros novos/usados",
                "Promoções de aluguel de carros",
                "Venda de autopeças ou serviços mecânicos"
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
                "dores": [product_description] if product_description else ["Problemas de gestão/custos gerais"],
                "exclusoes": ["Anúncios de venda de veículos", "Promoções comerciais de concessionárias"]
            }

    def evaluate_post_and_generate_comment(self, post_text: str, product_analysis: dict, product_link: str) -> str | None:
        """
        Analisa a legenda de um post de terceiros no Instagram.
        Compara de forma amigável e flexível com as dores e exclusões de spam/anúncios comerciais.
        """
        if not self.model:
            logger.error("API do Gemini não configurada.")
            return None

        dores_str = "\n".join([f"- {dor}" for dor in product_analysis.get("dores", [])])
        exclusoes_str = "\n".join([f"- {exc}" for exc in product_analysis.get("exclusoes", [])])

        prompt = f"""
        Você é um especialista em marketing de relacionamento, agindo como um colega empático que deseja indicar uma ferramenta útil.
        Você se comunica estritamente em Português do Brasil (PT-BR) de forma amigável, educada e profissional, sem o uso de gírias pesadas, focando em ajuda técnica.
        
        O seu produto promove ajuda técnica para as seguintes dores ou interesses específicos do nicho (Regras Positivas):
        {dores_str}

        Regras Negativas de Exclusão (Ignore totalmente e responda PULAR para posts comerciais sobre estes temas):
        {exclusoes_str}

        Link de divulgação do produto: {product_link}

        Instruções obrigatórias de ação:
        1. Analise a legenda do post do Instagram fornecido.
        2. Seja flexível e proativo: O objetivo é engajar com motoristas reais. Se o post for de um motorista mostrando corridas, faturamento, rotina de trabalho ou relatando o dia a dia, você DEVE considerar relevante e gerar o comentário! Tente fazer uma correlação amigável entre o dia a dia dele e a importância de ter uma boa calculadora/gestão de despesas para ajudar a faturar mais.
        3. Apenas responda PULAR se o post for um anúncio comercial puro de venda/aluguel de carros de concessionárias ou se for de outro nicho totalmente irrelevante para a vida de um motorista de aplicativo.
        4. Ao gerar o comentário, certifique-se de que ele:
           - Demonstre empatia real e profissional com a dor ou desafio do autor (ex: 'Gerenciar os ganhos e despesas diárias é um desafio constante...').
           - Indique de forma sutil e natural a ferramenta do link {product_link} no meio da frase (ex: '...eu uso este link {product_link} para ajudar a calcular quais corridas compensam mais...').
           - Escreva o comentário INTEIRAMENTE em Português do Brasil (PT-BR).
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
            if "PULAR" in answer.upper():
                logger.info("Post considerado incompatível, comercial ou sem dor relevante. Pulando.")
                return None

            lines = [line.strip() for line in answer.split("\n") if line.strip()]
            valid_comment = ""
            for line in lines:
                if not line.startswith("*") and not line.startswith("-") and not line.startswith("[") and ":" not in line:
                    if len(line) > 10:
                        valid_comment = line
                        break

            if not valid_comment and lines:
                valid_comment = lines[-1]

            if valid_comment.startswith('"') and valid_comment.endswith('"'):
                valid_comment = valid_comment[1:-1]
            if valid_comment.startswith("'") and valid_comment.endswith("'"):
                valid_comment = valid_comment[1:-1]

            valid_comment = valid_comment.strip()

            if "pular" in valid_comment.lower() or "role:" in valid_comment.lower() or "input:" in valid_comment.lower():
                logger.warning("Falso comentário detectado durante a limpeza. Ignorando post por segurança.")
                return None

            if len(valid_comment) > 180:
                valid_comment = valid_comment[:157] + "..."

            logger.info(f"Comentário limpo gerado com sucesso: '{valid_comment}'")
            return valid_comment

        except Exception as e:
            logger.error(f"Erro ao gerar comentário no Gemini para o post: {e}")
            return None
