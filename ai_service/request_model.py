from pydantic import BaseModel
from typing import List

class ScriptRequest(BaseModel):
    prompt: str
    model_id: str = "google/gemma-2-9b-it"

class VoiceRequest(BaseModel):
    script_text: str
    folder_name: str
    voice_name: str = "af_bella"
    speed: float = 1.1

class VideoRequest(BaseModel):
    scenes: List[str]
    folder_name: str