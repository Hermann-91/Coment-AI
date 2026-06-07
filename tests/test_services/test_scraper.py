from unittest.mock import patch, MagicMock
from src.services.scraper_service import ScraperService

@patch("src.services.scraper_service.requests.get")
def test_scrape_website_success(mock_get):
    """
    Testa se o ScraperService limpa o código HTML com sucesso,
    descartando scripts, estilos, cabeçalhos e menus, restando apenas o texto puro útil.
    """
    # Arrange: Criamos um HTML fictício contendo tags que devem ser descartadas
    mock_response = MagicMock()
    html_content = """
    <html>
        <head>
            <style>body { color: red; }</style>
            <script>console.log('teste-script');</script>
        </head>
        <body>
            <nav>Menu de Navegação Principal</nav>
            <header>Cabeçalho da Página</header>
            <main>
                <h1>Calculadora de Custos</h1>
                <p>Este aplicativo resolve a gestão financeira de motoristas.</p>
            </main>
            <footer>Direitos Reservados - Rodapé</footer>
        </body>
    </html>
    """
    # Convertendo a string UTF-8 contendo acentuação para bytes de forma segura
    mock_response.content = html_content.encode("utf-8")
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Act: Executamos a varredura
    result = ScraperService.scrape_website("https://site-teste-produto.com")

    # Assert: Garantimos que apenas o texto útil foi extraído
    assert "Calculadora de Custos" in result
    assert "gestão financeira de motoristas" in result
    assert "Menu de Navegação Principal" not in result
    assert "teste-script" not in result
    assert "body { color" not in result
