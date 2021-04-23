from construct import FocusedSeq, Terminated

from .common import SignatureAlgorithm

struct = FocusedSeq('key', 'key' / SignatureAlgorithm.RSA4096.key_construct, Terminated)
