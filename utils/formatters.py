import unicodedata

def normalize_text(text):
    """Convert text to lowercase and remove accents."""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

def format_table_name(table_name):
    """Convert snake_case to Title Case with spaces."""
    # Replace underscores with spaces and title case each word
    words = table_name.replace('_', ' ').split()
    return ' '.join(word.capitalize() for word in words)
