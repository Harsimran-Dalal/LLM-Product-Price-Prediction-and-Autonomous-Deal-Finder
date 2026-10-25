"""Helpers for presenting agent log messages in the Gradio UI."""

COLORS = {
    "\033[40m\033[31m": "#dd0000",
    "\033[40m\033[32m": "#00dd00",
    "\033[40m\033[33m": "#dddd00",
    "\033[40m\033[34m": "#0000ee",
    "\033[40m\033[35m": "#aa00dd",
    "\033[40m\033[36m": "#00dddd",
    "\033[40m\033[37m": "#87CEEB",
    "\033[44m\033[37m": "#ff7800",
}
RESET = "\033[0m"


def reformat(message: str) -> str:
    for ansi, color in COLORS.items():
        message = message.replace(ansi, f'<span style="color: {color}">')
    return message.replace(RESET, "</span>")

