import os

from dotenv import load_dotenv
from flask import Flask, flash, get_flashed_messages, redirect, render_template_string, request, url_for

from config import cfg

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
FLASK_BASE_URL = os.environ["FLASK_BASE_URL"].strip()

if not FLASK_BASE_URL.startswith("/"):
    FLASK_BASE_URL = f"/{FLASK_BASE_URL}"
FLASK_BASE_URL = FLASK_BASE_URL.rstrip("/")


def with_base_url(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    if path == FLASK_BASE_URL or path.startswith(f"{FLASK_BASE_URL}/"):
        return path
    return f"{FLASK_BASE_URL}{path}"

PAGE_TEMPLATE = """
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Config Admin</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; max-width: 900px; }
      h1 { margin-bottom: 20px; }
      .row { border: 1px solid #ddd; border-radius: 6px; padding: 12px; margin-bottom: 10px; }
      .key { font-family: monospace; font-weight: 700; }
      .desc { color: #444; margin: 6px 0 8px; }
      input[type=text] { width: 100%; padding: 8px; box-sizing: border-box; }
      button { padding: 10px 16px; }
      .msg { padding: 10px; border-radius: 6px; margin-bottom: 16px; }
      .ok { background: #e8f7e8; border: 1px solid #96cc96; }
      .err { background: #fdecec; border: 1px solid #e0a0a0; }
    </style>
  </head>
  <body>
    <h1>Configuration</h1>
    {% if message %}
      <div class="msg {{ message_type }}">{{ message }}</div>
    {% endif %}
    <form method="post">
      {% for item in items %}
        <div class="row">
          <div class="key">{{ item.key }}</div>
          <div class="desc">{{ item.description }}</div>
          <input type="text" name="{{ item.key }}" value="{{ item.value }}" />
        </div>
      {% endfor %}
      <button type="submit">Sauvegarder</button>
    </form>
  </body>
</html>
"""


def _display_value(value):
    if value is None:
        return "null"
    return str(value)


def _parse_value(raw_value: str, previous_value):
    if isinstance(previous_value, bool):
        lowered = raw_value.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
        raise ValueError(f"Invalid boolean value: {raw_value}")
    if isinstance(previous_value, int):
        return int(raw_value)
    if previous_value is None:
        stripped = raw_value.strip().lower()
        if stripped in ("", "null", "none"):
            return None
        return raw_value
    return raw_value


@app.route(with_base_url("/"), methods=["GET", "POST"])
def index():
    data = cfg.as_dict()
    descriptions = cfg.descriptions()

    if request.method == "POST":
        new_data = {}
        try:
            for key, old_value in data.items():
                raw_value = request.form.get(key)
                if raw_value is None:
                    raise KeyError(f"Missing field in form: {key}")
                new_data[key] = _parse_value(raw_value, old_value)
            cfg.save_all(new_data)
            flash("Configuration sauvegardee.", "ok")
            return redirect(with_base_url(url_for("index")))
        except Exception as exc:
            flash(f"Erreur de sauvegarde: {exc}", "err")
            data = new_data or data

    flashed = get_flashed_messages(with_categories=True)
    message = None
    message_type = "ok"
    if flashed:
        message_type, message = flashed[-1]
        if message_type == "ok":
            data = cfg.as_dict()

    items = [
        {
            "key": key,
            "description": descriptions.get(key, "Aucune description."),
            "value": _display_value(value),
        }
        for key, value in sorted(data.items())
    ]
    return render_template_string(
        PAGE_TEMPLATE,
        items=items,
        message=message,
        message_type=message_type,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
