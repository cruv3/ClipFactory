from pydantic import BaseModel
from typing import List

class VideoRequest(BaseModel):
    scenes: List[str]
    folder_name: str