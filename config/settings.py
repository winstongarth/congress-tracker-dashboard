"""Central config. Every value CLAUDE.md marks [CONFIG] lives here, not as a
hardcoded constant elsewhere in the codebase."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- secrets / environment ---
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/congress_trading"
    congress_api_key: str = ""
    contact_email: str = "you@example.com"

    # --- api [CONFIG] ---
    # Gates GraphiQL and the relaxed CORS origin regex needed for the Expo
    # dev client (see "Mobile dev" in the README). Never enable in prod.
    debug: bool = False

    # --- scraping etiquette [CONFIG] ---
    request_delay_seconds: float = 2.5  # default: 1 request per 2-3 seconds
    cache_dir: str = "data/cache"

    @property
    def user_agent(self) -> str:
        return (
            "congress-trading-tracker/0.1 "
            f"(personal research project; contact: {self.contact_email})"
        )

    # --- normalization [CONFIG] ---
    ticker_match_confidence_threshold: float = 0.75

    # --- member selection [CONFIG] ---
    selection_method: str = "all"  # "all" | "volume" | "frequency" | "performance" | "manual"

    # --- scoring engine [CONFIG] (Phase 2, defined here so weights are versioned in one place) ---
    recency_half_life_days: int = 90
    overlap_window_days: int = 60
    composite_weight_performance: float = 0.35
    composite_weight_overlap: float = 0.30
    composite_weight_conviction: float = 0.20
    composite_weight_recency: float = 0.15

    # --- v1 scope ---
    stocks_only: bool = True


settings = Settings()
