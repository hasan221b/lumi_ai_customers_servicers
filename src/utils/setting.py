from pydantic import BaseModel

class Query(BaseModel):
    question: str
    user_id: str | None = None  # Optional field
    chat_id: str | None = None  # Optional field