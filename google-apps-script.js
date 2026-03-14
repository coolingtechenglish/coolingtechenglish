// ============================================
// Google Apps Script — Paste this into your Apps Script editor
// 部署為 Web App 後，將 URL 貼到 index.html 的 APPS_SCRIPT_URL
//
// 設定步驟:
// 1. 建立 Google Sheet，欄位: Name | Email | StartDate | Active
// 2. 前往 Extensions > Apps Script
// 3. 貼上此程式碼
// 4. 部署 > New deployment > Web app
//    - Execute as: Me
//    - Who has access: Anyone
// 5. 複製 Web App URL，貼到 index.html 的 APPS_SCRIPT_URL
// ============================================

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    // Check if email already exists
    var emails = sheet.getRange(2, 2, Math.max(sheet.getLastRow() - 1, 1), 1).getValues();
    for (var i = 0; i < emails.length; i++) {
      if (emails[i][0] === data.email) {
        // Update existing row
        sheet.getRange(i + 2, 3).setValue(data.startDate);
        sheet.getRange(i + 2, 4).setValue('TRUE');
        return ContentService.createTextOutput(
          JSON.stringify({ status: 'updated', message: 'Challenge restarted' })
        ).setMimeType(ContentService.MimeType.JSON);
      }
    }

    // Add new row
    sheet.appendRow([data.name, data.email, data.startDate, 'TRUE']);

    return ContentService.createTextOutput(
      JSON.stringify({ status: 'ok', message: 'Registered successfully' })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: 'error', message: err.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(
    JSON.stringify({ status: 'ok', message: 'TechPulse 21-Day Challenge API' })
  ).setMimeType(ContentService.MimeType.JSON);
}
