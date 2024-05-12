from util import encode_jwt, decode_jwt


class TestUtil:
    def test_encode_jwt(self):
        token = encode_jwt('1', 'user 1', 'client')

        payload = decode_jwt(token)
        assert payload['id'] == '1'
        assert payload['user_id'] == 'user 1'
        assert payload['role'] == 'client'
