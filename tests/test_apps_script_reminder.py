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
