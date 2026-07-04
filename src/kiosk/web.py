import logging

from flask import Flask, redirect, render_template_string, request, url_for

logger = logging.getLogger(__name__)

PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
  <title>InkyPi Kiosk</title>
  <style>
    body { font-family: sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
    label { display: block; margin-top: 1rem; font-weight: bold; }
    input[type=text] { width: 100%; padding: 0.4rem; box-sizing: border-box; }
    .row { display: flex; gap: 1rem; }
    .row > div { flex: 1; }
    button { margin-top: 1.5rem; padding: 0.6rem 1.2rem; font-size: 1rem; }
    .stats { background: #f2f2f2; padding: 1rem; border-radius: 6px; margin-top: 2rem; }
    .error { color: #b00020; }
    .ok { color: #1a7f37; }
  </style>
</head>
<body>
  <h1>InkyPi Kiosk</h1>

  <form method="post" action="{{ url_for('save') }}">
    <label for="url">Screenshot URL</label>
    <input type="text" id="url" name="url" value="{{ config.url }}">

    <label for="refresh_interval_seconds">Refresh interval (seconds)</label>
    <input type="text" id="refresh_interval_seconds" name="refresh_interval_seconds" value="{{ config.refresh_interval_seconds }}">

    <label>Active hours (leave both blank to run 24/7)</label>
    <div class="row">
      <div>
        <label for="active_start">Start</label>
        <input type="text" id="active_start" name="active_start" placeholder="HH:MM" value="{{ active_start }}">
      </div>
      <div>
        <label for="active_end">End</label>
        <input type="text" id="active_end" name="active_end" placeholder="HH:MM" value="{{ active_end }}">
      </div>
    </div>

    <button type="submit">Save</button>
  </form>

  <form method="post" action="{{ url_for('refresh_now') }}">
    <button type="submit">Refresh now</button>
  </form>

  <div class="stats">
    <div>Currently within active hours: {{ "yes" if is_active else "no" }}</div>
    <div>Last attempt: {{ status.last_attempt_at or "never" }}</div>
    <div>Last successful refresh: {{ status.last_success_at or "never" }}</div>
    {% if status.last_error %}
      <div class="error">Last error: {{ status.last_error }}</div>
    {% else %}
      <div class="ok">No errors on last attempt</div>
    {% endif %}
  </div>
</body>
</html>
"""


def create_app(config, control):
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def index():
        active_hours = config.active_hours or {}
        return render_template_string(
            PAGE_TEMPLATE,
            config=config,
            active_start=active_hours.get("start", ""),
            active_end=active_hours.get("end", ""),
            is_active=config.is_active_now(),
            status=control.snapshot(),
        )

    @app.route("/save", methods=["POST"])
    def save():
        config.config["url"] = request.form.get("url", config.url).strip()

        try:
            config.config["refresh_interval_seconds"] = int(request.form.get("refresh_interval_seconds"))
        except (TypeError, ValueError):
            pass

        start = request.form.get("active_start", "").strip()
        end = request.form.get("active_end", "").strip()
        config.config["active_hours"] = {"start": start, "end": end} if start and end else None

        config.save()
        control.notify_config_changed()
        return redirect(url_for("index"))

    @app.route("/refresh", methods=["POST"])
    def refresh_now():
        control.request_refresh()
        return redirect(url_for("index"))

    return app
