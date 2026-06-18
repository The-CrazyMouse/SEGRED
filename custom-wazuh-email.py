#!/usr/bin/env python3
import sys
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

''' 
Caminho do ficheiro na máquina virtual: /var/ossec/integrations/custom-wazuh-email.py
'''

alert_file = sys.argv[1]

with open(alert_file) as f:
    alert = json.load(f)

rule = alert.get("rule", {})
agent = alert.get("agent", {})
data = alert.get("data", {})
decoder = alert.get("decoder", {})

subject = f"[WAZUH] {rule.get('level','N/A')} - {rule.get('description','Alert')}"

body_html = f"""<html>
<body>
<h3>WAZUH ALERT</h3>
<p><b>Rule:</b> {rule.get('id')}</p>
<p><b>Description:</b> {rule.get('description')}</p>
<p><b>Agent:</b> {agent.get('name')}</p>
</body>
</html>"""

SMTP_SERVER = "127.0.0.1"
SMTP_PORT = 25

FROM_EMAIL = "wazuh@localhost"
TO_EMAIL = "luismiguelpaiva70@gmail.com"

msg = MIMEMultipart("alternative")
msg["From"] = FROM_EMAIL
msg["To"] = TO_EMAIL
msg["Subject"] = subject

msg.attach(MIMEText("Wazuh Alert", "plain"))
msg.attach(MIMEText(body_html, "html", "utf-8"))

server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
server.quit()