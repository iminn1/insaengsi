/**
 * 인생시 — 묵상 제출 백엔드 (Google Apps Script + Google Sheets)
 *
 * 배포 방법: README.md 참고.
 * 시트는 처음 요청이 들어올 때 자동으로 만들어집니다 (users, reflections).
 *
 * 관리자 키: 스크립트 속성(Project Settings → Script properties)에
 *   ADMIN_KEY = 원하는 비밀번호
 * 를 넣어 두세요. 없으면 "admin" 이 기본값입니다 (반드시 바꾸세요).
 */

var USERS = 'users';
var REFS = 'reflections';
var USER_COLS = ['id', 'name', 'pinHash', 'token', 'createdAt'];
var REF_COLS = ['id', 'userId', 'name', 'day', 'text', 'isPublic', 'selected', 'createdAt', 'updatedAt'];

// ---------- 진입점 ----------
function doGet(e) {
  var p = (e && e.parameter) || {};
  return respond(handle(p.action || 'ping', p));
}

function doPost(e) {
  var req = {};
  try { req = JSON.parse(e.postData.contents || '{}'); } catch (err) { return respond({ ok: false, error: 'bad json' }); }
  return respond(handle(req.action, req));
}

function handle(action, req) {
  try {
    switch (action) {
      case 'ping': return { ok: true, time: new Date().toISOString() };
      case 'login': return login(req);
      case 'mine': return mine(req);
      case 'submit': return submit(req);
      case 'remove': return remove(req);
      case 'public': return publicList(req);
      case 'stats': return stats();
      case 'admin_all': return adminAll(req);
      case 'admin_select': return adminSelect(req);
      default: return { ok: false, error: 'unknown action: ' + action };
    }
  } catch (err) {
    return { ok: false, error: String(err && err.message || err) };
  }
}

function respond(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// ---------- 사용자 ----------
function login(req) {
  var name = clean(req.name, 30);
  var pin = String(req.pin || '').trim();
  if (!name) return { ok: false, error: '이름을 입력해 주세요.' };
  if (!/^\d{4}$/.test(pin)) return { ok: false, error: 'PIN은 숫자 4자리입니다.' };

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var users = readAll(USERS, USER_COLS);
    var found = users.rows.filter(function (u) { return normName(u.name) === normName(name); })[0];
    var pinHash = hash(name.toLowerCase() + ':' + pin);
    if (found) {
      if (found.pinHash !== pinHash) return { ok: false, error: '이미 등록된 이름입니다. PIN이 맞지 않습니다.' };
      return { ok: true, token: found.token, name: found.name, isNew: false };
    }
    var id = uid();
    var token = hash(id + ':' + pin + ':' + Math.random());
    appendRow(USERS, USER_COLS, { id: id, name: name, pinHash: pinHash, token: token, createdAt: now() });
    return { ok: true, token: token, name: name, isNew: true };
  } finally { lock.releaseLock(); }
}

function auth(req) {
  var token = String(req.token || '');
  if (!token) return null;
  var users = readAll(USERS, USER_COLS);
  return users.rows.filter(function (u) { return u.token === token; })[0] || null;
}

// ---------- 묵상 ----------
function mine(req) {
  var u = auth(req);
  if (!u) return { ok: false, error: 'auth', needLogin: true };
  var refs = readAll(REFS, REF_COLS).rows.filter(function (r) { return r.userId === u.id; });
  return { ok: true, name: u.name, items: refs.map(pubView) };
}

function submit(req) {
  var u = auth(req);
  if (!u) return { ok: false, error: 'auth', needLogin: true };
  var day = String(req.day || '');
  if (!/^(\d{1,2}|final)$/.test(day)) return { ok: false, error: 'bad day' };
  var text = clean(req.text, 3000);
  if (!text) return { ok: false, error: '내용이 비어 있습니다.' };
  var isPublic = req.isPublic ? 'TRUE' : 'FALSE';

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var all = readAll(REFS, REF_COLS);
    var existing = all.rows.filter(function (r) { return r.userId === u.id && String(r.day) === day; })[0];
    var t = now();
    if (existing) {
      updateRow(REFS, REF_COLS, existing._row, { text: text, isPublic: isPublic, updatedAt: t, name: u.name });
      existing.text = text; existing.isPublic = isPublic; existing.updatedAt = t;
      return { ok: true, item: pubView(existing) };
    }
    var row = { id: uid(), userId: u.id, name: u.name, day: day, text: text, isPublic: isPublic, selected: 'FALSE', createdAt: t, updatedAt: t };
    appendRow(REFS, REF_COLS, row);
    return { ok: true, item: pubView(row) };
  } finally { lock.releaseLock(); }
}

function remove(req) {
  var u = auth(req);
  if (!u) return { ok: false, error: 'auth', needLogin: true };
  var day = String(req.day || '');
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var all = readAll(REFS, REF_COLS);
    var existing = all.rows.filter(function (r) { return r.userId === u.id && String(r.day) === day; })[0];
    if (existing) deleteRow(REFS, existing._row);
    return { ok: true };
  } finally { lock.releaseLock(); }
}

function publicList(req) {
  var day = req.day ? String(req.day) : null;
  var rows = readAll(REFS, REF_COLS).rows.filter(function (r) {
    return isTrue(r.isPublic) && (!day || String(r.day) === day);
  });
  rows.sort(function (a, b) { return String(b.updatedAt).localeCompare(String(a.updatedAt)); });
  return { ok: true, items: rows.map(pubView) };
}

function stats() {
  var rows = readAll(REFS, REF_COLS).rows;
  var byDay = {}, people = {};
  rows.forEach(function (r) {
    byDay[r.day] = (byDay[r.day] || 0) + 1;
    people[r.userId] = true;
  });
  return { ok: true, total: rows.length, participants: Object.keys(people).length, byDay: byDay };
}

// ---------- 관리자 ----------
function isAdmin(req) {
  var key = PropertiesService.getScriptProperties().getProperty('ADMIN_KEY') || 'admin';
  return String(req.adminKey || '') === key;
}

function adminAll(req) {
  if (!isAdmin(req)) return { ok: false, error: '관리자 키가 맞지 않습니다.' };
  var rows = readAll(REFS, REF_COLS).rows;
  var users = readAll(USERS, USER_COLS).rows.length;
  return { ok: true, users: users, items: rows.map(function (r) {
    return { id: r.id, name: r.name, day: r.day, text: r.text, isPublic: isTrue(r.isPublic), selected: isTrue(r.selected), updatedAt: r.updatedAt };
  }) };
}

function adminSelect(req) {
  if (!isAdmin(req)) return { ok: false, error: '관리자 키가 맞지 않습니다.' };
  var all = readAll(REFS, REF_COLS);
  var target = all.rows.filter(function (r) { return r.id === req.id; })[0];
  if (!target) return { ok: false, error: 'not found' };
  updateRow(REFS, REF_COLS, target._row, { selected: req.selected ? 'TRUE' : 'FALSE' });
  return { ok: true };
}

// ---------- 시트 I/O ----------
function sheet(name, cols) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(cols);
    sh.setFrozenRows(1);
  }
  return sh;
}

function readAll(name, cols) {
  var sh = sheet(name, cols);
  var values = sh.getDataRange().getValues();
  var rows = [];
  for (var i = 1; i < values.length; i++) {
    var obj = { _row: i + 1 };
    for (var c = 0; c < cols.length; c++) obj[cols[c]] = values[i][c] === undefined ? '' : String(values[i][c]);
    if (obj.id) rows.push(obj);
  }
  return { rows: rows };
}

function appendRow(name, cols, obj) {
  sheet(name, cols).appendRow(cols.map(function (c) { return obj[c] === undefined ? '' : obj[c]; }));
}

function updateRow(name, cols, rowIndex, patch) {
  var sh = sheet(name, cols);
  Object.keys(patch).forEach(function (k) {
    var c = cols.indexOf(k);
    if (c >= 0) sh.getRange(rowIndex, c + 1).setValue(patch[k]);
  });
}

function deleteRow(name, rowIndex) {
  SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name).deleteRow(rowIndex);
}

// ---------- 유틸 ----------
function pubView(r) {
  return { id: r.id, name: r.name, day: r.day, text: r.text, isPublic: isTrue(r.isPublic), updatedAt: r.updatedAt };
}
// 시트가 'TRUE' 문자열을 불리언으로 바꾸므로 대소문자 무관 비교
function isTrue(v) { return String(v).toUpperCase() === 'TRUE'; }
function clean(s, max) { return String(s || '').replace(/\s+$/, '').replace(/^\s+/, '').slice(0, max); }
function normName(s) { return String(s || '').replace(/\s+/g, '').toLowerCase(); }
function now() { return new Date().toISOString(); }
function uid() { return Utilities.getUuid(); }
function hash(s) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s, Utilities.Charset.UTF_8);
  return bytes.map(function (b) { return ('0' + ((b + 256) % 256).toString(16)).slice(-2); }).join('');
}
