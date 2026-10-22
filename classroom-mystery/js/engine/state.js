// Game state: flags, evidence progress, review answers. Saved per browser.
// Flags are plain strings. The engine adds these automatically:
//   has:<evidenceId>     the player has collected the graphic
//   solved:<evidenceId>  the player answered its question correctly
//   talked:<npcId>       the player has spoken to the NPC
//   ready                every flag in mystery.readyWhen is set

export class GameState {
  constructor(mystery) {
    this.mystery = mystery;
    this.key = `classroom-mystery:${mystery.id}`;
    this.listeners = new Set();
    this.reset();
    this.load();
  }

  reset() {
    this.studentName = '';
    this.flags = new Set();
    this.evidence = {};      // id -> { attempts, firstTry, solvedAt }
    this.review = {};        // id -> { attempts, firstTry }
    this.culpritAttempts = 0;
    this.solved = false;
    this.startedAt = Date.now();
    this.finishedAt = null;
  }

  on(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  emit(type, payload) { for (const fn of this.listeners) fn(type, payload); this.save(); }

  has(flag) { return this.flags.has(flag); }
  check(requires = [], requiresNot = []) {
    return requires.every((f) => this.flags.has(f)) && requiresNot.every((f) => !this.flags.has(f));
  }

  set(flag) {
    if (this.flags.has(flag)) return;
    this.flags.add(flag);
    this.updateReady();
    this.emit('flag', flag);
  }

  updateReady() {
    if (!this.flags.has('ready') && this.mystery.readyWhen.every((f) => this.flags.has(f))) {
      this.flags.add('ready');
      this.emit('ready');
    }
  }

  giveEvidence(id) {
    if (this.flags.has(`has:${id}`)) return false;
    this.evidence[id] = this.evidence[id] || { attempts: 0, firstTry: null, solvedAt: null };
    this.set(`has:${id}`);
    this.emit('evidence', id);
    return true;
  }

  answerEvidence(id, correct) {
    const e = this.evidence[id] || (this.evidence[id] = { attempts: 0, firstTry: null, solvedAt: null });
    if (e.solvedAt) return;
    e.attempts++;
    if (e.firstTry === null) e.firstTry = !!correct;
    if (correct) {
      e.solvedAt = Date.now();
      this.set(`solved:${id}`);
      this.emit('solved', id);
    } else {
      this.emit('answer', id);
    }
  }

  answerReview(id, correct) {
    const r = this.review[id] || (this.review[id] = { attempts: 0, firstTry: null });
    r.attempts++;
    if (r.firstTry === null) r.firstTry = !!correct;
    this.emit('review', id);
  }

  finish() {
    this.solved = true;
    this.finishedAt = Date.now();
    this.emit('finished');
  }

  // Per-level results, for the report.
  levelSummary() {
    const levels = {};
    const add = (level, skill, firstTry, attempts, label) => {
      const L = (levels[level] = levels[level] || { items: [], correct: 0, total: 0 });
      L.items.push({ label, skill, firstTry, attempts });
      L.total++;
      if (firstTry) L.correct++;
    };
    for (const [id, ev] of Object.entries(this.mystery.evidence)) {
      const e = this.evidence[id];
      if (e && e.attempts) add(ev.level, ev.skill, e.firstTry, e.attempts, `${id}: ${ev.title}`);
    }
    for (const q of this.mystery.review) {
      const r = this.review[q.id];
      if (r && r.attempts) add(q.level, q.skill, r.firstTry, r.attempts, `${q.id}: Case review`);
    }
    return levels;
  }

  save() {
    try {
      localStorage.setItem(this.key, JSON.stringify({
        studentName: this.studentName,
        flags: [...this.flags],
        evidence: this.evidence,
        review: this.review,
        culpritAttempts: this.culpritAttempts,
        solved: this.solved,
        startedAt: this.startedAt,
        finishedAt: this.finishedAt
      }));
    } catch (e) { /* storage blocked: game still works, just no resume */ }
  }

  load() {
    try {
      const raw = localStorage.getItem(this.key);
      if (!raw) return;
      const d = JSON.parse(raw);
      this.studentName = d.studentName || '';
      this.flags = new Set(d.flags || []);
      this.evidence = d.evidence || {};
      this.review = d.review || {};
      this.culpritAttempts = d.culpritAttempts || 0;
      this.solved = !!d.solved;
      this.startedAt = d.startedAt || Date.now();
      this.finishedAt = d.finishedAt || null;
    } catch (e) { /* ignore */ }
  }

  wipe() {
    try { localStorage.removeItem(this.key); } catch (e) { /* ignore */ }
    this.reset();
    this.emit('reset');
  }
}
