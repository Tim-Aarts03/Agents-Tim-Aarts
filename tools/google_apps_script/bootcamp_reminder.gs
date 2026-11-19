/**
 * Monday reminder for everyone who signed up for Tuesday's bootcamp.
 * Runs inside Tim's own Google Form (same project as clear_bootcamp_responses.gs),
 * so participant addresses never leave Tim's Google account.
 *
 * Text and weather rules mirror tools/bootcamp_mail.py (reminder_mail) and
 * tools/bootcamp_weather.py: keep them in sync when either changes.
 *
 * Phase 1: REMINDER_SEND_AUTOMATICALLY = false -> Gmail draft (participants in BCC)
 * plus a note to Tim. Only switch to true after Tim approves automatic sending
 * (needs a CLAUDE.md change).
 *
 * Functions Tim runs by hand (once):
 *   installReminderTrigger()  - schedule createReminder() every Monday ~12:45 (Amsterdam)
 *   reminderDryRun()          - log the mail that would be made; nothing is drafted or sent
 */

var REMINDER_SEND_AUTOMATICALLY = false;
var REMINDER_TIMEZONE = 'Europe/Amsterdam';
var REMINDER_HOUR = 12;
var REMINDER_MINUTE = 45;
var REMINDER_MONDAY = 1; // ISO day number
var REMINDER_SESSION_TIME = '16:15';
var REMINDER_MAX_PARTICIPANTS = 12;
var REMINDER_LAST_RUN_KEY = 'reminderLastRunDate';

// Hof van Jacob, Haarlem; same values as tools/bootcamp_weather.py.
var WEATHER_LATITUDE = 52.38;
var WEATHER_LONGITUDE = 4.64;
var WEATHER_SESSION_HOURS = [16, 17];
var WEATHER_COLD_BELOW_C = 12.0;
var WEATHER_RAIN_PROBABILITY_PERCENT = 50;

var MONTHS_NL = ['januari', 'februari', 'maart', 'april', 'mei', 'juni',
  'juli', 'augustus', 'september', 'oktober', 'november', 'december'];
var EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function createReminder() {
  var today = Utilities.formatDate(new Date(), REMINDER_TIMEZONE, 'yyyy-MM-dd');
  // Guards: only on Mondays, and at most once per Monday (no double drafts or mails).
  if (Number(Utilities.formatDate(new Date(), REMINDER_TIMEZONE, 'u')) !== REMINDER_MONDAY) {
    Logger.log('Not Monday in Amsterdam: no reminder.');
    return;
  }
  var props = PropertiesService.getScriptProperties();
  if (props.getProperty(REMINDER_LAST_RUN_KEY) === today) {
    Logger.log('Reminder already made today.');
    return;
  }
  var recipients = signedUpEmails_();
  if (recipients.length === 0) {
    Logger.log('Nobody signed up: no reminder.');
    return;
  }
  var session = tomorrow_();
  var forecast = fetchForecast_(session.iso);
  var mail = buildReminder_(session, forecast);
  var me = Session.getEffectiveUser().getEmail();
  var options = { bcc: recipients.join(','), name: 'Tim Aarts' };

  if (REMINDER_SEND_AUTOMATICALLY) {
    GmailApp.sendEmail(me, mail.subject, mail.body, options);
  } else {
    GmailApp.createDraft(me, mail.subject, mail.body, options);
  }
  props.setProperty(REMINDER_LAST_RUN_KEY, today);
  GmailApp.sendEmail(me, noteSubject_(recipients.length), noteBody_(recipients.length, forecast));
}

function reminderDryRun() {
  var recipients = signedUpEmails_();
  var session = tomorrow_();
  var mail = buildReminder_(session, fetchForecast_(session.iso));
  Logger.log(recipients.length + ' participant(s).\nSubject: ' + mail.subject + '\n\n' + mail.body);
}

function installReminderTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (trigger.getHandlerFunction() === 'createReminder') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  ScriptApp.newTrigger('createReminder')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY)
    .atHour(REMINDER_HOUR)
    .nearMinute(REMINDER_MINUTE)
    .inTimezone(REMINDER_TIMEZONE)
    .create();
  Logger.log('Trigger installed: every Monday around ' + REMINDER_HOUR + ':' + REMINDER_MINUTE + ' (' + REMINDER_TIMEZONE + ').');
}

function signedUpEmails_() {
  var seen = {};
  var emails = [];
  FormApp.getActiveForm().getResponses().forEach(function (response) {
    var email = response.getRespondentEmail();
    if (!email) {
      response.getItemResponses().forEach(function (itemResponse) {
        if (/e-?mail/i.test(itemResponse.getItem().getTitle())) {
          email = String(itemResponse.getResponse());
        }
      });
    }
    email = String(email || '').trim().toLowerCase();
    if (EMAIL_PATTERN.test(email) && !seen[email]) {
      seen[email] = true;
      emails.push(email);
    }
  });
  return emails;
}

function tomorrow_() {
  var date = new Date(Date.now() + 24 * 60 * 60 * 1000);
  return {
    iso: Utilities.formatDate(date, REMINDER_TIMEZONE, 'yyyy-MM-dd'),
    day: Number(Utilities.formatDate(date, REMINDER_TIMEZONE, 'd')),
    month: Number(Utilities.formatDate(date, REMINDER_TIMEZONE, 'M'))
  };
}

/** Returns {minTemperature, maxRainProbability}, or null when the forecast is unavailable. */
function fetchForecast_(isoDay) {
  var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + WEATHER_LATITUDE +
    '&longitude=' + WEATHER_LONGITUDE +
    '&hourly=temperature_2m,precipitation_probability&timezone=Europe%2FAmsterdam' +
    '&start_date=' + isoDay + '&end_date=' + isoDay;
  try {
    var response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    if (response.getResponseCode() !== 200) {
      return null;
    }
    return parseForecast_(JSON.parse(response.getContentText()));
  } catch (e) {
    return null;
  }
}

function parseForecast_(payload) {
  var hourly = payload.hourly;
  var temps = [];
  var rains = [];
  for (var i = 0; i < hourly.time.length; i++) {
    var hour = Number(hourly.time[i].substring(11, 13));
    if (WEATHER_SESSION_HOURS.indexOf(hour) !== -1) {
      temps.push(hourly.temperature_2m[i]);
      rains.push(hourly.precipitation_probability[i] || 0);
    }
  }
  if (temps.length === 0) {
    return null;
  }
  return { minTemperature: Math.min.apply(null, temps), maxRainProbability: Math.max.apply(null, rains) };
}

function weatherLines_(forecast) {
  var lines = [];
  if (!forecast) {
    return lines;
  }
  if (forecast.minTemperature < WEATHER_COLD_BELOW_C) {
    lines.push('Het wordt fris, dus trek warme kleding aan.');
  }
  if (forecast.maxRainProbability >= WEATHER_RAIN_PROBABILITY_PERCENT) {
    lines.push('Bij regen gaan we naar het overdekte balkon van team 2.');
  }
  return lines;
}

function buildReminder_(session, forecast) {
  var parts = [
    '!Reminder!',
    'Wat leuk dat jij je hebt aangemeld voor de beweegsessie van morgen.\nVergeet je sportspullen niet mee te nemen.'
  ];
  var weather = weatherLines_(forecast);
  if (weather.length > 0) {
    parts.push(weather.join('\n'));
  }
  parts.push('Tot morgen!', 'Met vriendelijke groet,\nTim Aarts');
  return {
    subject: 'Reminder: beweegsessie morgen (' + session.day + ' ' + MONTHS_NL[session.month - 1] + ') om ' + REMINDER_SESSION_TIME,
    body: parts.join('\n\n')
  };
}

function noteSubject_(count) {
  return REMINDER_SEND_AUTOMATICALLY
    ? 'Bootcamp-reminder verstuurd (' + count + ' deelnemers)'
    : 'Bootcamp-reminder staat klaar in Concepten (' + count + ' deelnemers)';
}

function noteBody_(count, forecast) {
  var lines = [];
  lines.push(REMINDER_SEND_AUTOMATICALLY
    ? 'De reminder is verstuurd naar ' + count + ' deelnemer(s) (BCC).'
    : 'De reminder voor ' + count + ' deelnemer(s) staat in Gmail bij Concepten. Controleer hem en klik op Verzenden.');
  if (!forecast) {
    lines.push('Let op: de weersverwachting was niet beschikbaar, dus er staat geen weeradvies in de mail.');
  }
  if (count > REMINDER_MAX_PARTICIPANTS) {
    lines.push('Let op: meer dan ' + REMINDER_MAX_PARTICIPANTS + ' aanmeldingen.');
  }
  return lines.join('\n\n');
}
