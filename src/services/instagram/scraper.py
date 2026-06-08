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
        Acessa um post e extrai o texto da legenda do autor E os primeiros comentários válidos
        de forma assíncrona com espera ativa.
        Junta os blocos de texto úteis (até 4 blocos) para ajudar na análise semântica.
        """
        if not self.page:
            return ""

        try:
            logger.info(f"Extraindo legenda e comentários da URL: {post_url}")
            await self.page.goto(post_url, wait_until="load")
            
            # Seletor unificado para garantir que a leitura siga a ordem cronológica de cima para baixo
            unified_selector = 'h1, span[class*="_ap3a"], span[class*="x1lliihq"]'

            # Termos comuns da interface/menu lateral do Instagram que devem ser descartados
            menu_terms = {
                "página inicial", "pesquisa", "explorar", "reels", "mensagens", 
                "notificações", "criar", "perfil", "mais", "instagram", "entrar", "cadastre-se",
                "home", "search", "explore", "messages", "notifications", "create", "profile",
                "log in", "sign up", "configurações", "settings", "responder", "ver tradução"
            }

            # ESPERA ATIVA: Aguarda até 8 segundos no total para que o seletor unificado fique visível
            try:
                await self.page.locator(unified_selector).first.wait_for(state="visible", timeout=8000)
            except Exception:
                logger.warning("Nenhum seletor contendo texto ficou visível no tempo limite.")

            collected_blocks = []
            seen_texts = set()

            # Varre os elementos na ordem em que aparecem no DOM
            locators = self.page.locator(unified_selector)
            count = await locators.count()
            
            for i in range(count):
                try:
                    text = await locators.nth(i).text_content()
                    if text:
                        cleaned_text = text.strip()
                        
                        # Ignora se for menu
                        if cleaned_text.lower() in menu_terms:
                            continue
                        
                        # Filtro de segurança contra nomes de usuários e botões de interface:
                        # Exige que o texto tenha pelo menos 12 caracteres e contenha no mínimo 3 palavras (espaços)
                        if len(cleaned_text) <= 12 or len(cleaned_text.split()) < 3:
                            continue
                        
                        # Evita repetição exata
                        normalized_text = cleaned_text.lower()
                        if normalized_text in seen_texts:
                            continue
                            
                        seen_texts.add(normalized_text)
                        collected_blocks.append(cleaned_text)
                        
                        # Limita a leitura a no máximo 4 blocos de texto (legenda + primeiros comentários)
                        if len(collected_blocks) >= 4:
                            break
                    except Exception:
                        continue

            if collected_blocks:
                full_text = "\n\n".join(collected_blocks)
                logger.info(f"Legenda e comentários capturados com sucesso. Encontrados {len(collected_blocks)} blocos. Tamanho: {len(full_text)} caracteres.")
                return full_text

            logger.warning("Nenhum seletor contendo legenda ou comentários de postagem retornou dados válidos.")
            return ""

        except Exception as e:
            logger.error(f"Falha ao ler legenda/comentários do post {post_url}: {e}")
            return ""
