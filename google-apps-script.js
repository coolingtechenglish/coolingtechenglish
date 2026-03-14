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
// 6. 在 Apps Script 編輯器中，設定 sendDailyReminders 的每日觸發器
//    - Triggers > Add Trigger > sendDailyReminders > Time-driven > Day timer > 8am-9am
// ============================================

var SITE_URL = 'https://coolingtechenglish.github.io/coolingtechenglish/';

// ---- Web App Endpoints ----

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
  // Check if an email is already registered
  var checkEmail = e && e.parameter && e.parameter.check;
  if (checkEmail) {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      var data = sheet.getRange(2, 1, lastRow - 1, 4).getValues();
      for (var i = 0; i < data.length; i++) {
        if (String(data[i][1]).toLowerCase().trim() === checkEmail.toLowerCase().trim()) {
          return ContentService.createTextOutput(
            JSON.stringify({
              exists: true,
              name: data[i][0],
              startDate: data[i][2] instanceof Date
                ? data[i][2].toISOString().split('T')[0]
                : String(data[i][2]),
              active: String(data[i][3]).toUpperCase() === 'TRUE'
            })
          ).setMimeType(ContentService.MimeType.JSON);
        }
      }
    }
    return ContentService.createTextOutput(
      JSON.stringify({ exists: false })
    ).setMimeType(ContentService.MimeType.JSON);
  }

  return ContentService.createTextOutput(
    JSON.stringify({ status: 'ok', message: 'TechPulse 21-Day Challenge API' })
  ).setMimeType(ContentService.MimeType.JSON);
}

// ---- Daily Email Reminders (replaces EmailJS + Python) ----
// Set up a daily trigger: Triggers > Add Trigger > sendDailyReminders
// Time-driven > Day timer > 8am to 9am (Taiwan time)

function sendDailyReminders() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    Logger.log('No subscribers found.');
    return;
  }

  var data = sheet.getRange(2, 1, lastRow - 1, 4).getValues();
  // Columns: 0=Name, 1=Email, 2=StartDate, 3=Active

  var today = new Date();
  var sent = 0;
  var skipped = 0;

  for (var i = 0; i < data.length; i++) {
    var name = data[i][0] || 'Learner';
    var email = data[i][1];
    var startDate = data[i][2];
    var active = String(data[i][3]).toUpperCase();

    if (!email || active !== 'TRUE') {
      skipped++;
      continue;
    }

    // Calculate challenge day number
    var start = new Date(startDate);
    var dayNum = Math.floor((today - start) / 86400000) + 1;

    if (dayNum < 1 || dayNum > 21) {
      // Auto-deactivate after day 21
      if (dayNum > 21) {
        sheet.getRange(i + 2, 4).setValue('FALSE');
      }
      skipped++;
      continue;
    }

    // Send email via Gmail MailApp
    try {
      var subject = 'Day ' + dayNum + '/21 - Your Tech English Challenge Awaits! 🚀';
      var htmlBody = buildEmailHtml(name, dayNum);
      MailApp.sendEmail({
        to: email,
        subject: subject,
        htmlBody: htmlBody,
        name: 'TechPulse English'
      });
      sent++;
    } catch (err) {
      Logger.log('Failed to send to ' + email + ': ' + err);
    }
  }

  Logger.log('Reminders sent: ' + sent + ', skipped: ' + skipped);
}

function buildEmailHtml(name, dayNum) {
  var motivations = [
    "Every expert was once a beginner. Keep going! 💪",
    "Consistency beats intensity. You're building a habit! 🔥",
    "You're investing in your future self. It's worth it! 🌟",
    "Small daily improvements lead to stunning results! 📈",
    "The best time to learn was yesterday. The next best is today! ⏰"
  ];
  var motivation = motivations[dayNum % motivations.length];
  var progress = Math.round((dayNum / 21) * 100);

  return '<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px">'
    + '<h2 style="color:#6C63FF">Day ' + dayNum + ' of 21 🎯</h2>'
    + '<p>Hi <strong>' + name + '</strong>,</p>'
    + '<p>It\'s Day <strong>' + dayNum + '</strong> of your 21-Day Tech English Challenge!</p>'
    + '<div style="background:#f0f0f0;border-radius:10px;padding:3px;margin:15px 0">'
    + '  <div style="background:linear-gradient(90deg,#6C63FF,#FF6584);border-radius:8px;'
    + '    height:24px;width:' + progress + '%;text-align:center;color:#fff;font-size:12px;line-height:24px">'
    + progress + '%</div></div>'
    + '<p style="font-style:italic;color:#555">' + motivation + '</p>'
    + '<p><a href="' + SITE_URL + '" style="display:inline-block;background:#6C63FF;color:#fff;'
    + 'padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">'
    + "Start Today's Lesson →</a></p>"
    + '<p style="color:#999;font-size:12px;margin-top:20px">TechPulse English · 21-Day Challenge</p>'
    + '</div>';
}
