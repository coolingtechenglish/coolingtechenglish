/**
 * Google Apps Script for TechPulse 21-Day Challenge
 *
 * Handles:
 * - User registration (stores name, email, start date in Google Sheet)
 * - Daily email reminders with personalized challenge links
 * - Completion emails on day 21
 *
 * Setup:
 * 1. Open your Google Sheet → Extensions → Apps Script
 * 2. Paste this entire file, replacing all existing code
 * 3. Deploy → New deployment → Web app → Execute as Me → Anyone → Deploy
 * 4. Copy the Web App URL into index.html (APPS_SCRIPT_URL variable)
 * 5. Add a time-driven trigger: sendDailyReminders → Day timer → 9am-10am
 *
 * Google Sheet ID: 1qKmPLP9xiQGUV-ObvNEljylTIWJJAW-wD2_3RphyyqY
 */

var SHEET_ID = '1qKmPLP9xiQGUV-ObvNEljylTIWJJAW-wD2_3RphyyqY';
var SITE_URL = 'https://coolingtechenglish.github.io/techpulse/';

var DAY_TOPICS = [
  'IDE & Development Environment Vocabulary',
  'Git & Version Control Terms',
  'Data Types & Variables',
  'Debugging & Error Messages',
  'Logging & Monitoring',
  'API & Endpoint Vocabulary',
  'Week 1 Review Quiz',
  'Writing Clear Commit Messages',
  'Pull Request Descriptions & Reviews',
  'Reading Technical Documentation',
  'Writing Bug Reports',
  'Email Templates for Tech Teams',
  'Slack & Async Communication',
  'Week 2 Review & Writing Challenge',
  'Standup Meeting Phrases',
  'Code Review Comments',
  'Technical Interview Vocabulary',
  'Demo & Presentation Skills',
  'Architecture Discussion Terms',
  'Q&A Session Phrases',
  'Final Challenge & Celebration!'
];

/**
 * Handle incoming GET requests (registration)
 */
function doGet(e) {
  var action = e.parameter.action;

  if (action === 'register') {
    return handleRegister(e);
  }

  return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: 'Unknown action' }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Handle user registration
 */
function handleRegister(e) {
  var name = e.parameter.name || '';
  var email = e.parameter.email || '';
  var day = parseInt(e.parameter.day) || 1;

  if (!name || !email) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: 'Name and email required' }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName('Subscribers') || ss.insertSheet('Subscribers');

  // Check if headers exist
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['Name', 'Email', 'Start Date', 'Current Day', 'Status', 'Registered At']);
  }

  // Check for existing registration
  var data = sheet.getDataRange().getValues();
  var existingRow = -1;
  for (var i = 1; i < data.length; i++) {
    if (data[i][1] && data[i][1].toString().toLowerCase() === email.toLowerCase()) {
      existingRow = i + 1; // 1-indexed
      break;
    }
  }

  var now = new Date();

  if (existingRow > 0) {
    // Update existing registration
    sheet.getRange(existingRow, 4).setValue(day); // Update current day
    sheet.getRange(existingRow, 5).setValue('active');
  } else {
    // New registration
    sheet.appendRow([name, email, now, day, 'active', now]);

    // Send welcome email
    sendWelcomeEmail(name, email);
  }

  return ContentService.createTextOutput(JSON.stringify({ status: 'ok', message: 'Registered successfully' }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Send welcome email to new registrant
 */
function sendWelcomeEmail(name, email) {
  var subject = '🚀 Welcome to the 21-Day Tech English Challenge!';
  var challengeLink = SITE_URL + '?name=' + encodeURIComponent(name) + '&email=' + encodeURIComponent(email) + '&day=1';

  var body = '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">'
    + '<div style="background: #111; color: #f5f0e8; padding: 20px; text-align: center;">'
    + '<h1 style="font-size: 28px; margin: 0;">Tech<span style="color: #d63a2f; font-style: italic;">Pulse</span></h1>'
    + '<p style="margin: 5px 0 0; font-size: 12px; letter-spacing: 3px;">21-DAY TECH ENGLISH CHALLENGE</p>'
    + '</div>'
    + '<div style="padding: 30px; background: #f5f0e8;">'
    + '<h2 style="color: #111;">Hi ' + name + '! 👋</h2>'
    + '<p>You\'re officially in the 21-Day Tech English Challenge! Here\'s what to expect:</p>'
    + '<ul style="line-height: 1.8;">'
    + '<li><strong>Week 1:</strong> Tech Basics & Core Vocabulary</li>'
    + '<li><strong>Week 2:</strong> Writing & Communication</li>'
    + '<li><strong>Week 3:</strong> Real-World Professional Skills</li>'
    + '</ul>'
    + '<p>You\'ll receive a daily reminder email with your personalized link — click it to pick up right where you left off, even on a different device!</p>'
    + '<div style="text-align: center; margin: 25px 0;">'
    + '<a href="' + challengeLink + '" style="background: #111; color: #f5f0e8; padding: 14px 32px; text-decoration: none; font-weight: bold; letter-spacing: 2px; display: inline-block;">START DAY 1 →</a>'
    + '</div>'
    + '<p style="color: #6b6456; font-size: 13px;">Follow <strong>@CoolingTechEnglish</strong> on Instagram for daily tips!</p>'
    + '</div>'
    + '<div style="background: #111; color: #6b6456; padding: 15px; text-align: center; font-size: 12px;">'
    + 'TechPulse · CoolingTech English · #TechEnglish21'
    + '</div>'
    + '</div>';

  GmailApp.sendEmail(email, subject, 'Welcome to the 21-Day Tech English Challenge! Visit: ' + challengeLink, {
    htmlBody: body,
    name: 'TechPulse Challenge'
  });
}

/**
 * Send daily reminder emails to all active subscribers
 * Set up as a daily time-driven trigger (9am-10am Taiwan time)
 */
function sendDailyReminders() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName('Subscribers');
  if (!sheet || sheet.getLastRow() <= 1) return;

  var data = sheet.getDataRange().getValues();

  for (var i = 1; i < data.length; i++) {
    var name = data[i][0];
    var email = data[i][1];
    var currentDay = parseInt(data[i][3]) || 1;
    var status = data[i][4];

    if (status !== 'active' || !email) continue;

    if (currentDay > 21) {
      // Send completion email and mark as completed
      sendCompletionEmail(name, email);
      sheet.getRange(i + 1, 5).setValue('completed');
      continue;
    }

    // Send daily reminder
    sendDayReminder(name, email, currentDay);

    // Increment day
    sheet.getRange(i + 1, 4).setValue(currentDay + 1);
  }
}

/**
 * Send daily challenge reminder with personalized link
 */
function sendDayReminder(name, email, day) {
  var topic = DAY_TOPICS[day - 1] || 'Tech English Practice';
  var weekNum = Math.ceil(day / 7);
  var subject = '📖 Day ' + day + '/21: ' + topic + ' | TechPulse Challenge';
  var challengeLink = SITE_URL + '?name=' + encodeURIComponent(name) + '&email=' + encodeURIComponent(email) + '&day=' + day;

  var progressBar = '';
  for (var d = 1; d <= 21; d++) {
    var color = d < day ? '#2d8a4e' : (d === day ? '#d63a2f' : '#ddd');
    progressBar += '<span style="display:inline-block;width:12px;height:12px;background:' + color + ';margin:1px;border-radius:2px;"></span>';
  }

  var body = '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">'
    + '<div style="background: #111; color: #f5f0e8; padding: 20px; text-align: center;">'
    + '<h1 style="font-size: 28px; margin: 0;">Tech<span style="color: #d63a2f; font-style: italic;">Pulse</span></h1>'
    + '<p style="margin: 5px 0 0; font-size: 12px; letter-spacing: 3px;">DAY ' + day + ' OF 21</p>'
    + '</div>'
    + '<div style="padding: 30px; background: #f5f0e8;">'
    + '<h2 style="color: #111; margin-bottom: 5px;">Hey ' + name + '! 👋</h2>'
    + '<p style="color: #6b6456; margin-top: 0;">Week ' + weekNum + ' · Day ' + day + '</p>'
    + '<div style="background: #fff; border: 2px solid #111; padding: 20px; margin: 15px 0;">'
    + '<h3 style="margin: 0 0 8px; color: #111;">Today\'s Topic:</h3>'
    + '<p style="font-size: 18px; font-weight: bold; color: #d63a2f; margin: 0;">' + topic + '</p>'
    + '</div>'
    + '<div style="margin: 15px 0; text-align: center;">'
    + '<p style="font-size: 12px; color: #6b6456; margin-bottom: 5px;">Your Progress:</p>'
    + progressBar
    + '<p style="font-size: 12px; color: #6b6456; margin-top: 5px;">' + (day - 1) + '/21 completed (' + Math.round(((day - 1) / 21) * 100) + '%)</p>'
    + '</div>'
    + '<div style="text-align: center; margin: 25px 0;">'
    + '<a href="' + challengeLink + '" style="background: #111; color: #f5f0e8; padding: 14px 32px; text-decoration: none; font-weight: bold; letter-spacing: 2px; display: inline-block;">CONTINUE DAY ' + day + ' →</a>'
    + '</div>'
    + '<p style="color: #6b6456; font-size: 13px; text-align: center;">Clicking the button restores your progress automatically!</p>'
    + '</div>'
    + '<div style="background: #111; color: #6b6456; padding: 15px; text-align: center; font-size: 12px;">'
    + 'TechPulse · @CoolingTechEnglish · #TechEnglish21'
    + '</div>'
    + '</div>';

  GmailApp.sendEmail(email, subject, 'Day ' + day + ': ' + topic + '. Continue here: ' + challengeLink, {
    htmlBody: body,
    name: 'TechPulse Challenge'
  });
}

/**
 * Send completion/congratulations email
 */
function sendCompletionEmail(name, email) {
  var subject = '🎉 Congratulations! You completed the 21-Day Challenge!';
  var challengeLink = SITE_URL + '?name=' + encodeURIComponent(name) + '&email=' + encodeURIComponent(email) + '&day=22';

  var body = '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">'
    + '<div style="background: #111; color: #f5c842; padding: 20px; text-align: center;">'
    + '<h1 style="font-size: 28px; margin: 0;">🏆 CHALLENGE COMPLETE!</h1>'
    + '<p style="margin: 5px 0 0; font-size: 12px; letter-spacing: 3px; color: #f5f0e8;">21 DAYS · ALL DONE</p>'
    + '</div>'
    + '<div style="padding: 30px; background: #f5f0e8;">'
    + '<h2 style="color: #111;">Amazing work, ' + name + '! 🎊</h2>'
    + '<p>You\'ve completed all 21 days of the Tech English Challenge. That\'s incredible dedication!</p>'
    + '<p>Here\'s what you accomplished:</p>'
    + '<ul style="line-height: 1.8;">'
    + '<li>✅ Mastered core tech vocabulary</li>'
    + '<li>✅ Practiced professional writing skills</li>'
    + '<li>✅ Built real-world communication confidence</li>'
    + '</ul>'
    + '<div style="text-align: center; margin: 25px 0;">'
    + '<a href="' + challengeLink + '" style="background: #f5c842; color: #111; padding: 14px 32px; text-decoration: none; font-weight: bold; letter-spacing: 2px; display: inline-block;">VIEW YOUR ACHIEVEMENT →</a>'
    + '</div>'
    + '<p style="color: #6b6456; font-size: 13px;">Share your success with #TechEnglish21 on Instagram!</p>'
    + '</div>'
    + '<div style="background: #111; color: #6b6456; padding: 15px; text-align: center; font-size: 12px;">'
    + 'TechPulse · @CoolingTechEnglish · Congratulations! 🎉'
    + '</div>'
    + '</div>';

  GmailApp.sendEmail(email, subject, 'Congratulations ' + name + '! You completed the 21-Day Tech English Challenge!', {
    htmlBody: body,
    name: 'TechPulse Challenge'
  });
}
