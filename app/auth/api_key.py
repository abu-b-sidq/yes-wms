from __future__ import annotations

class LegacyAPIKeyVerifier:
    def __init__(self, allowed_keys: dict[str, str]) -> None:
        # allowed_keys is keyed by API key, value is a human-friendly client label.
        self.allowed_keys = allowed_keys

    def verify(self, api_key: str) -> str | None:
        return self.allowed_keys.get(api_key)
