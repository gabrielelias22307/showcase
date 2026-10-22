// Run in a worker tab open on /api/v1/users/self (see canvas-unit-build, Step 1).
// No API key: requests ride the teacher's signed-in session plus its CSRF cookie.
// Only the last plain expression comes back, so: set up, fire, then read in separate calls.

// --- call 1: set up (once per worker tab)
window.CT = decodeURIComponent((document.cookie.match(/_csrf_token=([^;]+)/) || [, ''])[1]);
window.P = function (m, u, b) {
  return fetch(u, {
    method: m, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'X-CSRF-Token': window.CT },
    body: b ? JSON.stringify(b) : undefined
  })
    .then(r => r.text().then(t => { document.title = 'R' + r.status; window.LAST = t.replace(/^while\(1\);/, ''); }))
    .catch(e => { window.LAST = 'ERR ' + e.message; });
};
'csrf=' + (window.CT ? 'ok' : 'NO');

// --- call 2: step 1, ask Canvas for an upload slot (fill COURSE_ID)
window.P('POST', '/api/v1/courses/COURSE_ID/files', {
  name: 'Jar Made by Dave - 3D Activity.html', size: 390356,
  content_type: 'text/html', parent_folder_path: 'Unit Activities', on_duplicate: 'rename'
}); 'sent';

// --- call 3: read upload_url + upload_params, then send the bytes with curl (see HANDOVER.md)
String(window.LAST).slice(0, 1500);

// --- call 4: step 2, create the assignment (EMBED = canvas-embed.html with numbers filled in)
window.EMBED = `PASTE canvas-embed.html HERE`;
window.P('POST', '/api/v1/courses/COURSE_ID/assignments', { assignment: {
  name: '\u{1F7E5} L#: 3D Object — Jar Made by Dave',
  description: window.EMBED,
  submission_types: ['online_text_entry', 'online_upload'],
  points_possible: 1, published: false, assignment_group_id: GROUP_ID
} }); 'sent';

// --- call 5: step 3, add to the module at the agreed position
window.P('POST', '/api/v1/courses/COURSE_ID/modules/MODULE_ID/items', { module_item: {
  title: '\u{1F7E5} L#: 3D Object — Jar Made by Dave',
  type: 'Assignment', content_id: ASSIGNMENT_ID, position: POSITION
} }); 'sent';

// --- call 6: verify (read-only)
window.P('GET', '/api/v1/courses/COURSE_ID/assignments/ASSIGNMENT_ID'); 'sent';
(function () { var a = JSON.parse(window.LAST); return [a.published, a.points_possible, a.submission_types.join(','), /<iframe[^>]+\/preview/.test(a.description)].join(' | '); })();
