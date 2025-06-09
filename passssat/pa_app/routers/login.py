from fastapi import APIRouter, Request, Depends, HTTPException, status, Response

from fastapi.responses import HTMLResponse

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from pa_app.utils.utils import templates
from pa_app.security_utils import OAuth2PasswordBearerWithCookie


router = APIRouter()

SECRET_KEY = "2e696b7554272d9a5f1e4f112a91c4c43bbdcea18aacdc4945675703c1f65550"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

db = {
    "PassAt": {
        "username": "PassAt",
        "full_name": "Pass Atlantic",
        "email": "jd@pomidor.com",
        "hashed_password": "$2b$12$BKO2CD4SNfrKYlHIvY92SeQXUN8uRWM.DY6/gyN5.y7bIF60cyPRy",
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db_users, username: str) -> Optional[UserInDB]:
    if username in db_users:
        user_data = db_users[username]
        return UserInDB(**user_data)
    return None


def authenticate_user(db_users, username: str, password: str) -> Optional[UserInDB]:
    user = get_user(db_users, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta  # Użyj świadomego czasu UTC
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username_from_payload: Optional[str] = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username_from_payload = payload.get(
            "sub"
        )  # payload.get("sub") może zwrócić None
        if username_from_payload is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_user(db, username=username_from_payload)  # Przekazujemy pewny string
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


@router.post("/token")
async def login_for_access_token(
    response: Response, form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Ustaw ciasteczko HTTP z tokenem
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="Lax",
        secure=False,  # Ustaw na True, jeśli używasz HTTPS w produkcji
        # Dla localhost (HTTP) musi być False
        path="/",
    )
    # Zwróć token również w ciele JSON (może być przydatne dla niektórych klientów lub debugowania)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/user/me/", response_model=User)
async def read_user_me(
    current_user: UserInDB = Depends(get_current_active_user),
):  # Poprawiono typ
    return current_user


@router.get("/user/me/items")
async def read_user_items(
    current_user: UserInDB = Depends(get_current_active_user),
):  # Poprawiono typ
    return [{"item_id": 1, "owner": current_user.username}]


@router.get("/login", response_class=HTMLResponse, name="login_page")
def serve_login_page(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("index_login.html", context)
