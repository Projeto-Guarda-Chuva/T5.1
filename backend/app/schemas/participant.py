from pydantic import BaseModel, EmailStr

class ParticipantCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    consent_accepted: bool = False

class ParticipantLogin(BaseModel):
    email: EmailStr
    password: str

class ParticipantResponse(BaseModel):
    id: str
    name: str
    email: EmailStr

class ParticipantToken(BaseModel):
    access_token: str
    user: ParticipantResponse