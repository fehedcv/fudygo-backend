from pydantic import BaseModel

class SessionLoginRequest(BaseModel):
    idToken: str