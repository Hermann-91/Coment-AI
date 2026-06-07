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
        Acessa a hashtag e extrai as URLs de posts recentes.
        """
        if not self.page:
            return []

        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        logger.info(f"Buscando publicações da hashtag #{hashtag}...")

        try:
            await self.page.goto(url, wait_until="load")
            await asyncio.sleep(random.uniform(2.5, 5.0))

            links = await self.page.locator('a[href*="/p/"]').all_attribute_values("href")
            unique_links = list(set(links))[:limit]

            full_urls = [
                f"https://www.instagram.com{link}" if not link.startswith("http") else link
                for link in unique_links
            ]
            return full_urls

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

            caption_element = self.page.locator('h1, span[class*="x1lliihq"]')
            if await caption_element.count() > 0:
                text = await caption_element.first.text_content()
                return text.strip()
            
            return ""

        except Exception as e:
            logger.error(f"Falha ao ler legenda do post {post_url}: {e}")
            return ""
