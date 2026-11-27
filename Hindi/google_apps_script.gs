/**
 * @OnlyCurrentDoc
 * (Limits the permission Google asks for to just the sheet this script is attached to.)
 */

// KBC results collector: paste this into Google Apps Script (script.google.com)
// attached to a Google Sheet. It adds one row per finished game.

const COLS = ["time_ist", "name", "result", "questions_cleared",
              "amount_won", "lifelines_used", "duration_sec"];

// Stops a name like "=HYPERLINK(...)" from being treated as a spreadsheet formula
const safe = v => /^[=+\-@]/.test(String(v)) ? "'" + v : v;

function doPost(e) {
  try {
    const d = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    if (sheet.getLastRow() === 0) sheet.appendRow(COLS);
    sheet.appendRow([
      safe(String(d.time_ist || "").slice(0, 19)),
      safe(String(d.name || "").slice(0, 30)),
      safe(String(d.result || "").slice(0, 30)),
      Number(d.questions_cleared) || 0,
      Number(d.amount_won) || 0,
      Number(d.lifelines_used) || 0,
      Number(d.duration_sec) || 0
    ]);
    return ContentService.createTextOutput("ok");
  } catch (err) {
    return ContentService.createTextOutput("error");
  }
}
