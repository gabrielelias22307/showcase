// All 2D screens: intro, dialogue, evidence viewer, notebook, case review,
// ending and teacher report. Pure DOM; no framework.

import { renderGraphic } from './graphics.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const $ = (sel, root = document) => root.querySelector(sel);

export class UI {
  constructor({ mystery, state, npcs, onAction }) {
    this.m = mystery;
    this.state = state;
    this.npcs = npcs;               // id -> NPC
    this.onAction = onAction;       // (action, payload) => void
    this.layer = $('#ui-layer');
    this.modal = null;              // currently open screen name
    this.dialogueNpc = null;
    this.keyHandlers = [];
    addEventListener('keydown', (e) => this.onKey(e));
  }

  get open() { return !!this.modal; }

  // ---------- generic modal ----------
  show(name, html, { cls = '', closable = true } = {}) {
    this.close(true);
    this.modal = name;
    const wrap = document.createElement('div');
    wrap.className = `modal ${cls}`;
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.innerHTML = `<div class="panel">${closable ? '<button class="close" data-close aria-label="Close">×</button>' : ''}${html}</div>`;
    this.layer.appendChild(wrap);
    wrap.addEventListener('click', (e) => { if (e.target.closest('[data-close]')) this.close(); });
    this.current = wrap;
    this.closable = closable;
    requestAnimationFrame(() => (wrap.querySelector('[autofocus]') || wrap.querySelector('button:not(.close), input'))?.focus());
    return wrap;
  }

  close(silent = false) {
    if (!this.current) return;
    this.current.remove();
    this.current = null;
    const was = this.modal;
    this.modal = null;
    if (was === 'dialogue' && this.dialogueNpc && !silent) { this.dialogueNpc.stopTalking(); this.dialogueNpc = null; }
    if (!silent) this.onAction('closed', was);
  }

  onKey(e) {
    if (e.target.closest?.('input, textarea')) { if (e.key === 'Escape') e.target.blur(); return; }
    if (this.current) {
      if (e.key === 'Escape' && this.closable) { e.preventDefault(); this.close(); return; }
      if (/^[1-9]$/.test(e.key)) {
        const btns = [...this.current.querySelectorAll('[data-num]')].filter((b) => !b.disabled);
        const b = btns.find((x) => x.dataset.num === e.key);
        if (b) { e.preventDefault(); b.click(); }
      }
    }
  }

  toast(html, ms = 3500) {
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = html;
    const box = $('#toasts');
    box.appendChild(t);
    while (box.children.length > 3) box.firstElementChild.remove();
    setTimeout(() => t.classList.add('out'), ms);
    setTimeout(() => t.remove(), ms + 400);
  }

  // ---------- intro ----------
  openIntro(hasSave) {
    const w = this.show('intro', `
      <p class="kicker">Graphic Literacy Mystery</p>
      <h1>${esc(this.m.title)}</h1>
      <p class="muted">${esc(this.m.setting)}</p>
      ${this.m.intro.map((p) => `<p>${esc(p)}</p>`).join('')}
      <p class="controls">${esc(this.m.controls)}</p>
      <label class="field">Your name (for your report)
        <input id="student-name" type="text" maxlength="60" value="${esc(this.state.studentName)}" autocomplete="off">
      </label>
      <div class="row">
        <button class="primary" data-start autofocus>${hasSave ? 'Continue' : 'Start investigating'}</button>
        ${hasSave ? '<button data-restart>Start over</button>' : ''}
      </div>`, { cls: 'intro', closable: false });
    w.querySelector('[data-start]').onclick = () => {
      this.state.studentName = $('#student-name').value.trim();
      this.state.save();
      this.close();
    };
    w.querySelector('[data-restart]')?.addEventListener('click', () => {
      if (confirm('Erase your progress and start over?')) { this.state.wipe(); location.reload(); }
    });
  }

  // ---------- dialogue ----------
  openDialogue(npc) {
    this.dialogueNpc = npc;
    this.state.set(`talked:${npc.id}`);
    this.renderNode(npc, npc.def.dialogue.start);
  }

  renderNode(npc, nodeId) {
    const def = npc.def;
    const node = def.dialogue.nodes[nodeId];
    const choices = node.choices.filter((c) => this.state.check(c.requires, c.requiresNot));
    const w = this.show('dialogue', `
      <div class="speaker"><span class="dot" style="background:${esc(def.color)}"></span>
        <div><strong>${esc(def.name)}</strong><span class="muted"> · ${esc(def.role || '')}</span></div></div>
      <p class="line">${esc(node.text)}</p>
      <div class="choices">${choices.map((c, i) => `<button data-num="${i + 1}" data-i="${i}"><kbd>${i + 1}</kbd> ${esc(c.text)}</button>`).join('')}</div>`,
    { cls: 'dialogue' });
    w.querySelectorAll('[data-i]').forEach((b) => {
      b.onclick = () => {
        const c = choices[+b.dataset.i];
        (c.set || []).forEach((f) => this.state.set(f));
        if (c.give && this.state.giveEvidence(c.give)) this.evidenceToast(c.give);
        if (c.action) { this.close(true); npc.stopTalking(); this.dialogueNpc = null; this.onAction(c.action); return; }
        if (c.end || !c.next) { this.close(); return; }
        this.renderNode(npc, c.next);
      };
    });
  }

  evidenceToast(id) {
    const ev = this.m.evidence[id];
    this.toast(`<strong>New evidence:</strong> ${esc(ev.title)}<br><span class="muted">Press N to open your notebook.</span>`);
  }

  // ---------- examine a prop ----------
  openExamine(prop) {
    const ex = prop.examine;
    (ex.set || []).forEach((f) => this.state.set(f));
    const isNew = ex.give ? this.state.giveEvidence(ex.give) : false;
    const w = this.show('examine', `
      <h2>${esc(prop.name)}</h2>
      <p>${esc(ex.text)}</p>
      <div class="row">
        ${ex.give ? `<button class="primary" data-view autofocus>Read the graphic</button>` : ''}
        <button data-close>Back</button>
      </div>`);
    if (isNew) this.evidenceToast(ex.give);
    w.querySelector('[data-view]')?.addEventListener('click', () => this.openEvidence(ex.give));
  }

  // ---------- evidence viewer ----------
  levelBadge(level, skill) {
    return `<span class="badge l${level}">WorkKeys Level ${level}</span><span class="skill">${esc(skill)}</span>`;
  }

  openEvidence(id, back) {
    const ev = this.m.evidence[id];
    const solved = this.state.has(`solved:${id}`);
    const locked = ev.requires && !this.state.check(ev.requires);
    const q = ev.question;
    const w = this.show('evidence', `
      <p class="kicker">Evidence ${esc(id)} · from ${esc(ev.from)}</p>
      <h2>${esc(ev.title)}</h2>
      <div class="levelrow">${this.levelBadge(ev.level, ev.skill)}</div>
      <figure class="graphic">${renderGraphic(ev, this.m.room)}</figure>
      <details class="alt"><summary>Describe this graphic in words</summary><p>${esc(ev.alt)}</p></details>
      <section class="question">
        ${locked ? `<p class="locked">🔒 ${esc(ev.requiresHint || 'Find more evidence first.')}</p>` : `
          <p class="qprompt">${esc(q.prompt)}</p>
          <div class="options">${q.options.map((o, i) => `<button data-num="${i + 1}" data-o="${i}" ${solved ? 'disabled' : ''} class="${solved && o.correct ? 'right' : ''}"><kbd>${String.fromCharCode(65 + i)}</kbd> ${esc(o.text)}</button>`).join('')}</div>
          <p class="feedback" aria-live="polite"></p>`}
        <div class="fact ${solved ? '' : 'hidden'}"><strong>Fact for your notebook:</strong> ${esc(ev.fact)}</div>
      </section>
      <div class="row"><button data-back>${back ? '← Back to notebook' : 'Close'}</button></div>`,
    { cls: 'wide' });
    w.querySelector('[data-back]').onclick = () => (back ? this.openNotebook(back) : this.close());
    if (locked || solved) return;
    const fb = w.querySelector('.feedback');
    w.querySelectorAll('[data-o]').forEach((b) => {
      b.onclick = () => {
        const o = q.options[+b.dataset.o];
        this.state.answerEvidence(id, !!o.correct);
        fb.textContent = o.feedback;
        fb.className = `feedback ${o.correct ? 'good' : 'bad'}`;
        if (o.correct) {
          w.querySelectorAll('[data-o]').forEach((x) => (x.disabled = true));
          b.classList.add('right');
          w.querySelector('.fact').classList.remove('hidden');
          this.toast(`<strong>Fact added.</strong> ${esc(ev.fact)}`, 4500);
        } else {
          b.disabled = true;
          b.classList.add('wrong');
        }
      };
    });
  }

  // ---------- notebook ----------
  openNotebook(tab = 'evidence') {
    const ids = Object.keys(this.m.evidence);
    const have = ids.filter((id) => this.state.has(`has:${id}`));
    const solved = have.filter((id) => this.state.has(`solved:${id}`));
    const tabs = [['evidence', `Evidence (${have.length})`], ['facts', `Facts (${solved.length})`], ['people', 'People'], ['progress', 'My progress']];
    let body = '';
    if (tab === 'evidence') {
      body = have.length ? `<div class="cards">${have.map((id) => {
        const ev = this.m.evidence[id];
        const done = this.state.has(`solved:${id}`);
        return `<button class="card" data-ev="${id}"><span class="kicker">${id} · from ${esc(ev.from)}</span><strong>${esc(ev.title)}</strong>
          <span>${this.levelBadge(ev.level, ev.skill)}</span><span class="status ${done ? 'good' : ''}">${done ? '✔ Question answered' : 'Question not answered yet'}</span></button>`;
      }).join('')}</div>` : '<p>No evidence yet. Talk to people and examine things in the room.</p>';
    } else if (tab === 'facts') {
      body = solved.length ? `<ol class="facts">${solved.map((id) => `<li><strong>${id}:</strong> ${esc(this.m.evidence[id].fact)}</li>`).join('')}</ol>` : '<p>Answer the question on each graphic to add facts here.</p>';
      body += `<p class="muted">You need ${this.m.readyWhen.length} key facts before the case review. You have ${this.m.readyWhen.filter((f) => this.state.has(f)).length}.</p>`;
    } else if (tab === 'people') {
      body = `<ul class="people">${this.m.npcs.map((n) => `<li><span class="dot" style="background:${esc(n.color)}"></span><strong>${esc(n.name)}</strong> · ${esc(n.role)} ${this.state.has(`talked:${n.id}`) ? '<span class="status good">talked</span>' : '<span class="status">not yet</span>'}</li>`).join('')}</ul>`;
    } else {
      body = this.progressTable() + `<div class="row"><button data-report>Teacher report</button><button data-restart class="danger">Start over</button></div>`;
    }
    const w = this.show('notebook', `
      <h2>Detective Notebook</h2>
      <div class="tabs" role="tablist">${tabs.map(([k, l]) => `<button role="tab" aria-selected="${k === tab}" data-tab="${k}">${l}</button>`).join('')}</div>
      <div class="tabbody">${body}</div>`, { cls: 'wide' });
    w.querySelectorAll('[data-tab]').forEach((b) => (b.onclick = () => this.openNotebook(b.dataset.tab)));
    w.querySelectorAll('[data-ev]').forEach((b) => (b.onclick = () => this.openEvidence(b.dataset.ev, 'evidence')));
    w.querySelector('[data-report]')?.addEventListener('click', () => this.openReport());
    w.querySelector('[data-restart]')?.addEventListener('click', () => {
      if (confirm('Erase your progress and start over?')) { this.state.wipe(); location.reload(); }
    });
  }

  progressTable() {
    const lv = this.state.levelSummary();
    const rows = [3, 4, 5, 6, 7].map((n) => {
      const L = lv[n];
      return `<tr><th>Level ${n}</th><td>${L ? `${L.correct} / ${L.total}` : '–'}</td><td>${L ? L.items.map((i) => `${i.firstTry ? '✔' : '✘'} ${esc(i.skill)}`).join('<br>') : '<span class="muted">not attempted</span>'}</td></tr>`;
    }).join('');
    return `<table class="report"><thead><tr><th>Skill level</th><th>Right on first try</th><th>Questions</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  // ---------- case review (final) ----------
  openReview(step = 0) {
    const qs = this.m.review;
    if (step >= qs.length) return this.openCulprit();
    const q = qs[step];
    const used = q.use.map((id) => `<details class="mini"><summary>${id}: ${esc(this.m.evidence[id].title)}</summary><figure class="graphic">${renderGraphic(this.m.evidence[id], this.m.room)}</figure></details>`).join('');
    const w = this.show('review', `
      <p class="kicker">Case review · question ${step + 1} of ${qs.length}</p>
      <div class="levelrow">${this.levelBadge(q.level, q.skill)}</div>
      <p class="qprompt">${esc(q.prompt)}</p>
      ${used ? `<div class="uses"><p class="muted">Graphics to use:</p>${used}</div>` : '<p class="muted">Think about all the graphics in your notebook.</p>'}
      <div class="options">${q.options.map((o, i) => `<button data-num="${i + 1}" data-o="${i}"><kbd>${String.fromCharCode(65 + i)}</kbd> ${esc(o.text)}</button>`).join('')}</div>
      <p class="feedback" aria-live="polite"></p>
      <div class="row"><button class="primary hidden" data-next>Next →</button></div>`, { cls: 'wide' });
    const fb = w.querySelector('.feedback');
    w.querySelectorAll('[data-o]').forEach((b) => {
      b.onclick = () => {
        const o = q.options[+b.dataset.o];
        this.state.answerReview(q.id, !!o.correct);
        fb.textContent = o.feedback;
        fb.className = `feedback ${o.correct ? 'good' : 'bad'}`;
        if (o.correct) {
          w.querySelectorAll('[data-o]').forEach((x) => (x.disabled = true));
          b.classList.add('right');
          const n = w.querySelector('[data-next]');
          n.classList.remove('hidden');
          n.setAttribute('data-num', '9');
          n.onclick = () => this.openReview(step + 1);
          n.focus();
        } else { b.disabled = true; b.classList.add('wrong'); }
      };
    });
  }

  openCulprit(message = '') {
    const suspects = this.m.npcs.filter((n) => n.id !== 'ortiz');
    const w = this.show('culprit', `
      <p class="kicker">Final answer</p>
      <h2>${esc(this.m.culpritPrompt)}</h2>
      ${message ? `<p class="feedback bad">${esc(message)}</p>` : ''}
      <div class="options grid">${suspects.map((n, i) => `<button data-num="${i + 1}" data-s="${n.id}"><span class="dot" style="background:${esc(n.color)}"></span> ${esc(n.name)}</button>`).join('')}</div>`, { cls: 'wide' });
    w.querySelectorAll('[data-s]').forEach((b) => {
      b.onclick = () => {
        const id = b.dataset.s;
        if (id === this.m.culprit) { this.state.finish(); this.openEnding(0); }
        else { this.state.culpritAttempts++; this.state.save(); this.openCulprit(this.m.wrongCulprit[id] || 'The evidence does not support that. Look at the times again.'); }
      };
    });
  }

  openEnding(i) {
    const lines = this.m.ending;
    if (i >= lines.length) return this.openReport(true);
    const w = this.show('ending', `
      <p class="kicker">Case closed</p>
      <p class="line big">${esc(lines[i])}</p>
      <div class="row"><button class="primary" data-num="1" autofocus>${i === lines.length - 1 ? 'See my report' : 'Continue'}</button></div>`, { closable: false });
    w.querySelector('.primary').onclick = () => this.openEnding(i + 1);
  }

  // ---------- teacher report ----------
  reportText() {
    const s = this.state;
    const mins = Math.round(((s.finishedAt || Date.now()) - s.startedAt) / 60000);
    const lv = s.levelSummary();
    const lines = [
      `${this.m.title} - Graphic Literacy report`,
      `Student: ${s.studentName || '(no name entered)'}`,
      `Date: ${new Date().toLocaleString()}`,
      `Case solved: ${s.solved ? 'yes' : 'not yet'}${s.solved ? ` (wrong suspects named first: ${s.culpritAttempts})` : ''}`,
      `Time spent: about ${mins} minutes`,
      '',
      'WorkKeys Graphic Literacy levels (right on first try):'
    ];
    for (const n of [3, 4, 5, 6, 7]) {
      const L = lv[n];
      lines.push(`  Level ${n}: ${L ? `${L.correct}/${L.total}` : 'not attempted'}`);
      if (L) L.items.forEach((i) => lines.push(`     ${i.firstTry ? 'RIGHT' : 'MISSED'}  ${i.label} - ${i.skill}${i.attempts > 1 ? ` (${i.attempts} tries)` : ''}`));
    }
    return lines.join('\n');
  }

  openReport(final = false) {
    const text = this.reportText();
    const w = this.show('report', `
      <p class="kicker">${final ? 'Great detective work!' : 'Progress report'}</p>
      <h2>Your Graphic Literacy report</h2>
      <label class="field">Your name <input id="report-name" type="text" maxlength="60" value="${esc(this.state.studentName)}"></label>
      ${this.progressTable()}
      <pre class="reporttext">${esc(text)}</pre>
      <div class="row">
        <button class="primary" data-copy>Copy report</button>
        <button data-download>Download .txt</button>
        <button data-print>Print / Save as PDF</button>
      </div>
      <p class="muted">Turn in your report the way your teacher asks: paste it into the assignment, or upload the file.</p>`, { cls: 'wide' });
    const refresh = () => { w.querySelector('.reporttext').textContent = this.reportText(); };
    w.querySelector('#report-name').oninput = (e) => { this.state.studentName = e.target.value.trim(); this.state.save(); refresh(); };
    w.querySelector('[data-copy]').onclick = async () => {
      try { await navigator.clipboard.writeText(this.reportText()); this.toast('Report copied.'); }
      catch { const r = document.createRange(); r.selectNodeContents(w.querySelector('.reporttext')); getSelection().removeAllRanges(); getSelection().addRange(r); this.toast('Press Ctrl+C to copy the selected report.'); }
    };
    w.querySelector('[data-download]').onclick = () => {
      const blob = new Blob([this.reportText()], { type: 'text/plain' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `graphic-literacy-mystery-${(this.state.studentName || 'student').replace(/\W+/g, '-')}.txt`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    };
    w.querySelector('[data-print]').onclick = () => print();
  }

  openHelp() {
    this.show('help', `
      <h2>How to play</h2>
      <p>${esc(this.m.controls)}</p>
      <ul>
        <li>Walk up to a person or object. When a prompt appears, press <kbd>E</kbd> or click it.</li>
        <li>People give you graphics: tables, charts, maps and flowcharts.</li>
        <li>Each graphic has one question. Answer it to add a fact to your notebook.</li>
        <li>Choices: click them, or press the number keys.</li>
        <li>When you have the key facts, talk to Ms. Ortiz to start the case review.</li>
      </ul>
      <div class="row"><button class="primary" data-close autofocus>Got it</button></div>`);
  }
}
