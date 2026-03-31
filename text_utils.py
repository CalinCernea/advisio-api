"""
ADVISIO — Utilitar curățare text pentru ReportLab
===================================================
Fontul Helvetica standard din ReportLab nu suportă diacritice românești.
Această funcție înlocuiește toate diacriticele cu variante ASCII.
"""

def clean(text: str) -> str:
    """Înlocuiește diacritice românești cu variante fără diacritic."""
    if not text:
        return text
    replacements = {
        'ă': 'a', 'Ă': 'A',
        'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I',
        'ș': 's', 'Ș': 'S',
        'ț': 't', 'Ț': 'T',
        # variante cu virgulă în loc de sedilă (des confundate)
        'ş': 's', 'Ş': 'S',
        'ţ': 't', 'Ţ': 'T',
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def c(text) -> str:
    """Alias scurt pentru clean() — pentru folosire inline."""
    if isinstance(text, str):
        return clean(text)
    return text


def clean_list(lst: list) -> list:
    """Curăță diacriticele dintr-o listă de string-uri."""
    return [clean(item) if isinstance(item, str) else item for item in lst]


def clean_dict(d: dict) -> dict:
    """Curăță recursiv diacriticele din toate valorile unui dict."""
    result = {}
    for key, value in d.items():
        if isinstance(value, str):
            result[key] = clean(value)
        elif isinstance(value, list):
            result[key] = _clean_list_deep(value)
        elif isinstance(value, dict):
            result[key] = clean_dict(value)
        elif isinstance(value, tuple):
            result[key] = tuple(clean(v) if isinstance(v, str) else v for v in value)
        else:
            result[key] = value
    return result


def _clean_list_deep(lst) -> list:
    """Curăță recursiv diacriticele dintr-o listă (inclusiv liste imbricate)."""
    result = []
    for item in lst:
        if isinstance(item, str):
            result.append(clean(item))
        elif isinstance(item, list):
            result.append(_clean_list_deep(item))
        elif isinstance(item, dict):
            result.append(clean_dict(item))
        elif isinstance(item, tuple):
            result.append(tuple(clean(v) if isinstance(v, str) else v for v in item))
        else:
            result.append(item)
    return result
