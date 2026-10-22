// Game state: flags, evidence progress, review answers. Saved per browser.
// Flags are plain strings. The engine adds these automatically:
//   has:<evidenceId>     the player has collected the graphic
//   solved:<evidenceId>  the player answered its question correctly
//   talked:<npcId>       the player has spoken to the NPC
//   ready                every flag in mystery.readyWhen is set
//
// Optional practice banks (data/banks/) are tracked separately in
// this.practice, so they never change the mystery.

export class GameState {
  constructor(mystery, bankDefs = []) {
    this.mystery = mystery;
    this.bankDefs = bankDefs;   // optional question banks from other WorkKeys tests
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
    this.banks = [];         // ids of the practice banks that are switched on
    this.practice = {};      // itemId -> { seen, attempts, firstTry, solvedAt }
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

  // ---------- optional practice banks ----------
  bankOn(id) { return this.banks.includes(id); }

  setBanks(ids) {
    const valid = ids.filter((id) => this.bankDefs.some((b) => b.id === id));
    if (valid.join() === this.banks.join()) return;
    this.banks = this.bankDefs.map((b) => b.id).filter((id) => valid.includes(id));
    this.emit('banks', this.banks);
  }

  activeBanks() { return this.bankDefs.filter((b) => this.banks.includes(b.id)); }

  bankItem(itemId) {
    for (const bank of this.bankDefs) if (bank.items[itemId]) return { bank, item: bank.items[itemId] };
    return null;
  }

  seePractice(itemId) {
    const p = this.practice[itemId] || (this.practice[itemId] = { seen: false, attempts: 0, firstTry: null, solvedAt: null });
    if (!p.seen) { p.seen = true; this.emit('practiceSeen', itemId); }
  }

  practiceDone(itemId) { return !!this.practice[itemId]?.solvedAt; }

  answerPractice(itemId, correct) {
    const p = this.practice[itemId] || (this.practice[itemId] = { seen: true, attempts: 0, firstTry: null, solvedAt: null });
    if (p.solvedAt) return;
    p.attempts++;
    if (p.firstTry === null) p.firstTry = !!correct;
    if (correct) p.solvedAt = Date.now();
    this.emit('practice', itemId);
  }

  // How many tasks in the switched-on banks are done, for the HUD.
  practiceCount() {
    let done = 0, total = 0;
    for (const b of this.activeBanks()) for (const id of Object.keys(b.items)) { total++; if (this.practiceDone(id)) done++; }
    return { done, total };
  }

  finish() {
    this.solved = true;
    this.finishedAt = Date.now();
    this.emit('finished');
  }

  // Per-level results, for the report. testId is 'graphic' (the mystery)
  // or the id of a practice bank, such as 'math' or 'docs'.
  levelSummary(testId = 'graphic') {
    const levels = {};
    const add = (level, skill, firstTry, attempts, label) => {
      const L = (levels[level] = levels[level] || { items: [], correct: 0, total: 0 });
      L.items.push({ label, skill, firstTry, attempts });
      L.total++;
      if (firstTry) L.correct++;
    };
    if (testId !== 'graphic') {
      const bank = this.bankDefs.find((b) => b.id === testId);
      for (const [id, it] of Object.entries(bank?.items || {})) {
        const p = this.practice[id];
        if (p && p.attempts) add(it.level, it.skill, p.firstTry, p.attempts, `${id}: ${it.title}`);
      }
      return levels;
    }
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
        finishedAt: this.finishedAt,
        banks: this.banks,
        practice: this.practice
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
      this.banks = (d.banks || []).filter((id) => this.bankDefs.some((b) => b.id === id));
      this.practice = d.practice || {};
    } catch (e) { /* ignore */ }
  }

  wipe() {
    const keepBanks = this.banks;   // "Start over" keeps the practice switches
    try { localStorage.removeItem(this.key); } catch (e) { /* ignore */ }
    this.reset();
    this.banks = keepBanks;
    this.emit('reset');
  }
}
