"""PKCE / OIDC protocol helpers.
State, nonce and code verifier/challenge are generated server-side during
the login handoff; the challenge is S256 as required by RFC 7636. The
provider's JWKS is fetched from the operator-discovered issuer URL.
"""
from __future__ import annotations
import base64,hashlib,secrets
from urllib.parse import urlencode
import httpx

MASK32=0xFFFFFFFF;RS256_JWK_ALGORITHM="RS256"

def generate_state()->str:return secrets.token_urlsafe(24)
def generate_nonce()->str:return secrets.token_urlsafe(24)
def generate_verifier()->str:return secrets.token_urlsafe(64)
def generate_challenge(verifier:str)->str:
    digest=hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

async def fetch_discovery(provider_url:str,http:httpx.AsyncClient|None=None)->dict:
    url=provider_url.rstrip("/")+"/.well-known/openid-configuration"
    async with _client(http)as c:
        r=await c.get(url,timeout=10);r.raise_for_status();return r.json()

async def fetch_jwks_jwk(discovery:dict,provider_url:str,http:httpx.AsyncClient|None=None)->dict:
    url=discovery["jwks_uri"]
    async with _client(http)as c:
        r=await c.get(url,timeout=10);r.raise_for_status()
        keys=r.json().get("keys",[])
        return keys[0]if keys else{}

def _base64url_decode(text:str)->bytes:
    pad="="*((4-len(text)%4)%4)
    return base64.urlsafe_b64decode(text+pad)

def jwk_to_pem(jwk:dict)->str:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
    n=int.from_bytes(_base64url_decode(jwk["n"]),"big")
    e=int.from_bytes(_base64url_decode(jwk["e"]),"big")
    key=rsa.RSAPublicNumbers(e,n).public_key()
    return key.public_bytes(Encoding.PEM,PublicFormat.SubjectPublicKeyInfo).decode()

def build_authorization_url(discovery:dict,client_id:str,redirect_uri:str,state:str,nonce:str,code_verifier:str,scope:str="openid email profile")->str:
    params={"response_type":"code","client_id":client_id,"redirect_uri":redirect_uri,"state":state,"nonce":nonce,"code_challenge":generate_challenge(code_verifier),"code_challenge_method":"S256","scope":scope}
    return discovery["authorization_endpoint"]+"?"+urlencode(params)

async def exchange_code(discovery:dict,client_id:str,client_secret:str,redirect_uri:str,code:str,code_verifier:str,http:httpx.AsyncClient|None=None)->dict:
    data={"grant_type":"authorization_code","code":code,"redirect_uri":redirect_uri,"client_id":client_id,"code_verifier":code_verifier}
    if client_secret:data["client_secret"]=client_secret
    async with _client(http)as c:
        r=await c.post(discovery["token_endpoint"],data=data,timeout=10);r.raise_for_status();return r.json()

async def validate_id_token(id_token:str,pem:str,nonce:str,audience:str,issuer:str)->dict:
    import jwt
    claims=jwt.decode(id_token,pem,algorithms=["RS256"],audience=audience,issuer=issuer,nonce=nonce,options={"verify_aud":True,"verify_iss":True,"verify_exp":True})
    return claims

def _client(http:httpx.AsyncClient|None)->httpx.AsyncClient:
    return http if http is not None else httpx.AsyncClient(timeout=10,follow_redirects=True)