from face_id import get_face_embedding
from unittest.mock import patch

@patch('face_id.DeepFace.represent')
def test_get_face_embedding_success(mock_represent):
    mock_represent.return_value = [{'embedding': [0.1, 0.2, 0.3], 'facial_area': {'x': 0, 'y': 0, 'w': 10, 'h': 10}}]
    result = get_face_embedding("dummy.jpg")
    assert result["success"] is True
    assert result["embedding"] == [0.1, 0.2, 0.3]

@patch('face_id.DeepFace.represent')
def test_get_face_embedding_fail(mock_represent):
    mock_represent.return_value = []
    result = get_face_embedding("dummy.jpg")
    assert result["success"] is False
