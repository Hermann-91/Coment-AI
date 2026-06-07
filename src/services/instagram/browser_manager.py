from playwright.async_api import async_playwright, Page
from src.utils.logger import setup_logger

logger = setup_logger("BrowserManager")

class BrowserManager:
    """
    Responsabilidade única: Gerenciar a inicialização, persistência e encerramento
    do navegador e do contexto de navegação com o Playwright.
    """
    def __init__(self, user_data_dir: str = "instagram_profile"):
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.context = None
        self.page = None

    async def start(self, headless: bool = False) -> Page:
        """
        Inicia o navegador persistente e retorna a página ativa principal.
        """
        logger.info("Iniciando navegador com perfil persistente local via Playwright...")
        self.playwright = await async_playwright().start()
        
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=headless,
            viewport={"width": 1280, "height": 720},
            # Argumento para remover a flag de automação e reduzir a detecção pelo Instagram
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.page = await self.context.new_page()
        logger.info("Navegador inicializado e pronto para uso.")
        return self.page

    async def stop(self):
        """
        Fecha as sessões e desliga o motor do Playwright.
        """
        logger.info("Finalizando navegador Playwright...")
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Conexões do navegador encerradas.")
