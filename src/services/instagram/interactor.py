import asyncio
import random
from playwright.async_api import Page
from src.utils.logger import setup_logger

logger = setup_logger("InstagramInteractor")

class InstagramInteractor:
    """
    Responsabilidade única: Executar interações e ações ativas no Instagram (Login e Comentários).
    """
    def __init__(self, page: Page):
        self.page = page

    async def login(self, username: str, password: str) -> bool:
        """
        Preenche os formulários e efetua o login se necessário.
        """
        if not self.page:
            return False

        try:
            await self.page.goto("https://www.instagram.com/accounts/login/", wait_until="load")
            await asyncio.sleep(random.uniform(2.0, 4.0))

            # Verifica se já está logado
            if "login" not in self.page.url:
                logger.info("Sessão existente detectada. Pulando tela de login.")
                return True

            logger.info(f"Efetuando login para o usuário: {username}")
            await self.page.fill('input[name="username"]', username)
            await asyncio.sleep(random.uniform(0.5, 1.2))

            await self.page.fill('input[name="password"]', password)
            await asyncio.sleep(random.uniform(0.5, 1.2))

            await self.page.click('button[type="submit"]')
            await self.page.wait_for_url("https://www.instagram.com/**", timeout=30000)
            
            logger.info("Login realizado com sucesso.")
            return True

        except Exception as e:
            logger.error(f"Erro ao autenticar no Instagram: {e}")
            return False

    async def comment(self, post_url: str, comment_text: str) -> bool:
        """
        Navega ao post, clica na caixa de texto e digita imitando digitação humana.
        """
        if not self.page:
            return False

        try:
            if self.page.url != post_url:
                await self.page.goto(post_url, wait_until="load")
                await asyncio.sleep(random.uniform(2.0, 3.5))

            comment_box = self.page.locator('textarea[placeholder*="Adicione um comentário"]')
            await comment_box.click()
            await asyncio.sleep(random.uniform(0.5, 1.0))

            logger.info("Simulando digitação humana do comentário...")
            for caractere in comment_text:
                await comment_box.type(caractere)
                await asyncio.sleep(random.uniform(0.04, 0.18))

            await asyncio.sleep(random.uniform(0.5, 1.2))
            
            # Clica em Publicar
            await self.page.click('div[role="button"]:has-text("Publicar")')
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            logger.info("Comentário enviado.")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar comentário no post {post_url}: {e}")
            return False
