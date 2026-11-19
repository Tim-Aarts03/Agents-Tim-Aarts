/**
 * Clears the bootcamp sign-up form every Tuesday evening, so the same link can
 * be sent again next week. Runs inside Tim's own Google Form (bound script);
 * Claude has no access to the form.
 *
 * Before deleting, all responses are mailed to Tim himself as an archive,
 * because deleting form responses cannot be undone. Mailing reuses the
 * compose-only Gmail permission (rawMessage_ and myAddress_ live in
 * bootcamp_reminder.gs), so no access to Tim's spreadsheets or Drive is needed.
 *
 * Functions Tim runs by hand (once):
 *   installTrigger()  - schedule clearResponses() every Tuesday ~20:00 (Amsterdam)
 *   dryRun()          - only logs what would be archived and deleted
 */

var CLEAR_TIMEZONE = 'Europe/Amsterdam';
var CLEAR_HOUR = 20;
var CLEAR_TUESDAY = 2; // ISO day number (Monday = 1)

function clearResponses() {
  // Guard against an accidental manual run or a wrongly configured trigger.
  if (Number(Utilities.formatDate(new Date(), CLEAR_TIMEZONE, 'u')) !== CLEAR_TUESDAY) {
    Logger.log('Not Tuesday in Amsterdam: nothing deleted.');
    return;
  }
  var form = FormApp.getActiveForm();
  var responses = form.getResponses();
  if (responses.length === 0) {
    Logger.log('No responses: nothing to do.');
    return;
  }
  var me = myAddress_();
  var today = Utilities.formatDate(new Date(), CLEAR_TIMEZONE, 'yyyy-MM-dd');
  // Archive first; if sending fails, the exception stops the run before anything is deleted.
  Gmail.Users.Messages.send({ raw: rawMessage_(me, [], archiveSubject_(today, responses.length),
    archiveBody_(responseRows_(responses))) }, 'me');
  form.deleteAllResponses();
  form.setAcceptingResponses(true);
  Logger.log('Archived (mail to ' + me + ') and deleted ' + responses.length + ' response(s).');
}

function dryRun() {
  var responses = FormApp.getActiveForm().getResponses();
  Logger.log(responses.length + ' response(s) would be archived and deleted.\n\n' + archiveBody_(responseRows_(responses)));
}

function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (trigger.getHandlerFunction() === 'clearResponses') {
      ScriptApp.deleteTrigger(trigger); // avoid double runs when installed twice
    }
  });
  ScriptApp.newTrigger('clearResponses')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.TUESDAY)
    .atHour(CLEAR_HOUR)
    .inTimezone(CLEAR_TIMEZONE)
    .create();
  Logger.log('Trigger installed: every Tuesday around ' + CLEAR_HOUR + ':00 (' + CLEAR_TIMEZONE + ').');
}

/** One row per response: sign-up time followed by every answer. */
function responseRows_(responses) {
  return responses.map(function (response) {
    var row = [Utilities.formatDate(response.getTimestamp(), CLEAR_TIMEZONE, 'dd-MM-yyyy HH:mm')];
    response.getItemResponses().forEach(function (itemResponse) {
      row.push(String(itemResponse.getResponse()));
    });
    return row;
  });
}

function archiveSubject_(isoDay, count) {
  return 'Archief bootcamp ' + isoDay + ' (' + count + ' aanmeldingen)';
}

function archiveBody_(rows) {
  var lines = ['Aanmeldingen voor de bootcamp van vandaag. Het formulier is daarna leeggemaakt.', ''];
  rows.forEach(function (row, i) {
    lines.push((i + 1) + '. ' + row.join(' | '));
  });
  return lines.join('\n');
}
