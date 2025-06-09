from typing import Optional, Dict
from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        # 1. Spróbuj z nagłówka Authorization (standard)
        authorization: Optional[str] = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)  # type: ignore
        if authorization and scheme and param and scheme.lower() == "bearer":
            return param

        # 2. Jeśli nie ma w nagłówku, spróbuj z ciasteczka "access_token"
        token_from_cookie: Optional[str] = request.cookies.get("access_token")

        if token_from_cookie:
            # Sprawdź, czy token z ciasteczka ma prefix "Bearer " i usuń go
            parts = token_from_cookie.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]  # Zwróć sam token
            elif (
                len(parts) == 1
            ):  # Jeśli w ciasteczku jest tylko sam token (bez "Bearer ")
                return parts[0]
            # Jeśli format jest niepoprawny, a auto_error=True, poniższy kod rzuci błąd

        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return None
