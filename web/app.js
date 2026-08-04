// Pyodide PoC — 파이썬 엔진을 브라우저에서 그대로 돌린다.
//
// JS↔Python 경계는 gidc/web_api.py 뿐이고, 오가는 값은 평범한 dict/list다.
// 그래서 이쪽은 .toJs() 한 번 + destroy() 만 신경 쓰면 된다.
//
// 검증(슬롯별 허용 주옵션, 부옵션 4개·중복 금지, 무기 종류)은 엔진이 이미 갖고 있다.
// 여기서는 드롭다운을 미리 걸러 잘못 고를 수 없게 하고, 그래도 뚫린 건 errors로 받는다.

// 없는 id를 조용히 null로 돌려주면 한참 뒤에 엉뚱한 자리에서 터진다.
// 대부분 index.html과 app.js의 버전이 어긋난 경우라 그렇게 말해 준다.
function $(id) {
  const el = document.getElementById(id);
  if (!el) throw new Error(
    `#${id} 를 찾을 수 없습니다. index.html과 app.js 버전이 어긋났을 수 있습니다 — ` +
    `강력 새로고침(Ctrl+Shift+R) 해보세요.`);
  return el;
}

const status_ = $("status");
const MAX_PARTY = 4;

let api = null;
let reg = null;           // get_registries() 결과
let party = [];           // 빌드시트 spec 배열
let answers = {};
let target = "";
let enemyLevel = 100;
let editing = null;       // 빌드 창이 열려 있는 파티 인덱스 (닫혀 있으면 null)

function make(tag, props = {}, ...kids) {
  const n = document.createElement(tag);
  Object.assign(n, props);
  for (const k of kids) n.append(k);
  return n;
}

function opt(list, value, getVal = (x) => x, getLabel = (x) => x) {
  const s = make("select");
  for (const x of list) s.add(new Option(getLabel(x), String(getVal(x))));
  s.value = String(value);
  return s;
}

// extra 는 settings 만 덮어쓴다 (히트 설명이 targets/explain 을 바꿔 부른다).
function sheet(extra = {}) {
  return {
    party,
    enemy: { level: enemyLevel },
    settings: { reaction: "NONE", charLevel: 90, targets: target ? [target] : [], ...extra },
  };
}

// PyProxy -> 순수 JS 객체. 파이썬 dict를 JS 객체로 바꾸고 프록시는 즉시 해제한다.
function unwrap(proxy) {
  const out = proxy.toJs({ dict_converter: Object.fromEntries });
  proxy.destroy();
  return out;
}

function fail(what, e) {
  status_.className = "err";
  status_.textContent = what + ":\n" + (e && e.message ? e.message : String(e));
  console.error(e);
}

async function boot() {
  const t0 = performance.now();
  try {
    status_.textContent = "Pyodide 런타임 내려받는 중… (최초 1회, 이후 캐시)";
    const py = await loadPyodide();

    const tRuntime = performance.now();
    status_.textContent = "엔진 번들 푸는 중…";
    const zip = await (await fetch("engine.zip", { cache: "no-cache" })).arrayBuffer();
    py.unpackArchive(zip, "zip");

    status_.textContent = "엔진 임포트 중…";
    api = py.pyimport("gidc.web_api");
    reg = unwrap(api.get_registries());

    // 기본 파티: 스커크 조합을 빌드시트로 펴서 시작한다
    party = ["skirk_party/skirk", "skirk_party/furina",
             "skirk_party/escoffier", "skirk_party/mona"]
            .map((n) => unwrap(api.preset_to_sheet(n)));

    const t1 = performance.now();
    status_.textContent =
      `준비 완료 — 캐릭터 ${reg.counts.characters} / 무기 ${reg.counts.weapons} / ` +
      `성유물 ${reg.counts.artifactSets}세트\n` +
      `런타임 ${((tRuntime - t0) / 1000).toFixed(1)}s · ` +
      `엔진 ${((t1 - tRuntime) / 1000).toFixed(2)}s · ` +
      `번들 ${(zip.byteLength / 1024).toFixed(0)}KB`;

    $("reset").disabled = false;
    renderAll();
  } catch (e) {
    fail("초기화 실패", e);
  }
}

// 파티 구성·빌드가 바뀌면 답변을 비운다. 질문 ID가 (호출 지점, 반복 횟수)라
// 구성이 달라지면 같은 ID가 다른 질문을 가리킬 수 있다.
//
// rebuildEditor는 열려 있는 빌드 창의 위젯 구성 자체가 달라지는 변경(무기 교체,
// 성유물 세트 착탈)에만 준다. 숫자만 고쳤는데 다시 그리면 입력 포커스가 날아간다.
function structuralChange(rebuildEditor = false) {
  answers = {};
  renderParty();
  if (rebuildEditor) renderEditor();
  recalc();
}

function renderAll() {
  renderParty();
  recalc();
}

// ── 파티 ─────────────────────────────────────────────────────────────────
function renderParty() {
  const box = $("party");
  box.innerHTML = "";

  party.forEach((c, i) => {
    const sel = opt(reg.characters, c.character, (x) => x.name, (x) => x.name);
    sel.onchange = () => { swapCharacter(i, sel.value); };
    const edit = make("button", { className: "mini", textContent: "빌드", title: "빌드 편집" });
    edit.onclick = () => openEditor(i);
    const del = make("button", { className: "mini", textContent: "✕", title: "제외" });
    del.onclick = () => { closeEditor(); party.splice(i, 1); structuralChange(); };
    box.append(make("div", { className: "slot on" },
      make("div", { className: "line" }, sel, edit, del),
      make("div", { className: "line sub", textContent: slotSummary(c) })));
  });

  if (party.length < MAX_PARTY) {
    const add = make("select");
    add.add(new Option("+ 캐릭터 추가", ""));
    for (const p of reg.presets) add.add(new Option(`${p.char} · ${p.id}`, p.id));
    add.onchange = () => {
      if (!add.value) return;
      party.push(unwrap(api.preset_to_sheet(add.value)));
      structuralChange();
    };
    box.append(make("div", { className: "slot" }, add));
  }

  $("partycount").textContent = `— ${party.length}/${MAX_PARTY}명`;

  const sel = $("target");
  sel.innerHTML = "";
  sel.add(new Option("전원", ""));
  for (const c of party) sel.add(new Option(c.character, c.character));
  if (![...sel.options].some((o) => o.value === target)) target = "";
  sel.value = target;
}

function slotSummary(c) {
  const arts = Object.values(c.artifacts || {}).filter(Boolean).length;
  return `Lv${c.level} C${c.constellation} · ${c.weapon ? c.weapon.name : "무기 없음"} · 성유물 ${arts}/5`;
}

// 캐릭터를 바꾸면 그 캐릭터의 프리셋이 있으면 그것으로, 없으면 무기를 비운다
// (무기 종류가 안 맞으면 엔진이 거부하기 때문).
function swapCharacter(i, name) {
  const preset = reg.presets.find((p) => p.char === name);
  if (preset) {
    party[i] = unwrap(api.preset_to_sheet(preset.id));
  } else {
    party[i] = { ...party[i], character: name, weapon: null, traits: [] };
  }
  structuralChange(true);
}

// ── 빌드 편집 창 ─────────────────────────────────────────────────────────
function openEditor(i) {
  editing = i;
  renderEditor();
  $("editor").showModal();
}

function closeEditor() {
  editing = null;
  $("editor").close();
}

function renderEditor() {
  if (editing === null) return;
  const c = party[editing];
  $("editortitle").textContent = `${c.character} 빌드`;
  const body = $("editorbody");
  body.innerHTML = "";
  body.append(buildEditor(c));
}

function buildEditor(c) {
  const meta = reg.characters.find((x) => x.name === c.character) || {};
  c.artifacts = c.artifacts || {};
  const d = make("div");

  // 레벨 / 명함 / 특성 레벨
  const row = make("div", { className: "row" });
  for (const [key, label, min, max] of [
    ["level", "레벨", 1, 90], ["constellation", "명함", 0, 6],
    ["naLevel", "평타", 1, 10], ["skillLevel", "E", 1, 10], ["burstLevel", "Q", 1, 10],
  ]) {
    const inp = make("input", { type: "number", value: c[key], min, max });
    inp.style.width = "4rem";
    inp.onchange = () => { c[key] = Number(inp.value); structuralChange(); };
    row.append(make("label", { textContent: label }, inp));
  }
  d.append(row);

  // 획득 가능 특성 (니콜의 마도 등)
  if (meta.unlockableTraits && meta.unlockableTraits.length) {
    const trow = make("div", { className: "row" });
    for (const t of meta.unlockableTraits) {
      const info = reg.traits.find((x) => x.id === t);
      const cb = make("input", { type: "checkbox", checked: (c.traits || []).includes(t) });
      cb.onchange = () => {
        c.traits = cb.checked ? [...(c.traits || []), t]
                              : (c.traits || []).filter((x) => x !== t);
        structuralChange();
      };
      trow.append(make("label", { textContent: info ? info.label : t }, cb));
    }
    d.append(trow);
  }

  // 무기 — 캐릭터가 장착 가능한 종류만 보여준다
  const usable = reg.weapons.filter((w) => !meta.weaponType || w.type === meta.weaponType);
  const wrow = make("div", { className: "row" });
  const wsel = make("select");
  wsel.add(new Option("(없음)", ""));
  for (const w of usable) wsel.add(new Option(`${w.name} (기초 ${w.baseAtk})`, w.name));
  wsel.value = c.weapon ? c.weapon.name : "";
  wsel.onchange = () => {
    c.weapon = wsel.value ? { name: wsel.value, refinement: c.weapon?.refinement || 1 } : null;
    structuralChange(true);   // 정련 셀렉트의 활성 여부가 바뀐다
  };
  const rsel = opt([1, 2, 3, 4, 5], c.weapon ? c.weapon.refinement : 1,
                   (x) => x, (x) => "정련 " + x);
  rsel.disabled = !c.weapon;
  rsel.onchange = () => { if (c.weapon) { c.weapon.refinement = Number(rsel.value); structuralChange(); } };
  wrow.append(make("label", { textContent: "무기" }, wsel), rsel);
  d.append(wrow);

  // 성유물 5슬롯
  for (const slot of reg.slots) d.append(artifactEditor(c, slot));
  return d;
}

function artifactEditor(c, slot) {
  const a = (c.artifacts || {})[slot.key];
  const box = make("div", { className: "art" });
  const hdr = make("div", { className: "hdr" });
  hdr.append(make("span", { className: "name", textContent: slot.label }));

  const setSel = make("select");
  setSel.add(new Option("(없음)", ""));
  for (const s of reg.artifactSets) setSel.add(new Option(s.label, s.id));
  setSel.value = a ? a.set : "";
  setSel.style.flex = "1";
  setSel.onchange = () => {
    if (!setSel.value) { c.artifacts[slot.key] = null; }
    else if (a) { a.set = setSel.value; }
    else { c.artifacts[slot.key] = blankArtifact(slot); }
    structuralChange(!a || !setSel.value);   // 착탈이면 주옵·부옵 위젯이 생기거나 사라진다
  };
  hdr.append(setSel);
  box.append(hdr);

  if (!a) return box;

  // 주옵션 — 이 부위에 허용된 것만
  const mrow = make("div", { className: "hdr" });
  const allowed = reg.validMainStats[slot.key] || [];
  const msel = opt(allowed, a.main.stat, (x) => x, (x) => statLabel(x));
  msel.style.flex = "1";
  msel.onchange = () => { a.main.stat = msel.value; structuralChange(); };
  const mval = make("input", { type: "number", step: "0.1", value: a.main.value });
  mval.style.width = "5rem";
  mval.onchange = () => { a.main.value = Number(mval.value); structuralChange(); };
  mrow.append(make("span", { className: "name", textContent: "주옵" }), msel, mval);
  box.append(mrow);

  // 부옵션 4개 — 원소피해/치유는 목록에서 빠져 있다
  const subs = make("div", { className: "subs" });
  a.subs.forEach((s, i) => {
    const ssel = opt(reg.validSubStats, s.stat, (x) => x, (x) => statLabel(x));
    ssel.onchange = () => { s.stat = ssel.value; structuralChange(); };
    const sval = make("input", { type: "number", step: "0.1", value: s.value });
    sval.onchange = () => { s.value = Number(sval.value); structuralChange(); };
    subs.append(make("div", {}, ssel, sval));
  });
  box.append(subs);
  return box;
}

function blankArtifact(slot) {
  const main = (reg.validMainStats[slot.key] || ["HP"])[0];
  const pool = reg.validSubStats;
  return {
    set: reg.artifactSets[0].id,
    main: { stat: main, value: 0 },
    subs: [0, 1, 2, 3].map((i) => ({ stat: pool[i % pool.length], value: 0 })),
  };
}

const statLabel = (id) => (reg.statTypes.find((s) => s.id === id) || {}).label || id;

// ── 답변 수렴 루프의 한 스텝 ─────────────────────────────────────────────
// pending 이 남아 있어도 stats/damage 는 채워져 온다(미답은 중립 기본값).
function recalc() {
  if (!api) return;
  $("errors").textContent = "";
  if (!party.length) {
    for (const id of ["questions", "stats", "damage"]) $(id).innerHTML = "";
    $("qcount").textContent = "— 파티를 편성하세요";
    return;
  }

  const t0 = performance.now();
  let out;
  try {
    out = unwrap(api.run_calculation(sheet(), answers));
  } catch (e) {
    fail("계산 실패", e);
    return;
  }
  const ms = performance.now() - t0;

  if (out.errors.length) {
    $("errors").textContent = out.errors
      .map((e) => (e.character ? `[${e.character}] ` : "") + e.message).join("\n");
  }

  renderQuestions(out.questions, out.pending, out.stale);
  renderStats(out.stats);
  renderDamage(out.damage);

  $("dmgtarget").textContent = (target ? `— ${target}` : "— 전원") + " · 히트를 누르면 근거";
  $("qcount").textContent = out.errors.length
    ? "— 빌드 오류"
    : `— 총 ${out.questions.length}개 중 미답 ${out.pending.length}개 · 계산 ${ms.toFixed(0)}ms`;
}

// ── 질문 ─────────────────────────────────────────────────────────────────
function renderQuestions(questions, pending, stale) {
  const pendingSet = new Set(pending), staleSet = new Set(stale);
  const box = $("questions");
  box.innerHTML = "";

  for (const q of questions) {
    const div = make("div", { className: "q" + (pendingSet.has(q.id) ? " pending" : "") });
    const label = make("label", { textContent: q.prompt });
    for (const [cond, text] of [[pendingSet.has(q.id), "미답"], [staleSet.has(q.id), "범위 조정됨"]]) {
      if (cond) label.prepend(make("span", { className: "badge", textContent: text }));
    }
    div.append(label, widget(q));
    box.append(div);
  }
}

function widget(q) {
  const cur = answers[q.id];
  const bump = (v) => { answers[q.id] = v; recalc(); };   // 답변은 구조 변경이 아니다

  if (q.kind === "bool") {
    const e = make("input", { type: "checkbox", checked: cur === true });
    e.onchange = () => bump(e.checked);
    return e;
  }
  if (q.kind === "int") {
    const e = make("input", { type: "number", min: q.min, max: q.max,
                              value: cur !== undefined ? cur : q.min });
    e.onchange = () => bump(Number(e.value));
    return e;
  }
  if (q.kind === "choice") {
    const e = opt(q.options.map((o, i) => i), cur !== undefined ? cur : 0,
                  (i) => i, (i) => q.options[i]);
    e.onchange = () => bump(Number(e.value));
    return e;
  }
  // 다중 선택 — <select multiple>은 선택 상태가 눈에 안 들어오고 Ctrl+클릭을
  // 요구해서 실수로 기존 선택을 날린다. 체크박스 칩으로 편다.
  const picked = new Set(cur || []);
  const box = make("div", { className: "multi" });
  q.options.forEach((o, i) => {
    const cb = make("input", { type: "checkbox", checked: picked.has(i) });
    const chip = make("label", { className: "chip" + (picked.has(i) ? " on" : "") },
                       cb, make("span", { textContent: o }));
    cb.onchange = () => {
      if (cb.checked) picked.add(i); else picked.delete(i);
      chip.classList.toggle("on", cb.checked);
      bump([...picked].sort((a, b) => a - b));
    };
    box.append(chip);
  });
  return box;
}

// ── 결과 ─────────────────────────────────────────────────────────────────
const pct = (v) => (v * 100).toFixed(1) + "%";
const num = (v) => v.toLocaleString("ko-KR", { maximumFractionDigits: 0 });
// 설명에 쓰는 수 — 0.466(계수·배율)과 24,000(피해)이 한 화면에 섞여 나온다.
const fmt = (v) => (typeof v === "number"
  ? v.toLocaleString("ko-KR", { maximumFractionDigits: 4 }) : String(v));
const signed = (v) => (v > 0 ? "+" : "") + fmt(v);

// onRow(tr, i) 는 데이터 행에만 불린다 (머리글 행은 건너뛴다).
function table(node, headers, rows, onRow = null) {
  node.innerHTML = "";
  const tr = node.insertRow();
  headers.forEach((h) => tr.append(make("th", { textContent: h })));
  rows.forEach((row, i) => {
    const r = node.insertRow();
    row.forEach((c, j) => {
      const td = r.insertCell();
      if (typeof c === "string") td.textContent = c; else td.append(c);
      if (j > 0) td.className = "num";
    });
    if (onRow) onRow(r, i);
  });
}

function renderStats(stats) {
  table($("stats"), ["캐릭터", "공격력", "HP", "방어력", "치확", "치피", "충전"],
    stats.map((s) => [s.name, num(s.atk), num(s.hp), num(s.def),
                      pct(s.critRate), pct(s.critDmg), pct(s.energyRecharge)]));
}

function renderDamage(damage) {
  const multi = new Set(damage.map((d) => d.char)).size > 1;
  table($("damage"), [multi ? "캐릭터 · 히트" : "히트", "비크리", "크리", "기댓값"],
    damage.map((d) => [multi ? `${d.char} · ${d.hit}` : d.hit,
                       num(d.nonCrit), num(d.crit), num(d.expected)]),
    (tr, i) => {
      tr.className = "hit";
      tr.tabIndex = 0;
      tr.title = "왜 이 데미지인지 보기";
      tr.onclick = () => openExplain(damage[i].char, damage[i].hit);
      tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); tr.onclick(); } };
    });
}

// ── 히트 설명 ────────────────────────────────────────────────────────────
// 히트를 누르면 "왜 이 숫자인가"를 계산을 한 번 더 돌려서 받아 온다.
// 본 계산에 얹지 않고 따로 부르는 이유가 둘이다.
//
//  · settings.explain 은 히트 '이름'만 받는다. 같은 이름의 히트를 두 캐릭터가
//    가질 수 있어 targets 로 캐릭터를 좁혀야 엉뚱한 사람 설명이 나오지 않는다.
//    본 계산의 targets 를 건드리면 데미지 표까지 그 한 명으로 줄어든다.
//  · explain 을 켜면 엔진이 버프 기여를 기록하느라 느려진다. 누를 때만 켜면 된다.
//
// 답변(answers)은 지금 화면 그대로 넘긴다 — 표에 보이는 그 숫자를 설명해야 한다.
function openExplain(char, hit) {
  let out;
  try {
    out = unwrap(api.run_calculation(sheet({ targets: [char], explain: hit }), answers));
  } catch (e) {
    fail("설명 계산 실패", e);
    return;
  }
  renderExplain(char, hit, out.explain);
  $("explain").showModal();
}

function renderExplain(char, hit, ex) {
  $("explaintitle").textContent = `${char} · ${hit}`;
  const body = $("explainbody");
  body.innerHTML = "";

  // 표에 있던 히트가 사라지는 경우 — 답변이 바뀌어 히트 구성 자체가 달라졌을 때다.
  if (!ex) {
    body.append(make("div", { textContent:
      "이 히트의 설명을 만들지 못했습니다. 답변이 바뀌어 히트가 사라졌을 수 있습니다 — 표를 다시 확인하세요." }));
    return;
  }

  const r = ex.result;
  body.append(make("div", { className: "ex-res",
    textContent: `비크리 ${num(r.nonCrit)} · 크리 ${num(r.crit)} · 기댓값 ${num(r.expected)}` }));
  // 어떤 보너스가 왜 안 걸리는지는 결국 이 둘로 갈린다 (원소 없는 평타 = 물리라 냉기 보너스가 안 붙는다)
  body.append(make("div", { className: "ex-kind",
    textContent: `${ex.element} · ${ex.skillType}` }));

  body.append(section("공식 — 이 순서로 곱해져 숫자가 됐다", formulaTable(ex.formula)));
  if (ex.stats.length) body.append(applySection("스탯 조립", ex.stats, statBlock));
  for (const g of ex.groups) body.append(applySection(g.label, g.fields, fieldBlock));
}

function section(title, ...kids) {
  return make("div", { className: "ex-sec" }, make("h3", { textContent: title }), ...kids);
}

// 이 히트에 실제로 들어가는 것만 펼치고, 나머지는 접어 둔다.
// 지우지 않는 이유 — 걸릴 줄 알았던 버프가 왜 안 걸렸는지가 대개 알고 싶은 것이다.
function applySection(title, items, render) {
  const on  = items.filter((x) => x.applied);
  const off = items.filter((x) => !x.applied);
  const sec = section(title, ...on.map(render));

  if (off.length) {
    const box = make("details", { className: "ex-off" },
      make("summary", { textContent: `이 히트엔 안 걸림 ${off.length}개` }));
    for (const x of off) box.append(render(x));
    sec.append(box);
  }
  if (!on.length && !off.length) return make("div");
  return sec;
}

// 항목은 한국어 이름으로 읽고, 엔진의 원래 term은 그 옆에 흐리게 남긴다
// (스탯 조립·보너스 풀은 필드명을 그대로 쓰므로 둘을 이어 볼 수 있어야 한다).
function formulaTable(steps) {
  const t = make("table");
  table(t, ["항목", "값", "비고"],
        steps.map((s) => [termCell(s), fmt(s.value), s.note || ""]));
  return t;
}

function termCell(s) {
  const cell = make("span", {}, make("span", { textContent: s.label }));
  if (s.term !== s.label) cell.append(make("span", { className: "term", textContent: s.term }));
  return cell;
}

// 공격력 2,737 = 1,033 × (1 + 1.303) + 358  — 그 아래 조각별 기여
function statBlock(s) {
  const line = `${s.label} ${fmt(s.final)} = ${fmt(s.base)} × (1 + ${fmt(s.pct)}) + ${fmt(s.flat)}`;
  return make("div", { className: "ex-field" },
    make("div", { className: "head" }, make("span", { className: "nm", textContent: line })),
    ...s.components.map(fieldBlock));
}

function fieldBlock(fb) {
  const head = make("div", { className: "head" },
    make("span", { className: "nm", textContent: fb.field }));
  if (fb.baseline) head.append(make("span", { className: "base", textContent: `기본 ${fmt(fb.baseline)}` }));
  head.append(make("span", { textContent: fmt(fb.total) }));

  const parts = make("div", { className: "ex-parts" });
  for (const p of [...fb.parts].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))) {
    parts.append(make("div", {},
      make("span", { className: "src", textContent: p.source + (p.note ? ` (${p.note})` : "") }),
      make("span", { textContent: signed(p.delta) })));
  }
  // 기록된 기여로 설명되지 않는 몫. 두 가지가 섞이지 않게 갈라 적는다.
  //  · 선언 필드(계수 등): 히트가 만들어질 때 박힌 값이라 원장에 없는 게 정상이다.
  //    버프가 얹히기도 한다 — 스커크 뱀의 계략은 coeff에 더하므로 기여 + 선언값으로 갈린다.
  //  · 그 밖: 아직 add()로 마이그레이션되지 않은 버프다. 엔진이 옮겨 갈수록 0으로 수렴한다.
  if (Math.abs(fb.remainder) > 1e-6) {
    parts.append(make("div", { className: fb.declared ? "" : "rest" },
      make("span", { className: "src", textContent: fb.declared ? "선언값" : "미계측(기타)" }),
      make("span", { textContent: signed(fb.remainder) })));
  }

  const d = make("div", { className: "ex-field" }, head);
  if (parts.childElementCount) d.append(parts);
  return d;
}

$("explainclose").onclick = () => $("explain").close();
$("editorclose").onclick = () => closeEditor();
$("editor").addEventListener("close", () => { editing = null; });   // Esc로 닫힌 경우
$("reset").onclick = () => { answers = {}; recalc(); };
$("target").onchange = (e) => { target = e.target.value; recalc(); };
$("enemylv").onchange = (e) => { enemyLevel = Number(e.target.value); recalc(); };

boot();
