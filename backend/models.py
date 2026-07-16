"""
Pydantic models: the request bodies our endpoints accept, and the response
shape we ask Gemini to fill in for the quiz feature (response_schema).
"""

from pydantic import BaseModel


class SummarizePartRequest(BaseModel):
    part_index: int


class QuestionRequest(BaseModel):
    question: str


class QuizQuestion(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]


class ActivateConversationRequest(BaseModel):
    conversation_id: int
