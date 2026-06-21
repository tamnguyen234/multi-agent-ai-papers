from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    email: EmailStr

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    noti_daily: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class NotificationUpdate(BaseModel):
    noti_daily: bool
