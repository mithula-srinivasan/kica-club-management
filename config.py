import os

# "production" on Render. Anything else (or not set) means your Mac.
APP_ENV = os.getenv("APP_ENV", "development")
IS_PRODUCTION = APP_ENV == "production"


def setting(name: str, default: str | None = None) -> str | None:
    """Read a setting from the environment (or .env).

    On your Mac, a missing setting uses the default.
    In production, a missing setting stops the app from starting,
    so a mistake is noticed straight away instead of causing strange bugs.
    """
    value = os.getenv(name)

    if value:
        return value

    if IS_PRODUCTION:
        raise RuntimeError(
            f"The {name} setting is missing. Add it in Render's Environment settings."
        )

    return default