from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from unidl.downloader.downloader import _openssl_decrypt


def test_hls_aes128_uses_in_process_decryption() -> None:
    key = bytes(range(16))
    iv = bytes(range(16, 32))
    clear = (b"HLS AES-128 segment\0" * 400)[:8192]
    padding = 16 - len(clear) % 16
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    encrypted = encryptor.update(clear + bytes([padding]) * padding) + encryptor.finalize()

    assert _openssl_decrypt(encrypted, "AES_128", key, iv) == clear


def test_hls_aes128_ecb_uses_in_process_decryption() -> None:
    key = bytes(range(16))
    clear = (b"HLS AES ECB segment\0" * 500)[:8000]
    padding = 16 - len(clear) % 16
    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    encrypted = encryptor.update(clear + bytes([padding]) * padding) + encryptor.finalize()

    assert _openssl_decrypt(encrypted, "AES_128_ECB", key, None) == clear
