from web_search import search_web_for_image
from unittest.mock import patch, MagicMock, mock_open

@patch('web_search.vision.ImageAnnotatorClient')
@patch('os.environ.get')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_image_data")
def test_search_web_for_image(mock_file, mock_env, mock_client):
    mock_env.return_value = "fake_cred"
    
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.error.message = "" # Ensure error message is falsy
    mock_page = MagicMock()
    mock_page.url = "http://example.com"
    mock_page.page_title = "Example"
    mock_page.full_matching_images = True
    mock_page.partial_matching_images = False
    
    mock_response.web_detection.pages_with_matching_images = [mock_page]
    mock_instance.web_detection.return_value = mock_response
    
    results = search_web_for_image("dummy.jpg")
    assert len(results) == 1
    assert results[0]["url"] == "http://example.com"
    assert results[0]["score"] == 0.95
