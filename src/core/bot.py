import asyncio
import random
from src.services.scraper_service import ScraperService
from src.services.api.gemini import GeminiService
from src.services.instagram.browser_manager import BrowserManager
from src.services.instagram.scraper import InstagramScraper
from src.services.instagram.interactor import InstagramInteractor
from src.utils.logger import setup_logger

logger = setup_logger("MarketingBot")

class MarketingBot:
    """
    Orquestrador central do Robo_marketing.
    Coordenador do fluxo que injeta as páginas nos serviços especialistas em SOLID.
    """
    def __init__(self, gemini_api_key: str = "", instagram_profile_dir: str = "instagram_profile"):
        self.scraper = ScraperService()
        self.gemini = GeminiService(api_key=gemini_api_key)
        self.browser_manager = BrowserManager(user_data_dir=instagram_profile_dir)
        self.is_running = False

    async def run(
        self,
        instagram_user: str,
        instagram_pass: str,
        product_link: str,
        product_description: str,
        niche_tags: list[str],
        limit_per_tag: int = 5,
        log_callback=None
    ):
        def report(message: str, is_error: bool = False):
            if is_error:
                logger.error(message)
            else:
                logger.info(message)
            if log_callback:
                log_callback(message)

        self.is_running = True
        report("🚀 Iniciando a execução do Robo_marketing...")

        try:
            # 1. Scrape do site do produto
            report("1. Analisando site e proposta de valor do produto...")
            website_text = ""
            if product_link:
                website_text = self.scraper.scrape_website(product_link)

            # 2. IA - Persona e dores
            report("2. Mapeando persona e dores do produto com a IA Gemini...")
            product_analysis = self.gemini.analyze_product(product_description, website_text)
            
            report(f" Persona identificada: {product_analysis.get('persona', 'Geral')}")
            for dor in product_analysis.get("dores", []):
                report(f" -> Dor Mapeada: {dor}")

            if not product_analysis.get("dores"):
                report("❌ Nenhuma dor do produto foi mapeada. Encerrando execução.", is_error=True)
                return

            # 3. Inicializa o Navegador
            report("3. Inicializando navegador local...")
            page = await self.browser_manager.start(headless=False)

            # Instancia os submódulos especialistas injetando a página ativa
            ig_scraper = InstagramScraper(page=page)
            ig_interactor = InstagramInteractor(page=page)

            # 4. Login no Instagram
            report("4. Efetuando login no Instagram...")
            logged = await ig_interactor.login(instagram_user, instagram_pass)
            if not logged:
                report("❌ Falha no login do Instagram. Encerrando execução.", is_error=True)
                await self.browser_manager.stop()
                return

            # 5. Varredura de Hashtags
            report("5. Iniciando varredura das hashtags de nicho...")
            for tag in niche_tags:
                if not self.is_running:
                    report("⏹️ Execução interrompida pelo usuário.")
                    break

                tag = tag.strip()
                report(f"🔎 Analisando posts com a hashtag: #{tag}")
                post_urls = await ig_scraper.get_posts_by_hashtag(tag, limit=limit_per_tag)

                for url in post_urls:
                    if not self.is_running:
                        break

                    report(f"Lendo publicação: {url}")
                    caption = await ig_scraper.get_post_caption(url)
                    
                    if not caption:
                        report("⚠️ Não foi possível ler a legenda do post. Pulando...")
                        continue

                    # IA - Avaliação e geração
                    report("Analisando legenda do post com o Gemini...")
                    comment = self.gemini.evaluate_post_and_generate_comment(
                        post_text=caption,
                        product_analysis=product_analysis,
                        product_link=product_link
                    )

                    if comment:
                        report(f"✨ Dor identificada! Comentando no post: '{comment}'")
                        success = await ig_interactor.comment(url, comment)
                        if success:
                            delay = random.uniform(45.0, 90.0)
                            report(f"⏱️ Aguardando {delay:.1f} segundos de intervalo seguro (anti-ban)...")
                            await asyncio.sleep(delay)
                    else:
                        report("Post considerado irrelevante. Pulando...")
                        await asyncio.sleep(random.uniform(5.0, 10.0))

            report("🎉 Execução das tarefas finalizada!")

        except Exception as e:
            report(f"❌ Erro crítico durante a execução do robô: {e}", is_error=True)

        finally:
            self.is_running = False
            await self.browser_manager.stop()

    def stop(self):
        self.is_running = False
        logger.info("Solicitação de parada recebida.")
