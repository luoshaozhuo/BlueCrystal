from __future__ import annotations
import hashlib, re, traceback
_NUMBER=re.compile(r"\b\d+(?:\.\d+)?\b"); _ADDR=re.compile(r"0x[0-9a-fA-F]+")
def make_error_fingerprint(exc:BaseException,*,operation:str)->str:
    frames=traceback.extract_tb(exc.__traceback__)
    stable=tuple((f.name,f.filename.rsplit("/",1)[-1]) for f in frames[-4:])
    msg=_NUMBER.sub("<n>",_ADDR.sub("<addr>",str(exc)))[:512]
    raw=repr((type(exc).__module__,type(exc).__qualname__,operation,msg,stable))
    return hashlib.sha256(raw.encode()).hexdigest()
