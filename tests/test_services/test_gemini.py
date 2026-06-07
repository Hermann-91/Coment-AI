from unittest.mock import patch, MagicMock
from src.services.gemini_service import GeminiService

@patch("src.services.gemini_service.genai.GenerativeModel")
def test_analyze_product_success(mock_model_class):
    """
    Valida a análise de produto com o Gemini, garantindo que o retorno JSON
    seja interpretado e transformado em dicionário corretamente.
    """
    # Arrange: Mocka o modelo e sua resposta textual em formato JSON
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"persona": "Motoristas de app", "dores": ["custo de gasolina", "falta de lucro"]}'
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    # Inicializamos o serviço injetando uma chave de teste
    service = GeminiService(api_key="chave_ficticia_teste")

    # Act
    result = service.analyze_product("Planilha de custos", "Site de dados")

    # Assert
    assert result["persona"] == "Motoristas de app"
    assert "custo de gasolina" in result["dores"]
    mock_model_instance.generate_content.assert_called_once()

@patch("src.services.gemini_service.genai.GenerativeModel")
def test_evaluate_post_generate_comment(mock_model_class):
    """
    Testa a geração de comentário quando o post aborda uma dor relevante.
    """
    # Arrange: Define a resposta simulada que o modelo dará contendo o comentário
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Sei bem como é isso! Teste essa calculadora no link: https://meulink.com"
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    service = GeminiService(api_key="chave_ficticia_teste")
    product_analysis = {"persona": "Motoristas", "dores": ["preço da gasolina"]}

    # Act
    comment = service.evaluate_post_and_generate_comment(
        post_text="A gasolina subiu de novo em SP, impossível trabalhar!",
        product_analysis=product_analysis,
        product_link="https://meulink.com"
    )

    # Assert
    assert comment == "Sei bem como é isso! Teste essa calculadora no link: https://meulink.com"

@patch("src.services.gemini_service.genai.GenerativeModel")
def test_evaluate_post_should_skip(mock_model_class):
    """
    Testa se o serviço retorna None (Pular) quando a legenda do post não reflete nenhuma dor do produto.
    """
    # Arrange: Simula o retorno de 'PULAR' do Gemini
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "PULAR"
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    service = GeminiService(api_key="chave_ficticia_teste")
    product_analysis = {"persona": "Motoristas", "dores": ["preço da gasolina"]}

    # Act
    comment = service.evaluate_post_and_generate_comment(
        post_text="Belo churrasco em família no domingo!",
        product_analysis=product_analysis,
        product_link="https://meulink.com"
    )

    # Assert
    assert comment is None
