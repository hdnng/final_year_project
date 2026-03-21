def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        return f"<style>{f.read()}</style>"