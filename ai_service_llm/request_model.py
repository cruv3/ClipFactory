from pydantic import BaseModel

class ScriptRequest(BaseModel):
    prompt: str
    model_id: str = "google/gemma-3-27b-it"
