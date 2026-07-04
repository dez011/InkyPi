import io
import logging

from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from PIL import Image

logger = logging.getLogger(__name__)

PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>InkyPi &middot; {{ config.device_id }}</title>
  <style>
    :root {
      --bg: #f4f5f7;
      --card: #ffffff;
      --text: #1a1d21;
      --muted: #6b7280;
      --border: #e5e7eb;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --ok: #16a34a;
      --err: #dc2626;
      --hint-bg: #eef2ff;
      --input-bg: #ffffff;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #111318;
        --card: #1b1e25;
        --text: #e7e9ee;
        --muted: #9aa1ad;
        --border: #2a2e37;
        --accent: #6366f1;
        --accent-hover: #818cf8;
        --hint-bg: #1e2233;
        --input-bg: #14161c;
      }
    }
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg); color: var(--text);
      max-width: 680px; margin: 0 auto; padding: 1.5rem 1rem 3rem;
    }
    header { display: flex; align-items: center; gap: 0.75rem; margin: 0.5rem 0 1.5rem; flex-wrap: wrap; }
    header h1 { font-size: 1.4rem; margin: 0; letter-spacing: -0.02em; }
    .badge {
      font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.6rem;
      border-radius: 999px; text-transform: uppercase; letter-spacing: 0.05em;
      background: var(--hint-bg); color: var(--accent);
    }
    .card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 1.25rem 1.25rem 1.5rem; margin-bottom: 1rem;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .card h2 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin: 0 0 1rem; }
    label { display: block; margin: 1rem 0 0.35rem; font-weight: 600; font-size: 0.9rem; }
    label:first-of-type { margin-top: 0; }
    input[type=text], input[type=number], input[type=time] {
      width: 100%; padding: 0.55rem 0.7rem; font-size: 0.95rem;
      border: 1px solid var(--border); border-radius: 8px;
      background: var(--input-bg); color: var(--text);
    }
    input:focus { outline: 2px solid var(--accent); outline-offset: -1px; border-color: transparent; }
    .row { display: flex; gap: 1rem; }
    .row > div { flex: 1; }
    .field-note { font-size: 0.8rem; color: var(--muted); margin-top: 0.3rem; }

    .toggle-row { display: flex; align-items: flex-start; gap: 0.9rem; margin-top: 1.25rem; }
    .toggle { position: relative; flex-shrink: 0; width: 46px; height: 26px; margin-top: 2px; }
    .toggle input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; inset: 0; border-radius: 999px;
      background: var(--border); transition: background 0.15s;
    }
    .slider:before {
      content: ""; position: absolute; height: 20px; width: 20px;
      left: 3px; top: 3px; border-radius: 50%; background: #fff;
      transition: transform 0.15s; box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .toggle input:checked + .slider { background: var(--accent); }
    .toggle input:checked + .slider:before { transform: translateX(20px); }
    .toggle-text b { font-size: 0.9rem; }
    .toggle-text div { font-size: 0.8rem; color: var(--muted); margin-top: 0.15rem; }

    .hint {
      background: var(--hint-bg); border-radius: 8px;
      padding: 0.75rem 0.9rem; margin-top: 1rem; font-size: 0.85rem; line-height: 1.6;
    }
    code {
      background: rgba(127,127,127,0.15); padding: 0.1rem 0.35rem;
      border-radius: 4px; font-size: 0.85em; word-break: break-all;
    }
    button {
      margin-top: 1.25rem; padding: 0.6rem 1.4rem; font-size: 0.95rem; font-weight: 600;
      color: #fff; background: var(--accent); border: none; border-radius: 8px; cursor: pointer;
    }
    button:hover { background: var(--accent-hover); }
    button.secondary { background: transparent; color: var(--accent); border: 1px solid var(--accent); margin-top: 0; }
    button.secondary:hover { background: var(--hint-bg); }

    .stat-grid { display: grid; grid-template-columns: auto 1fr; gap: 0.5rem 1.25rem; font-size: 0.9rem; }
    .stat-grid dt { color: var(--muted); }
    .stat-grid dd { margin: 0; }
    .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 0.4rem; vertical-align: middle; }
    .dot.ok { background: var(--ok); }
    .dot.err { background: var(--err); }
    .error-text { color: var(--err); }
  </style>
</head>
<body>
  <header>
    <h1>InkyPi</h1>
    <span class="badge">{{ config.device_id }}</span>
    <span class="badge">{{ config.mode }}</span>
  </header>

  <form method="post" action="{{ url_for('save') }}">
    <div class="card">
      <h2>Device</h2>

      <label for="device_id">Device ID</label>
      <input type="text" id="device_id" name="device_id" value="{{ config.device_id }}">
      <div class="field-note">How external senders (e.g. Home Assistant) identify this frame.</div>

      <div class="toggle-row">
        <label class="toggle" style="margin:0">
          <input type="checkbox" name="receiver_mode" {{ "checked" if config.mode == "receiver" else "" }}>
          <span class="slider"></span>
        </label>
        <div class="toggle-text">
          <b>Receiver mode</b>
          <div>Stop taking screenshots and wait for images pushed to this frame instead.</div>
        </div>
      </div>

      {% if config.mode == "receiver" %}
      <div class="hint">
        Push an image: <code>POST http://{{ request.host }}/api/display</code><br>
        (multipart field <code>image</code>, or a raw PNG/JPEG body)<br>
        Device info: <code>GET http://{{ request.host }}/api/info</code>
      </div>
      {% endif %}
    </div>

    <div class="card">
      <h2>Kiosk (screenshot) settings</h2>

      <label for="url">Screenshot URL</label>
      <input type="text" id="url" name="url" value="{{ config.url }}">

      <label for="refresh_interval_seconds">Refresh interval (seconds)</label>
      <input type="number" id="refresh_interval_seconds" name="refresh_interval_seconds" min="10" value="{{ config.refresh_interval_seconds }}">

      <label>Active hours</label>
      <div class="row">
        <div>
          <input type="time" name="active_start" value="{{ active_start }}">
          <div class="field-note">Start</div>
        </div>
        <div>
          <input type="time" name="active_end" value="{{ active_end }}">
          <div class="field-note">End</div>
        </div>
      </div>
      <div class="field-note">Leave both blank to run 24/7. Only applies to kiosk screenshots.</div>

      <button type="submit">Save</button>
    </div>
  </form>

  <div class="card">
    <h2>Status</h2>
    <dl class="stat-grid">
      <dt>Health</dt>
      <dd>
        {% if status.last_error %}
          <span class="dot err"></span><span class="error-text">{{ status.last_error }}</span>
        {% else %}
          <span class="dot ok"></span>OK
        {% endif %}
      </dd>
      <dt>Within active hours</dt>
      <dd>{{ "Yes" if is_active else "No" }}</dd>
      <dt>Last attempt</dt>
      <dd>{{ status.last_attempt_at or "never" }}</dd>
      <dt>Last success</dt>
      <dd>{{ status.last_success_at or "never" }}</dd>
    </dl>
    <form method="post" action="{{ url_for('refresh_now') }}" style="margin-top:1.25rem">
      <button type="submit" class="secondary">Refresh now</button>
    </form>
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
        config.config["mode"] = "receiver" if request.form.get("receiver_mode") else "kiosk"

        device_id = request.form.get("device_id", "").strip()
        if device_id:
            config.config["device_id"] = device_id

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

    @app.route("/api/info", methods=["GET"])
    def api_info():
        """Identity/state endpoint so an external system (Home Assistant) can
        discover and address this frame. Future per-frame configuration from
        the sender's side should build on this."""
        status = control.snapshot()
        return jsonify({
            "device_id": config.device_id,
            "mode": config.mode,
            "resolution": list(config.get_resolution()),
            "orientation": config.orientation,
            "last_attempt_at": str(status["last_attempt_at"]) if status["last_attempt_at"] else None,
            "last_success_at": str(status["last_success_at"]) if status["last_success_at"] else None,
            "last_error": status["last_error"],
        })

    @app.route("/api/display", methods=["POST"])
    def api_display():
        """Receives an image and queues it for display. Accepts either a
        multipart upload (field name "image") or a raw PNG/JPEG request body.
        Works in any mode - an explicit push always wins - but in receiver
        mode this is the only image source. Returns 202: the actual e-ink
        refresh takes ~30s and happens on the runner thread."""
        if "image" in request.files:
            data = request.files["image"].read()
        else:
            data = request.get_data()

        if not data:
            return jsonify({"error": "no image data - send multipart field 'image' or a raw image body"}), 400

        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except Exception as e:
            return jsonify({"error": f"could not decode image: {e}"}), 400

        logger.info(f"Received pushed image ({image.width}x{image.height}, {len(data)} bytes)")
        control.submit_image(image)
        return jsonify({"status": "accepted", "device_id": config.device_id}), 202

    return app
