import unicodedata

def normalize_text(text):
    """Convert text to lowercase and remove accents."""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')
