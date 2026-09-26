import os
import time

KEY_LEN = 32
IV_LEN = 16
MAC_LEN = 8


def _to_octet(bee2_lib, data: bytes):
    size = len(data) if data else 1
    vp = bee2_lib.memAlloc(size)

    if data:
        bee2_lib.bee2_memmove(vp, data, len(data))

    return vp, bee2_lib.vp2op(vp)


def _check_err(value, func_name: str) -> int:

    if not isinstance(value, int):
        raise RuntimeError(
            f"{func_name}: SWIG вернул {type(value).__name__} вместо int. "
            "Пересоберите биндинг или добавьте явный typemap в .i-файл."
        )
    return value


def hash256(data: bytes) -> bytes:
    from . import bee2_lib

    if not data:
        return b"\x00" * 32

    src_vp, src_op = _to_octet(bee2_lib, data)
    hash_vp = bee2_lib.memAlloc(32)
    hash_op = bee2_lib.vp2op(hash_vp)

    try:
        err = _check_err(bee2_lib.beltHash(hash_op, src_op, len(data)), "beltHash")
        if err != 0:
            raise RuntimeError(f"beltHash error: {err}")
        return bee2_lib.bee2_get_bytes(hash_vp, 32)
    finally:
        bee2_lib.memFree(src_vp)
        bee2_lib.memFree(hash_vp)


def encrypt(
    data: bytes,
    key: bytes,
    aad: bytes = b"",
    iv: bytes | None = None,
) -> tuple[bytes, bytes, bytes, float]:

    from . import bee2_lib

    if len(key) != KEY_LEN:
        raise ValueError(f"key must be {KEY_LEN} bytes, got {len(key)}")

    if iv is None:
        iv = os.urandom(IV_LEN)
    elif len(iv) != IV_LEN:
        raise ValueError(f"iv must be {IV_LEN} bytes, got {len(iv)}")

    dest_vp = bee2_lib.memAlloc(len(data) if data else 1)
    dest_op = bee2_lib.vp2op(dest_vp)

    src1_vp, src1_op = _to_octet(bee2_lib, data)
    src2_vp, src2_op = _to_octet(bee2_lib, aad)
    key_vp, key_op = _to_octet(bee2_lib, key)
    iv_vp, iv_op = _to_octet(bee2_lib, iv)

    mac_vp = bee2_lib.memAlloc(MAC_LEN)
    mac_op = bee2_lib.vp2op(mac_vp)

    try:
        start = time.perf_counter()
        err = bee2_lib.beltDWPWrap(
            dest_op, mac_op,
            src1_op, len(data),
            src2_op, len(aad),
            key_op, len(key),
            iv_op,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        err = _check_err(err, "beltDWPWrap")
        if err != 0:
            raise RuntimeError(f"beltDWPWrap error: {err}")

        ciphertext = bee2_lib.bee2_get_bytes(dest_vp, len(data)) if data else b""
        mac = bee2_lib.bee2_get_bytes(mac_vp, MAC_LEN)

        return ciphertext, mac, iv, elapsed_ms

    finally:
        for vp in (dest_vp, src1_vp, src2_vp, key_vp, iv_vp, mac_vp):
            bee2_lib.memFree(vp)


def decrypt(
    data: bytes,
    key: bytes,
    mac: bytes,
    iv: bytes,
    aad: bytes = b"",
) -> tuple[bytes, float]:

    from . import bee2_lib

    if len(key) != KEY_LEN:
        raise ValueError(f"key must be {KEY_LEN} bytes, got {len(key)}")
    if len(mac) != MAC_LEN:
        raise ValueError(f"mac must be {MAC_LEN} bytes, got {len(mac)}")
    if len(iv) != IV_LEN:
        raise ValueError(f"iv must be {IV_LEN} bytes, got {len(iv)}")

    dest_vp = bee2_lib.memAlloc(len(data) if data else 1)
    dest_op = bee2_lib.vp2op(dest_vp)

    src1_vp, src1_op = _to_octet(bee2_lib, data)
    src2_vp, src2_op = _to_octet(bee2_lib, aad)
    mac_vp, mac_op = _to_octet(bee2_lib, mac)
    key_vp, key_op = _to_octet(bee2_lib, key)
    iv_vp, iv_op = _to_octet(bee2_lib, iv)

    try:
        start = time.perf_counter()
        err = bee2_lib.beltDWPUnwrap(
            dest_op,
            src1_op, len(data),
            src2_op, len(aad),
            mac_op,
            key_op, len(key),
            iv_op,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        err = _check_err(err, "beltDWPUnwrap")
        if err != 0:
            raise IntegrityError(
                f"belt-dwp: проверка имитовставки не пройдена (err={err})"
            )

        plaintext = bee2_lib.bee2_get_bytes(dest_vp, len(data)) if data else b""

        return plaintext, elapsed_ms

    finally:
        for vp in (dest_vp, src1_vp, src2_vp, mac_vp, key_vp, iv_vp):
            bee2_lib.memFree(vp)


class IntegrityError(ValueError):
    """Имитовставка не сошлась: данные повреждены, подделаны или ключ неверен."""