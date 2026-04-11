import hashlib
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class AESCipher:
    """Decrypt Feishu event callback encrypted payloads."""

    def __init__(self, key: str):
        sha256 = hashlib.sha256()
        sha256.update(key.encode("utf-8"))
        self.key = sha256.digest()

    def decrypt(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted)
        iv = data[:16]
        cipher = Cipher(
            algorithms.AES(self.key), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(data[16:]) + decryptor.finalize()
        # Remove PKCS7 padding
        pad_len = decrypted[-1]
        return decrypted[:-pad_len].decode("utf-8")
