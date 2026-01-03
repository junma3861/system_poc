from dataclasses import dataclass

@dataclass
class Settings:
    openrouter_api_key: str
    openrouter_model: str = "openrouter-default-model"
