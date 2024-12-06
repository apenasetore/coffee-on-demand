from pydantic import BaseModel


class Step(BaseModel):
    explanation: str
    output: str


class RegisterResponseFormat(BaseModel):
    in_phase: bool
    firstname: bool
    lastname: bool

class ResponseFormat(BaseModel):
    # steps: list[Step]
    in_phase: bool
    message: str
    quantity: int
    container: int
    want_to_register: bool


class ResponseStopFormat(BaseModel):
    stop: bool
    message: str
    reason: str
