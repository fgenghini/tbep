FALLBACK_MESSAGE = "An error occurred. Try again in a moment."


def format_fallback_message(error: Exception) -> str:
    return f"{FALLBACK_MESSAGE}\n\n{error}"
