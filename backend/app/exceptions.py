from __future__ import annotations


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class MeteoriteNotFoundError(AppError):
    def __init__(self, meteorite_id: int):
        super().__init__(f"Meteorite {meteorite_id} not found", status_code=404)


class AIConfigurationError(AppError):
    def __init__(self):
        super().__init__(
            "AI explanations are temporarily unavailable.",
            status_code=503,
        )


class AIGenerationError(AppError):
    def __init__(
        self,
        message: str = "Failed to generate AI explanation. Please try again later.",
    ):
        super().__init__(message, status_code=502)
