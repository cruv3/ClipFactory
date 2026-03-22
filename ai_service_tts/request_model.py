from pydantic import BaseModel

class VoiceRequest(BaseModel):
    script_text: str
    folder_name: str
    voice_name: str = "af_bella"
    speed: float = 1.15