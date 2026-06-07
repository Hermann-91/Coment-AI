import asyncio
import random
from playwright.async_api import Page
from src.utils.logger import setup_logger

logger = setup_logger("InstagramScraper")

class InstagramScraper:
    """
    Responsabilidade única: Extração de informações do Instagram (Hashtags, posts e legendas).
    """
    def __init__(self, page: Page):
        self.page = page

    async def get_posts_by_hashtag(self, hashtag: str, limit: int = 5) -> list[str]:
        """
        Acessa a hashtag, simula rolagens e extrai as URLs de posts recentes e Reels.
        """
        if not self.page:
            return []

        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        logger.info(f"Buscando publicações da hashtag #{hashtag}...")

        try:
            await self.page.goto(url, wait_until="load")
            await asyncio.sleep(random.uniform(2.5, 4.0))

            # Simula um scroll suave para baixo para forçar o carregamento dinâmico do Instagram
            logger.info("Realizando rolagem de página para carregar posts...")
            await self.page.evaluate("window.scrollTo(0, 600)")
            await asyncio.sleep(random.uniform(1.5, 3.0))

            # Coleta links de posts tradicionais (/p/) e Reels (/reel/)
            links_posts = await self.page.locator('a[href*="/p/"]').all_attribute_values("href")
            links_reels = await self.page.locator('a[href*="/reel/"]').all_attribute_values("href")
            
            # Une as listas e remove duplicadas
            all_links = list(set(links_posts + links_reels))
            
            # Filtra e formata para URLs absolutas
            filtered_links = []
            for link in all_links:
                full_link = f"https://www.instagram.com{link}" if not link.startswith("http") else link
                filtered_links.append(full_link)

            # Limita a quantidade solicitada
            unique_links = filtered_links[:limit]
            
            logger.info(f"Encontrados {len(unique_links)} posts/reels para a hashtag #{hashtag}.")
            return unique_links

        except Exception as e:
            logger.error(f"Erro ao capturar posts da hashtag #{hashtag}: {e}")
            return []

    async def get_post_caption(self, post_url: str) -> str:
        """
        Acessa um post e extrai o texto da legenda do autor.
        """
        if not self.page:
            return ""

        try:
            logger.info(f"Extraindo legenda da URL: {post_url}")
            await self.page.goto(post_url, wait_until="load")
            await asyncio.sleep(random.uniform(2.0, 4.0))

            # Seletores do Instagram comuns para a legenda principal
            caption_element = self.page.locator('h1, span[class*="x1lliihq"]')
            if await caption_element.count() > 0:
                text = await caption_element.first.text_content()
                return text.strip()
            
            return ""

        except Exception as e:
            logger.error(f"Falha ao ler legenda do post {post_url}: {e}")
            return ""
