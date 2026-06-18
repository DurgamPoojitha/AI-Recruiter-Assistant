import os
import jwt
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List

# Ensure these match the Auth0 configuration in .env
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
AUTH0_ALGORITHMS = ["RS256"]

security = HTTPBearer()

def verify_jwt(token: str) -> Dict[str, Any]:
    if not AUTH0_DOMAIN or not AUTH0_API_AUDIENCE:
        # Mock behavior if Auth0 is not fully configured (fallback)
        return {"sub": "mock-user", "org_id": 1, "roles": ["Admin"]}

    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks_client = jwt.PyJWKClient(jwks_url)
    
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload
    except jwt.PyJWKClientError as e:
        raise HTTPException(status_code=401, detail=f"Unable to fetch JWKS: {str(e)}")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token is expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Unable to parse authentication token: {str(e)}")

async def get_current_user() -> Dict[str, Any]:
    # Auth removed for testing - always return Admin user
    return {
        "user_id": "mock-user",
        "roles": ["Admin"],
        "org_id": 1
    }

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Dict[str, Any] = Security(get_current_user)):
        # If user has 'Admin' they bypass checks
        if "Admin" in user.get("roles", []):
            return user
            
        for role in self.allowed_roles:
            if role in user.get("roles", []):
                return user
                
        raise HTTPException(
            status_code=403, 
            detail=f"Operation not permitted. Required roles: {self.allowed_roles}"
        )
