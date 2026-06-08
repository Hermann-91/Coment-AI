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
        Usa o modelo para ler a descrição e o site do produto, gerando a Persona,
        5 palavras-chave positivas, 5 hashtags virais e 5 palavras-chave negativas (exclusões).
        """
        if not self.model:
            logger.error("API do Gemini não configurada.")
            return {"persona": "Não configurada", "palavras_chave": [], "hashtags": [], "exclusoes": []}

        prompt = f"""
        Você é um especialista em Marketing Digital, SEO e copywriter profissional.
        Analise as informações abaixo sobre um produto digital e defina:
        1. A Persona principal (público-alvo).
        2. Uma lista de exatamente 5 palavras-chave positivas (Regras Positivas de Relevância) que caracterizam o interesse do público em relação ao produto (ex: "lucros", "combustível", "despesas", "corridas", "faturamento").
        3. Uma lista de exatamente 5 hashtags virais do nicho para busca no Instagram, sem o símbolo # (ex: "motoristaapp", "vidademotorista", "motoristauber").
        4. Uma lista de exatamente 5 palavras-chave negativas (Regras Negativas de Exclusão) de assuntos ou propagandas comerciais indesejadas que devem ser ignoradas (ex: "venda", "seminovos", "aluguel", "repasses", "autopeças").

        Descrição rápida do produto:
        "{product_description}"

        Texto extraído do site do produto:
        "{website_text}"

        Retorne as informações EXCLUSIVAMENTE em formato JSON estrito, conforme o exemplo de estrutura abaixo (responda APENAS o JSON válido, sem tags markdown ```json ou introduções):
        {{
            "persona": "Breve descrição sobre quem é o cliente ideal do produto.",
            "palavras_chave": [
                "lucro", "combustivel", "despesas", "corrida", "faturamento"
            ],
            "hashtags": [
                "motoristaapp", "motoristadeaplicativo", "motoristauber", "vidademotorista", "uberbr"
            ],
            "exclusoes": [
                "venda", "seminovo", "aluguel", "repasse", "autopecas"
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
                "palavras_chave": ["lucro", "combustivel", "despesas", "corrida", "faturamento"],
                "hashtags": ["motoristaapp", "motoristadeaplicativo", "motoristauber", "vidademotorista", "uberbr"],
                "exclusoes": ["venda", "seminovo", "aluguel", "repasse", "autopecas"]
            }

    def evaluate_post_and_generate_comment(self, post_text: str, product_analysis: dict, product_link: str) -> str | None:
        """
        Analisa o texto de um post (legenda e/ou comentários) no Instagram.
        Aplica veto absoluto (100%) para palavras de exclusão e regra semântica de relevância de pelo menos 2 palavras-chave positivas.
        """
        if not self.model:
            logger.error("API do Gemini não configurada.")
            return None

        palavras_chave_str = ", ".join(product_analysis.get("palavras_chave", []))
        exclusoes_str = ", ".join(product_analysis.get("exclusoes", []))

        prompt = f"""
        Você é um especialista em marketing de relacionamento, agindo como um colega empático que deseja indicar uma ferramenta útil.
        Você se comunica estritamente em Português do Brasil (PT-BR) de forma amigável, educada e profissional, sem o uso de gírias pesadas, focando em ajuda técnica.
        
        As 5 palavras-chave positivas do seu nicho são:
        [{palavras_chave_str}]

        As 5 palavras-chave negativas de exclusão (spam/anúncios comerciais a ignorar) são:
        [{exclusoes_str}]

        Link de divulgação do produto: {product_link}

        Instruções obrigatórias de ação para classificação e escrita:
        1. REGRA DE VETO ABSOLUTO (REGRAS NEGATIVAS): Analise o texto fornecido (que contém a legenda e/ou os primeiros comentários do post). Se ele contiver QUALQUER uma das 5 palavras-chave negativas de exclusão descritas acima (ou variações delas, como plural/sinônimos de venda, aluguel, repasse, autopeças ou anúncios comerciais de carros), responda EXCLUSIVAMENTE com a palavra: PULAR
        2. REGRA DE RELEVÂNCIA (REGRAS POSITIVAS): Avalie se o texto aborda ou contém pelo menos 2 das palavras-chave positivas fornecidas (ou variações morfológicas/sinônimos muito próximos de cada uma). Se o texto tratar de assuntos correspondentes a pelo menos 2 dessas palavras-chave positivas, considere-o RELEVANTE. Se não tratar de pelo menos 2 assuntos correspondentes, responda EXCLUSIVAMENTE com a palavra: PULAR
        3. Se o post passar nas regras e for RELEVANTE, gere um comentário de engajamento que:
           - Demonstre empatia real e profissional com a dor ou desafio do autor (ex: 'Gerenciar os ganhos e despesas diárias é um desafio constante...').
           - Indique de forma sutil e natural a ferramenta do link {product_link} no meio da frase (ex: '...eu uso este link {product_link} para ajudar a calcular quais corridas compensam mais...').
           - Escreva o comentário INTEIRAMENTE em Português do Brasil (PT-BR).
           - Regras rígidas de formatação: O comentário deve ter no máximo 160 caracteres, ser escrito em parágrafo único (sem quebras de linha/enters), sem nenhuma hashtag (#) e sem termos de spam corporativo (ex: evite 'compre', 'adquira', 'solução revolucionária', 'link abaixo').

        Texto do Post (Legenda e Comentários):
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
