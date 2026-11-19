"""The Apps Script reminder must produce exactly the same mail as tools.bootcamp_mail."""

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from tools.bootcamp_mail import reminder_mail
from tools.bootcamp_weather import SessionForecast, advice_for_session, parse_forecast

SCRIPT = Path("tools/google_apps_script/bootcamp_reminder.gs")
PAYLOAD = {"hourly": {"time": ["2026-11-24T15:00", "2026-11-24T16:00", "2026-11-24T17:00"],
                      "temperature_2m": [13, 11.5, 10], "precipitation_probability": [90, 40, 60]}}
NODE_RUNNER = """
const fs = require('fs'), vm = require('vm'); const ctx = {}; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), ctx);
const payload = JSON.parse(process.argv[2]);
const out = [ctx.parseForecast_(payload), {minTemperature: 15, maxRainProbability: 10}, null].map(f => {
  const m = ctx.buildReminder_({iso: '2026-11-24', day: 24, month: 11}, f); return [m.subject, m.body]; });
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_apps_script_reminder_matches_python():
    result = subprocess.run(["node", "-e", NODE_RUNNER, str(SCRIPT), json.dumps(PAYLOAD)],
                            capture_output=True, text=True, check=True)
    expected = []
    for forecast in (parse_forecast(PAYLOAD), SessionForecast(min_temperature_c=15, max_rain_probability=10), None):
        mail = reminder_mail(date(2026, 11, 24), advice_for_session(forecast), ["x@example.org"])
        expected.append([mail.subject, mail.body])
    assert json.loads(result.stdout) == expected


MIME_RUNNER = """
const fs = require('fs'), vm = require('vm');
const b64 = (s, safe) => { const x = Buffer.from(s, 'utf8').toString(safe ? 'base64url' : 'base64'); return x; };
const ctx = {Utilities: {Charset: {UTF_8: 'utf8'}, base64Encode: s => b64(s, false), base64EncodeWebSafe: s => b64(s, true)}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), ctx);
console.log(ctx.rawMessage_('tim@example.org', ['a@example.org', 'b@example.org'], 'Reminder: beweegsessie', 'Tot morgen! 💪'));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_participants_only_in_bcc_and_text_survives_encoding():
    import base64
    import email
    import email.policy

    raw = subprocess.run(["node", "-e", MIME_RUNNER, str(SCRIPT)], capture_output=True, text=True, check=True).stdout.strip()
    message = email.message_from_bytes(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)), policy=email.policy.default)
    assert message["To"] == "tim@example.org"
    assert message["Bcc"] == "a@example.org, b@example.org"
    assert message["Subject"] == "Reminder: beweegsessie"
    assert message.get_content().strip() == "Tot morgen! 💪"


def test_script_never_uses_full_gmail_access():
    for gs in Path("tools/google_apps_script").glob("*.gs"):
        code = "\n".join(line for line in gs.read_text().splitlines() if not line.lstrip().startswith("*"))
        assert "GmailApp" not in code and "MailApp" not in code
    scopes = json.loads(Path("tools/google_apps_script/appsscript.json").read_text())["oauthScopes"]
    assert "https://mail.google.com/" not in scopes
    assert "https://www.googleapis.com/auth/gmail.compose" in scopes
