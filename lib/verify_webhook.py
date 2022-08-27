import base64
import hashlib
import hmac


def verify(data, hmac_header, shared_secret):
    """
    :param data: binary
    :param hmac_header: str
    :param shared_secret: str
    :return: bool
    """

    _hmac_calc = hmac.new(shared_secret.encode('utf-8'),
                          data,
                          hashlib.sha256).digest()
    hmac_calc = base64.b64encode(_hmac_calc)

    res = hmac.compare_digest(hmac_header.encode('utf-8'), hmac_calc)
    return res
