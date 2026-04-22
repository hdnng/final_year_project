"""CSS loader for Streamlit pages."""


def load_css(file_path: str) -> str:
    """Read a CSS file and wrap it in a <style> tag for Streamlit injection."""
    with open(file_path, encoding="utf-8") as f:
        return f"<style>{f.read()}</style>"