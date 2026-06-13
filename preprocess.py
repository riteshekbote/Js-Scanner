"""
Module: preprocess.py
Purpose: Extract all string literals from JS code
"""
import re

def extract_string_literals(js_code, max_len=8000):
    """Extract all strings from JS, combine and return"""
    pattern = re.compile(r'(["\'])(?:(?=(\\?))\2.)*?\1|`[^`]*`', re.DOTALL)
    matches = pattern.findall(js_code)

    literals = []
    for m in matches:
        if isinstance(m, tuple):
            s = m[0]
        else:
            s = m
        if len(s) >= 2 and s[0] in ('"', "'", '`'):
            s = s[1:-1]
        if len(s) > 4:
            literals.append(s)

    unique = list(set(literals))
    result = "\n".join(unique)

    if len(result) > max_len:
        result = result[:max_len] + "\n... (content too long, truncated)"
    return result
