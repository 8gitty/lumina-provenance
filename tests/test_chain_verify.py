from chain_verify import hash_data
import hashlib
import json

def test_hash_data():
    data = {"url": "http://example.com", "score": 0.95}
    expected_str = json.dumps(data, sort_keys=True)
    expected_hash = hashlib.sha256(expected_str.encode('utf-8')).hexdigest()
    assert hash_data(data) == expected_hash
