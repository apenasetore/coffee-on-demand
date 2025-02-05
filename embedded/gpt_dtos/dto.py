from enum import Enum
from pydantic import BaseModel


class Step(BaseModel):
    explanation: str
    output: str


class GPTInteractionRegistration(BaseModel):
    response: str
    firstname: str = None
    lastname: str = None
    completed_conversation: bool


class GPTInteraction(BaseModel):
    response: str
    chosen_coffee_weight: int = None
    container_number: int = None
    total_price: float = None
    order_confirmed: bool = None


class GPTAudioResponse(BaseModel):
    audio_base64: str
    transcription: str
    audio_id: str


class GPTDataResponse(BaseModel):
    response: str
    chosen_coffee_weight: int = None
    container_number: int = None
    total_price: float = None
    order_confirmed: bool = None


class GPTRegistrationDataResponse(BaseModel):
    response: str
    firstname: str = None
    lastname: str = None
    user_intent_gotten: bool


class GPTStage(str, Enum):
    NORMAL_FLOW = "NORMAL_FLOW"
    REGISTRATION = "REGISTRATION"
