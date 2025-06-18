import re
def remove_parentheses_content(text):
    """Remove all parentheses and their content from the text

Parameter:
Text (str): entered text

Return:
Str: Processed text"""

    # More accurate regular expressions to match parentheses and their contents
    result = re.sub(r'\（[^（）]*\）', '', text)  # Handling Chinese parentheses
    result = re.sub(r'\([^()]*\)', '', result)  # Handling English parentheses
    return result


