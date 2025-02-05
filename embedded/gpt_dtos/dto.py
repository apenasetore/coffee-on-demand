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


class ResponseFormat(BaseModel):
    in_phase: bool
    message: str
    quantity: int
    container: int
    total: float
    want_to_register: bool


class ResponseStopFormat(BaseModel):
    stop: bool
    message: str
    reason: str
