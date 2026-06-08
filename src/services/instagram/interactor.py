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

    async def login(self, username: str = "") -> bool:
        """
        Acessa o Instagram e aguarda que o usuário faça o login manualmente caso
        não exista uma sessão ativa. Retorna True assim que o login for detectado.
        """
        if not self.page:
            return False

        try:
            logger.info("Acessando o Instagram...")
            await self.page.goto("https://www.instagram.com/", wait_until="load")
            await asyncio.sleep(3.0)

            # Verifica se já está logado pela presença de elementos comuns do feed ou navegação
            is_logged = "login" not in self.page.url and (
                await self.page.locator('svg[aria-label="Feed de atividades"], svg[aria-label="Página inicial"], svg[aria-label="Direct"]').count() > 0
            )

            if is_logged:
                logger.info("Sessão ativa detectada! Iniciando fluxo de automação direta.")
                return True

            logger.info("⚠️ Login não detectado. Por favor, efetue o login MANUALMENTE na janela do navegador aberta.")
            logger.info("O robô aguardará você realizar o login e resolver qualquer CAPTCHA para assumir o controle.")

            # Loop de monitoramento de login manual (timeout de 5 minutos)
            timeout = 300  # 5 minutos
            interval = 2.0
            elapsed = 0.0

            while elapsed < timeout:
                if self.page.is_closed():
                    logger.error("A janela do navegador foi fechada antes de efetuar o login.")
                    return False

                # Verifica se a URL atual mudou e se os elementos da conta logada apareceram
                is_logged_now = "login" not in self.page.url and (
                    await self.page.locator('svg[aria-label="Feed de atividades"], svg[aria-label="Página inicial"], svg[aria-label="Direct"]').count() > 0
                )

                if is_logged_now:
                    logger.info("🎉 Login manual detectado com sucesso! O robô agora assumirá o controle do fluxo.")
                    await asyncio.sleep(3.0)  # Delay de segurança para estabilização da página
                    return True

                await asyncio.sleep(interval)
                elapsed += interval

            logger.error("⏱️ Tempo limite para login manual esgotado (5 minutos).")
            return False

        except Exception as e:
            logger.error(f"Erro no fluxo de login manual: {e}")
            return False

    async def comment(self, post_url: str, comment_text: str) -> bool:
        """
        Navega ao post, clica na caixa de texto e digita imitando digitação humana.
        """
        if not self.page:
            return False

        try:
            if self.page.url != post_url:
                logger.info(f"Navegando até o post: {post_url}")
                await self.page.goto(post_url, wait_until="load")
                await asyncio.sleep(random.uniform(2.0, 3.5))

            # Seletor multilíngue para a caixa de comentário
            comment_box = self.page.locator(
                'textarea[placeholder*="comentário"], '
                'textarea[placeholder*="comment"], '
                'textarea[aria-label*="comentário"], '
                'textarea[aria-label*="comment"]'
            ).first

            # Aguarda a caixa de comentário estar visível
            await comment_box.wait_for(state="visible", timeout=10000)
            await comment_box.click()
            await asyncio.sleep(random.uniform(0.5, 1.0))

            logger.info("Simulando digitação humana do comentário...")
            # Limpa qualquer texto residual antes de digitar
            await comment_box.fill("")
            await asyncio.sleep(random.uniform(0.2, 0.5))

            for caractere in comment_text:
                await comment_box.type(caractere)
                await asyncio.sleep(random.uniform(0.04, 0.18))

            await asyncio.sleep(random.uniform(0.5, 1.2))

            # Seletor multilíngue para o botão de postar
            publish_button = self.page.locator(
                'div[role="button"]:has-text("Postar"), '
                'div[role="button"]:has-text("Publicar"), '
                'div[role="button"]:has-text("Post"), '
                'div[role="button"]:has-text("Publish")'
            ).first

            # Aguarda o botão estar visível e clica
            await publish_button.wait_for(state="visible", timeout=5000)
            await publish_button.click()
            
            logger.info("Comentário enviado! Aguardando estabilização...")
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar comentário no post {post_url}: {e}")
            return False
