import base64
import secrets
import uuid
import time

from bee2_pack.bee2_wrapper import encrypt, decrypt, hash256
from database.db import save_photo, get_photo, save_key, get_key

IV_LEN = 16
MAC_LEN = 8


def generate_key() -> bytes:
    return secrets.token_bytes(32)


def upload_photo(photo_base64: str):
    start_upload_time = time.perf_counter()

    photo_bytes = base64.b64decode(photo_base64)

    photo_id = str(uuid.uuid4())

    photo_hash = hash256(photo_bytes)

    key = generate_key()

    ciphertext, mac, iv, crypto_time_ms = encrypt(
        photo_bytes,
        key
    )

    encrypted_photo = iv + mac + ciphertext

    save_photo(
        photo_id,
        encrypted_photo,
        photo_hash
    )

    save_key(
        photo_id,
        key
    )

    end_upload_time = time.perf_counter()

    upload_time_ms = (
        end_upload_time - start_upload_time
    ) * 1000

    return (
        photo_id,
        crypto_time_ms,
        upload_time_ms
    )


def download_photo(photo_id: str):
    start_download_time = time.perf_counter()

    stored_blob, saved_hash = get_photo(photo_id)

    if stored_blob is None:
        raise ValueError("Photo not found")

    if saved_hash is None:
        raise ValueError("Hash not found")

    if len(stored_blob) < IV_LEN + MAC_LEN:
        raise ValueError("Corrupted photo record")

    iv = stored_blob[:IV_LEN]
    mac = stored_blob[IV_LEN:IV_LEN + MAC_LEN]
    ciphertext = stored_blob[IV_LEN + MAC_LEN:]

    key = get_key(photo_id)

    if key is None:
        raise ValueError("Key not found")

    photo_bytes, decrypt_time_ms = decrypt(
        ciphertext,
        key,
        mac,
        iv
    )

    check_hash = hash256(photo_bytes)

    if check_hash != saved_hash:
        raise ValueError("Integrity error")

    end_download_time = time.perf_counter()

    download_time_ms = (
        end_download_time - start_download_time
    ) * 1000

    return (
        base64.b64encode(photo_bytes).decode(),
        download_time_ms,
        decrypt_time_ms
    )


