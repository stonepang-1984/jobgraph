"""Crypto utilities for License system"""

import hashlib
import os

from loguru import logger


def generate_key(password: str) -> bytes:
    """从密码派生加密密钥"""
    return hashlib.sha256(password.encode()).digest()[:32]


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """AES-256 加密数据

    Args:
        data: 要加密的数据
        key: 32字节密钥

    Returns:
        加密后的数据 (IV + 密文)
    """
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        # 生成随机 IV
        iv = os.urandom(16)

        # 填充数据
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        # 加密
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # 返回 IV + 密文
        return iv + ciphertext

    except ImportError:
        logger.error("cryptography package not installed")
        raise


def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """AES-256 解密数据

    Args:
        encrypted_data: 加密的数据 (IV + 密文)
        key: 32字节密钥

    Returns:
        解密后的数据
    """
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        # 提取 IV 和密文
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]

        # 解密
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # 去除填充
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data

    except ImportError:
        logger.error("cryptography package not installed")
        raise


def encrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    """加密文件

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        key: 32字节密钥
    """
    with open(input_path, "rb") as f:
        data = f.read()

    encrypted = encrypt_data(data, key)

    with open(output_path, "wb") as f:
        f.write(encrypted)

    logger.info(f"Encrypted {input_path} -> {output_path}")


def decrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    """解密文件

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        key: 32字节密钥
    """
    with open(input_path, "rb") as f:
        encrypted = f.read()

    decrypted = decrypt_data(encrypted, key)

    with open(output_path, "wb") as f:
        f.write(decrypted)

    logger.info(f"Decrypted {input_path} -> {output_path}")


def hash_data(data: bytes) -> str:
    """计算数据哈希"""
    return hashlib.sha256(data).hexdigest()
