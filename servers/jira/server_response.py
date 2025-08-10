from dataclasses import dataclass
from typing import Optional

@dataclass(init=True)
class Response:
    is_error: bool
    error_message: Optional[bool]