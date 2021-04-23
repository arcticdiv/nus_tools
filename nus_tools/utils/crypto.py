import hashlib
from typing import Any, Callable, List, Optional, Union, cast
from constructutils.checksum import ChecksumVerifyError

from Crypto.Cipher import AES as _AES
from Crypto.Cipher._mode_cbc import CbcMode

from Crypto.PublicKey import RSA as _RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA1, SHA256

from .. import ids
from ..config import Configuration


class AES:
    @classmethod
    def cbc(cls, key: bytes, iv: bytes) -> CbcMode:
        return cls.__get_inst(key, _AES.MODE_CBC, iv)

    @staticmethod
    def __get_inst(key: bytes, mode: int, iv: Optional[bytes] = None) -> Any:
        return _AES.new(key=key, mode=mode, iv=cast(bytes, iv))


class TitleKey:
    @classmethod
    def decrypt(cls, title_key: bytes, title_id: ids.TTitleIDInput) -> bytes:
        return cls.__get_aes(title_id).decrypt(title_key)

    @classmethod
    def encrypt(cls, title_key: bytes, title_id: ids.TTitleIDInput) -> bytes:
        return cls.__get_aes(title_id).encrypt(title_key)

    @staticmethod
    def __get_aes(title_id: ids.TTitleIDInput) -> CbcMode:
        title_id = ids.TitleID.get_inst(title_id)
        if title_id.type.platform == ids.TitlePlatform.WIIU:
            common_key = Configuration.keys.common_wiiu
        elif title_id.type.platform == ids.TitlePlatform._3DS:
            raise NotImplementedError
        else:
            assert False
        return AES.cbc(common_key, bytes(title_id) + bytes(8))


#####
# checksum stuff
#####

def verify_sha1(data: bytes, expected_hash: bytes) -> None:
    digest = hashlib.sha1(data).digest()
    if digest != expected_hash:
        raise ChecksumVerifyError('hash mismatch', expected_hash, digest)


#####
# cert stuff
#####

class SignatureError(Exception):
    pass


# TODO: ecdsa
def verify_signature(data: bytes, signature_struct: Any, key_struct: Any) -> bool:
    # create signer from public key
    signer = pkcs1_15.new(_RSA.construct((
        int.from_bytes(key_struct.modulus, byteorder='big'),
        key_struct.exponent
    )))

    # calculate data hash
    hash_algorithm = signature_struct.type.hash_alg
    hash_func: Callable[[bytes], Union[SHA1.SHA1Hash, SHA256.SHA256Hash]]
    if hash_algorithm == 'SHA1':
        hash_func = SHA1.new
    elif hash_algorithm == 'SHA256':
        hash_func = SHA256.new
    else:
        raise RuntimeError(f'unknown hash algorithm {hash_algorithm!r}')

    data_hash = hash_func(data)

    # verify signature
    try:
        signer.verify(data_hash, signature_struct.data)
        return True
    except ValueError:
        return False


def verify_chain(data: bytes, issuer: str, signature_struct: Any, certificate_structs: List[Any], root_key: Any) -> None:
    certificates = {cert.name: cert for cert in certificate_structs}

    # split a string like 'Root-CA00000003-CP0000000b' into parts
    issuer_parts = issuer.split('-')
    if issuer_parts[0] != 'Root':
        raise RuntimeError('topmost certificate in chain must be \'Root\'')
    for part in issuer_parts[1:]:
        if part not in certificates:
            raise RuntimeError(f'missing certificate: {part!r}')

    # iterate chain
    while True:
        issuer_part = issuer_parts[-1]
        if issuer_part == 'Root':
            # root certificate
            issuer_key = root_key
        else:
            # intermediate certificate
            issuer_cert = certificates[issuer_part]
            issuer_key = issuer_cert.key
            if issuer_cert.issuer.split('-') != issuer_parts[:-1]:
                raise RuntimeError(f'issuer of intermediate certificate {issuer_cert.name} does not match issuer of initial data')

        # do the thing
        if not verify_signature(data, signature_struct, issuer_key):
            raise SignatureError(f'invalid signature for data {data[:32]!r}[...] by {issuer_part}')

        # if issuer is 'Root' and the signature is valid, we're done
        if issuer_part == 'Root':
            break

        # otherwise, check signature of current certificate:
        # remove last part from issuer, just checked that one
        issuer_parts = issuer_parts[:-1]
        # data to be verified is the raw data of the certificate that was just used
        data = issuer_cert.__raw_cert__
        # signature of new data
        signature_struct = issuer_cert.signature
