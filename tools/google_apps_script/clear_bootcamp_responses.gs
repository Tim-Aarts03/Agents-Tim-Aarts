/**
 * Clears the bootcamp sign-up form every Tuesday evening, so the same link can
 * be sent again next week. Runs inside Tim's own Google Form (bound script);
 * Claude has no access to the form.
 *
 * Before deleting, every response is copied to the Google Sheet
 * "Bootcamp aanmeldingen archief" in Tim's Drive, because deleting form
 * responses cannot be undone.
 *
 * Functions Tim runs by hand (once):
 *   installTrigger()  - schedule clearResponses() every Tuesday ~20:00 (Amsterdam)
 *   dryRun()          - only logs how many responses would be archived and deleted
 */

var ARCHIVE_NAME = 'Bootcamp aanmeldingen archief';
var ARCHIVE_ID_KEY = 'archiveSpreadsheetId';
var TIMEZONE = 'Europe/Amsterdam';
var RUN_HOUR = 20;
var TUESDAY = 2; // ISO day number (Monday = 1)

function clearResponses() {
  // Guard against an accidental manual run or a wrongly configured trigger.
  if (!isTuesdayInAmsterdam_()) {
    Logger.log('Not Tuesday in Amsterdam: nothing deleted.');
    return;
  }
  var form = FormApp.getActiveForm();
  var responses = form.getResponses();
  if (responses.length === 0) {
    Logger.log('No responses: nothing to do.');
    return;
  }
  archive_(form, responses);
  form.deleteAllResponses();
  form.setAcceptingResponses(true);
  Logger.log('Archived and deleted ' + responses.length + ' response(s).');
}

function dryRun() {
  var count = FormApp.getActiveForm().getResponses().length;
  Logger.log(count + ' response(s) would be archived and deleted. Today is Tuesday: ' + isTuesdayInAmsterdam_());
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
    .atHour(RUN_HOUR)
    .inTimezone(TIMEZONE)
    .create();
  Logger.log('Trigger installed: every Tuesday around ' + RUN_HOUR + ':00 (' + TIMEZONE + ').');
}

function archive_(form, responses) {
  var sheet = archiveSheet_(form);
  var session = Utilities.formatDate(new Date(), TIMEZONE, 'yyyy-MM-dd');
  var rows = responses.map(function (response) {
    var row = [session, Utilities.formatDate(response.getTimestamp(), TIMEZONE, 'yyyy-MM-dd HH:mm')];
    response.getItemResponses().forEach(function (itemResponse) {
      row.push(String(itemResponse.getResponse()));
    });
    return row;
  });
  var width = Math.max.apply(null, rows.map(function (r) { return r.length; }));
  rows = rows.map(function (r) { while (r.length < width) { r.push(''); } return r; });
  sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, width).setValues(rows);
}

function archiveSheet_(form) {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty(ARCHIVE_ID_KEY);
  if (id) {
    return SpreadsheetApp.openById(id).getSheets()[0];
  }
  var spreadsheet = SpreadsheetApp.create(ARCHIVE_NAME);
  var header = ['Bootcampdatum', 'Aangemeld op'];
  form.getItems().forEach(function (item) { header.push(item.getTitle()); });
  spreadsheet.getSheets()[0].appendRow(header);
  props.setProperty(ARCHIVE_ID_KEY, spreadsheet.getId());
  return spreadsheet.getSheets()[0];
}

function isTuesdayInAmsterdam_() {
  return Number(Utilities.formatDate(new Date(), TIMEZONE, 'u')) === TUESDAY;
}
