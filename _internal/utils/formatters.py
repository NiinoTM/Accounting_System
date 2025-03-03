import unicodedata

def normalize_text(text):
    """Convert text to lowercase and remove accents."""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

def format_table_name(table_name):
    """Convert snake_case to Title Case with spaces and handle ID formatting."""
    # First handle the special case of 'id' as a standalone field
    if table_name.lower() == 'id':
        return 'ID'
    
    # Replace underscores with spaces
    name = table_name.replace('_', ' ')
    
    # Remove ' id' if it exists at the end (case insensitive)
    if name.lower().endswith(' id'):
        name = name[:-3]
    
    # Split into words and capitalize each one
    words = name.split()
    formatted = ' '.join(word.capitalize() for word in words)
    
    return formatted or 'ID'  # Return 'ID' if string becomes empty
