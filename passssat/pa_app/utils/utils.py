from fastapi.templating import Jinja2Templates
import json
import os

templates = Jinja2Templates(directory="templates")


def tojson_pretty_filter(value, indent=2, ensure_ascii=False):
    if value is None:
        return ""
    if isinstance(
        value, str
    ):  # Jeśli już jest stringiem, spróbuj sparsować i sformatować
        try:
            return json.dumps(
                json.loads(value), indent=indent, ensure_ascii=ensure_ascii
            )
        except json.JSONDecodeError:
            return value  # Zwróć oryginalny string, jeśli nie jest JSONem
    return json.dumps(value, indent=indent, ensure_ascii=ensure_ascii)


templates.env.filters["tojson_pretty"] = tojson_pretty_filter
