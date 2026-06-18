# server.py
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
TICKETS_FILE = "tickets.json"


def load_tickets():
    if not os.path.exists(TICKETS_FILE):
        return []
    with open(TICKETS_FILE, "r") as f:
        return json.load(f)


def save_all(tickets):
    with open(TICKETS_FILE, "w") as f:
        json.dump(tickets, f, indent=2)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400

    tickets = load_tickets()
    now = datetime.now()

    ticket = {
        "id": now.strftime("%Y%m%d%H%M%S%f"),
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "rule": data.get("rule", {}).get("description", "Unknown"),
        "level": data.get("rule", {}).get("level", 0),
        "agent": data.get("agent", {}).get("name", "Unknown"),
        "ip": data.get("data", {}).get("srcip", "Unknown"),
        "status": "Novo",
    }

    tickets.append(ticket)
    save_all(tickets)
    return jsonify({"status": "ok", "ticket": ticket}), 200


@app.route("/tickets", methods=["GET"])
def get_tickets():
    return jsonify(load_tickets())


@app.route("/tickets/<ticket_id>/status", methods=["POST"])
def update_status(ticket_id):
    new_status = request.json.get("status")
    if new_status not in ["Novo", "Em Análise", "Fechado"]:
        return jsonify({"error": "invalid status"}), 400

    tickets = load_tickets()
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = new_status
            save_all(tickets)
            return jsonify({"status": "ok"}), 200
    return jsonify({"error": "not found"}), 404


@app.route("/check-new", methods=["GET"])
def check_new():
    tickets = load_tickets()
    now = datetime.now()
    recent = []
    for t in tickets:
        t_time = datetime.strptime(t["timestamp"], "%Y-%m-%d %H:%M:%S")
        if now - t_time <= timedelta(seconds=3):
            recent.append(t)
    return jsonify({"new": len(recent) > 0, "tickets": recent})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
