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
        Acessa a hashtag, aguarda a renderização activa dos posts e extrai as URLs.
        """
        if not self.page:
            return []

        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        logger.info(f"Navegando para a hashtag: #{hashtag}")

        try:
            await self.page.goto(url, wait_until="load")
            
            # ESPERA ATIVA: Aguarda até 10 segundos para o Instagram carregar e renderizar os posts na grade
            logger.info("Aguardando carregamento dinâmico dos posts na grade...")
            try:
                await self.page.wait_for_selector('a[href*="/p/"], a[href*="/reel/"]', timeout=10000)
            except Exception:
                logger.warning(f"⚠️ Nenhuma publicação visível carregou para #{hashtag} no tempo limite de 10s.")
                return []

            # Simula um scroll suave para baixo para carregar mais posts dinamicamente
            logger.info("Realizando rolagem de página para carregar posts adicionais...")
            await self.page.evaluate("window.scrollTo(0, 600)")
            await asyncio.sleep(random.uniform(1.5, 3.0))

            # Coleta links de posts tradicionais (/p/) e Reels (/reel/) usando evaluate_all
            logger.info("Extraindo links de posts e reels...")
            links_posts = await self.page.locator('a[href*="/p/"]').evaluate_all(
                "elements => elements.map(el => el.getAttribute('href'))"
            )
            links_reels = await self.page.locator('a[href*="/reel/"]').evaluate_all(
                "elements => elements.map(el => el.getAttribute('href'))"
            )
            
            # Garante que as variáveis sejam listas mesmo em caso de retorno nulo
            links_posts = links_posts or []
            links_reels = links_reels or []

            # Une as locais e remove duplicadas
            all_links = list(set(links_posts + links_reels))
            
            # Filtra e formata para URLs absolutas
            filtered_links = []
            for link in all_links:
                if link:
                    full_link = f"https://www.instagram.com{link}" if not link.startswith("http") else link
                    filtered_links.append(full_link)

            # Limita a quantidade solicitada
            unique_links = filtered_links[:limit]
            
            logger.info(f"Encontrados {len(unique_links)} posts/reels para #{hashtag}.")
            return unique_links

        except Exception as e:
            logger.error(f"Erro ao capturar posts da hashtag #{hashtag}: {e}")
            return []

    async def get_post_caption(self, post_url: str) -> str:
        """
        Acessa um post e extrai o texto da legenda do autor de forma assíncrona com espera ativa.
        Varre todos os elementos da página e filtra elementos do menu do Instagram por conteúdo e tamanho.
        """
        if not self.page:
            return ""

        try:
            logger.info(f"Extraindo legenda da URL: {post_url}")
            await self.page.goto(post_url, wait_until="load")
            
            # Seletores amplos e globais de legenda
            caption_selectors = [
                'h1',                           # h1 da legenda
                'span[class*="_ap3a"]',         # Classe comum de texto no post
                'span[class*="x1lliihq"]'       # Classe genérica de texto no Instagram
            ]

            # Termos comuns da interface/menu lateral do Instagram que devem ser descartados
            menu_terms = {
                "página inicial", "pesquisa", "explorar", "reels", "mensagens", 
                "notificações", "criar", "perfil", "mais", "instagram", "entrar", "cadastre-se",
                "home", "search", "explore", "messages", "notifications", "create", "profile",
                "log in", "sign up", "configurações", "settings"
            }

            # ESPERA ATIVA: Aguarda até 8 segundos no total para que algum seletor fique visível
            for selector in caption_selectors:
                try:
                    await self.page.locator(selector).first.wait_for(state="visible", timeout=2000)
                    break
                except Exception:
                    continue

            # Varre os seletores para encontrar o primeiro texto de legenda válido
            for selector in caption_selectors:
                locators = self.page.locator(selector)
                count = await locators.count()
                
                for i in range(count):
                    try:
                        text = await locators.nth(i).text_content()
                        if text:
                            cleaned_text = text.strip()
                            # Descarta textos que são termos de menu ou muito curtos para serem legendas reais
                            if cleaned_text.lower() in menu_terms or len(cleaned_text) <= 15:
                                continue
                            
                            logger.info(f"Legenda capturada com sucesso via '{selector}': {cleaned_text[:50]}...")
                            return cleaned_text
                    except Exception:
                        continue

            logger.warning("Nenhum seletor contendo legenda de postagem retornou dados válidos.")
            return ""

        except Exception as e:
            logger.error(f"Falha ao ler legenda do post {post_url}: {e}")
            return ""
