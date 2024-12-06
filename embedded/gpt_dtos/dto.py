from pydantic import BaseModel


class Step(BaseModel):
    explanation: str
    output: str


class ResponseFormat(BaseModel):
    # steps: list[Step]
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
