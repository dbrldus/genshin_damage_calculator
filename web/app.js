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
// 히트별 상황 반응 — { 캐릭터명: { 히트명: "VAPORIZE" } }.
// 파티가 바뀌어 불가능해진 선택은 엔진이 무반응으로 되돌려 보내므로(_selected_reaction)
// 여기서 지우지 않는다. 버튼의 눌림 상태는 저장값이 아니라 엔진이 되돌려준 값으로 그린다.
let hitReactions = {};
let target = "";
let enemyLevel = 100;
let editing = null;       // 빌드 창이 열려 있는 파티 인덱스 (닫혀 있으면 null)
// 지금 편집 중인 슬롯이 어느 저장 빌드에서 왔는가 (드롭다운의 선택 표시 + 저장할 때
// 기본 이름). 빌드 창은 구조가 바뀔 때마다 통째로 다시 그려지므로 선택 상태를
// DOM이 아니라 여기서 복원해야 한다.
let editorBuildName = null;

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
    // 캐릭터 레벨은 여기서 보내지 않는다 — 방어력/반응 레벨 배율은 때리는 캐릭터
    // 자신의 레벨로 정해지므로 엔진이 party[i].level 을 직접 읽는다. 하나로 뭉치면
    // 레벨이 섞인 파티에서 틀리고, Lv.80 을 90 으로 계산하면 피해가 2.78% 부풀려진다.
    settings: { hitReactions, targets: target ? [target] : [], ...extra },
  };
}

// PyProxy -> 순수 JS 객체. 파이썬 dict를 JS 객체로 바꾸고 프록시는 즉시 해제한다.
function unwrap(proxy) {
  const out = proxy.toJs({ dict_converter: Object.fromEntries });
  proxy.destroy();
  return out;
}

const msgOf = (e) => (e && e.message ? e.message : String(e));

function fail(what, e) {
  status_.className = "err";
  status_.textContent = what + ":\n" + msgOf(e);
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

    // 빈 파티로 시작한다. 예시 조합을 깔아 두면 내 파티를 짜기 전에 남의 빌드를 먼저
    // 지워야 하고, 화면의 숫자가 내 것인지 예시인지 헷갈린다.
    party = [];

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

  // 추가하는 캐릭터는 맨몸으로 들어온다 — 무기도 성유물도 없는 기본 스펙.
  // 프리셋으로 넣으면 남이 짜 둔 빌드가 딸려 와서, 내 빌드를 넣으려면 먼저 지워야 한다.
  // 목록은 등록된 캐릭터 전부다 (프리셋이 있든 없든).
  if (party.length < MAX_PARTY) {
    const add = make("select");
    add.add(new Option("+ 캐릭터 추가", ""));
    for (const c of reg.characters) add.add(new Option(c.name, c.name));
    add.onchange = () => {
      if (!add.value) return;
      party.push(unwrap(api.blank_sheet(add.value)));
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
  // 상한 레벨은 같은 Lv 표기로 두 상태가 존재하므로 돌파를 함께 적는다 —
  // 파티 카드만 보고 Lv80 5돌파와 Lv80 6돌파를 구분할 수 있어야 한다.
  const forked = (reg.ascensionPhases[c.level] || []).length > 1;
  const lv = `Lv${c.level}` + (forked ? `·${c.ascension}돌파` : "");
  return `${lv} C${c.constellation} · ${weaponSummary(c.weapon)} · 성유물 ${arts}/5`;
}

// 무기는 만렙이 기본이라 그때는 레벨을 적지 않는다 — 늘 붙어 있으면 눈에 안 들어와서,
// 정작 만렙이 아닌 무기를 끼웠을 때 알아채지 못한다.
function weaponSummary(w) {
  if (!w) return "무기 없음";
  const rule = weaponRule(w.name);
  if (w.level == null || w.level === rule.maxLevel) return w.name;
  const forked = (rule.phases[w.level] || []).length > 1;
  return `${w.name} Lv${w.level}` + (forked ? `·${w.ascension}돌파` : "");
}

// 캐릭터를 바꾸면 그 캐릭터의 맨몸 빌드로 갈아 끼운다 — [+ 캐릭터 추가]와 같은 출발점이다.
// 앞 캐릭터의 레벨·성유물을 물려주지 않는 이유: 다른 캐릭터를 골랐다는 건 이 슬롯을
// 새로 짜겠다는 뜻이고, 물려받은 값은 내가 정한 것처럼 보이면서 실은 남의 빌드 잔해다.
// (무기는 어차피 종류가 안 맞으면 엔진이 거부한다.)
function swapCharacter(i, name) {
  party[i] = unwrap(api.blank_sheet(name));
  editorBuildName = null;
  structuralChange(true);
}

// ── 빌드 편집 창 ─────────────────────────────────────────────────────────
function openEditor(i) {
  editing = i;
  editorBuildName = null;   // 슬롯이 바뀌었다 — 앞 슬롯에서 고른 이름을 물려받으면 안 된다
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

// 레벨이 바뀌면 돌파 단계를 다시 맞춘다. 지금 값이 새 레벨에서도 유효하면 건드리지 않고
// (Lv.80/6돌파 → Lv.85 는 그대로 6), 아니면 그 레벨의 기본값 = 돌파한 쪽으로 옮긴다.
// 가능한 단계 목록은 엔진이 준 표(reg.ascensionPhases)만 읽는다 — 규칙을 여기 베껴 두면
// 조용히 어긋난다. 표에 없는 레벨(범위 밖)은 그대로 두고 엔진이 오류로 잡게 한다.
function phaseFor(level, current) {
  const phases = reg.ascensionPhases[level];
  if (!phases || !phases.length) return current;
  return phases.includes(current) ? current : phases[phases.length - 1];
}

// 무기 쪽도 같은 일을 하되 표를 성급으로 한 번 더 고른다 — 1·2성만 Lv.70/4돌파에서
// 끝나기 때문이다. 무기를 안 골랐을 때도 입력을 그려야 해서 5성 표를 기본으로 준다.
function weaponRule(name) {
  const meta = name && reg.weapons.find((w) => w.name === name);
  return reg.weaponLevels[meta ? meta.rarity : 5];
}

// 무기의 (레벨, 돌파) 짝을 그 무기의 성급에서 유효한 값으로 맞춘다. 레벨을 바꿨을 때도,
// 상한이 다른 무기로 갈아 끼웠을 때도 같은 함수를 지난다 — 규칙이 한 곳에만 있게.
function weaponLevelFor(w) {
  const rule = weaponRule(w.name);
  // 레벨이 아직 없으면(무기를 막 골랐을 때) 만렙에서 시작하고, 있으면 1~상한으로 자른다.
  // 0이나 빈 칸을 만렙으로 되돌리지 않는 것이 중요하다 — 지우고 다시 치는 중에 값이
  // 90으로 튀면 무엇을 입력했는지 알 수 없다.
  const raw = Number(w.level);
  const level = w.level == null || Number.isNaN(raw)
    ? rule.maxLevel
    : Math.min(Math.max(Math.round(raw), 1), rule.maxLevel);
  const phases = rule.phases[level];
  return {
    ...w,
    level,
    ascension: phases.includes(w.ascension) ? w.ascension : phases[phases.length - 1],
  };
}

function buildEditor(c) {
  const meta = reg.characters.find((x) => x.name === c.character) || {};
  c.artifacts = c.artifacts || {};
  const d = make("div");

  // 빌드 주고받기 — 이 브라우저에 저장해 둔 빌드(왼쪽)와 JSON(오른쪽).
  // 드롭다운에는 지금 캐릭터로 저장한 빌드만 올린다. 다른 캐릭터 빌드까지 섞으면
  // 목록이 길어지는 데다, 골랐을 때 슬롯의 캐릭터까지 갈리는 게 예상 밖이다
  // (그건 [가져오기]가 하는 일이고 창에 그렇게 적혀 있다).
  const share = make("div", { className: "art-share" },
    make("span", { className: "name", textContent: "빌드" }));

  const saved = savedBuildsFor(c.character);
  const ssel = make("select");
  ssel.add(new Option(saved.length ? "(저장된 빌드 불러오기)" : "(저장된 빌드 없음)", ""));
  for (const e of saved) ssel.add(new Option(e.name, e.name));
  // 방금 불러온/저장한 빌드가 지워졌을 수도 있으니 목록에 있을 때만 고른 상태로 둔다.
  ssel.value = saved.some((e) => e.name === editorBuildName) ? editorBuildName : "";
  ssel.disabled = !saved.length;
  ssel.title = "저장해 둔 빌드를 이 슬롯에 불러옵니다";
  ssel.onchange = () => { if (ssel.value) loadSavedBuild(ssel.value); };
  share.append(ssel);

  const save = make("button", { className: "mini", textContent: "저장" });
  save.disabled = !storage();
  save.title = save.disabled
    ? "이 브라우저에서는 로컬 저장을 쓸 수 없습니다 (file:// 로 열었거나 시크릿 모드)"
    : "지금 빌드에 이름을 붙여 이 브라우저에 저장한다";
  save.onclick = () => saveCurrentBuild(c);
  share.append(save);

  // 지우는 대상은 드롭다운이 지금 가리키는 빌드다. 고른 게 없으면 잠가 둔다 —
  // 무엇을 지우는지 모르는 채로 눌리는 삭제 버튼이 제일 나쁘다.
  const del = make("button", { className: "mini", textContent: "삭제" });
  del.disabled = !ssel.value;
  del.title = ssel.value
    ? `저장된 "${ssel.value}" 을(를) 지웁니다 (슬롯에 적용된 빌드는 그대로)`
    : "지울 빌드를 드롭다운에서 먼저 고르세요";
  del.onclick = () => deleteSavedBuild(ssel.value);
  share.append(del);

  for (const [mode, label, title] of [
    ["export", "내보내기", "이 빌드를 JSON으로 복사한다"],
    ["import", "가져오기", "JSON을 붙여넣어 이 슬롯을 교체한다"],
  ]) {
    const b = make("button", { className: "mini", textContent: label, title });
    b.onclick = () => openShare(mode);
    share.append(b);
  }
  d.append(share);

  // 레벨 / 돌파 / 명함 / 특성 레벨
  const row = make("div", { className: "row" });

  const lv = make("input", { type: "number", value: c.level, min: 1, max: reg.maxLevel });
  lv.style.width = "4rem";
  lv.onchange = () => {
    c.level     = Number(lv.value);
    c.ascension = phaseFor(c.level, c.ascension);
    structuralChange(true);        // 레벨이 바뀌면 돌파 선택지 자체가 달라진다
  };
  row.append(make("label", { textContent: "레벨" }, lv));

  // 돌파 — 상한 레벨(20/40/50/60/70/80)에서만 두 갈래다. Lv.80/80(미돌파)과
  // Lv.80/90(돌파 완료)은 기초 스탯도 어센션 보너스도 다른 캐릭터라 물어봐야 한다.
  // 나머지 레벨은 단계가 하나뿐이라 잠가 둔다 — 값을 숨기지는 않는다(왜 이 스탯인지 보인다).
  const phases = reg.ascensionPhases[c.level] || [c.ascension];
  const asel = opt(phases, c.ascension, (p) => p, (p) => `${p}돌파`);
  asel.disabled = phases.length < 2;
  asel.title = phases.length < 2
    ? "이 레벨에서는 돌파 단계가 하나로 정해집니다"
    : "같은 레벨에 돌파 전/후 두 상태가 있습니다";
  asel.onchange = () => { c.ascension = Number(asel.value); structuralChange(); };
  row.append(make("label", { textContent: "돌파" }, asel));

  for (const [key, label, min, max] of [
    ["constellation", "명함", 0, 6],
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
    c.weapon = wsel.value
      ? weaponLevelFor({ name: wsel.value, refinement: c.weapon?.refinement || 1,
                         // 무기를 바꾸면 성급이 바뀌어 레벨 상한도 달라진다. 들고 있던
                         // 레벨을 그대로 물려주되 새 상한에 맞춰 자른다.
                         level: c.weapon?.level, ascension: c.weapon?.ascension })
      : null;
    structuralChange(true);   // 레벨/돌파/정련 입력의 활성 여부와 선택지가 바뀐다
  };
  const rsel = opt([1, 2, 3, 4, 5], c.weapon ? c.weapon.refinement : 1,
                   (x) => x, (x) => "정련 " + x);
  rsel.disabled = !c.weapon;
  rsel.onchange = () => { if (c.weapon) { c.weapon.refinement = Number(rsel.value); structuralChange(); } };
  wrow.append(make("label", { textContent: "무기" }, wsel), rsel);
  d.append(wrow);

  // 무기 레벨 / 돌파 — 캐릭터 레벨과 같은 규칙이고, 상한만 성급으로 갈린다
  // (1·2성은 Lv.70/4돌파에서 끝난다). 무기가 없으면 잠가 두되 숨기지는 않는다.
  const wrule = weaponRule(c.weapon && c.weapon.name);
  const wlrow = make("div", { className: "row" });

  const wlv = make("input", {
    type: "number", value: c.weapon ? c.weapon.level : "", min: 1, max: wrule.maxLevel,
  });
  wlv.style.width = "4rem";
  wlv.disabled = !c.weapon;
  wlv.onchange = () => {
    if (!c.weapon) return;
    c.weapon.level = Number(wlv.value);
    Object.assign(c.weapon, weaponLevelFor(c.weapon));
    structuralChange(true);        // 레벨이 바뀌면 돌파 선택지 자체가 달라진다
  };
  wlrow.append(make("label", { textContent: "무기 레벨" }, wlv));

  const wphases = c.weapon ? wrule.phases[c.weapon.level] || [c.weapon.ascension] : [];
  const wasel = opt(wphases, c.weapon ? c.weapon.ascension : "", (p) => p, (p) => `${p}돌파`);
  wasel.disabled = !c.weapon || wphases.length < 2;
  wasel.title = !c.weapon
    ? "무기를 먼저 고르세요"
    : wphases.length < 2
      ? "이 레벨에서는 돌파 단계가 하나로 정해집니다"
      : "같은 레벨에 돌파 전/후 두 상태가 있습니다 — 기본 공격력이 다릅니다";
  wasel.onchange = () => {
    if (c.weapon) { c.weapon.ascension = Number(wasel.value); structuralChange(); }
  };
  wlrow.append(make("label", { textContent: "무기 돌파" }, wasel));
  d.append(wlrow);

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
    else { c.artifacts[slot.key] = blankArtifact(slot, setSel.value); }
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

// 세트는 반드시 고른 값을 받는다. 기본값을 두면 (없음)에서 무언가를 고른 순간
// 그 선택이 목록 첫 세트로 바뀌어 버린다 — 다시 그릴 때 드롭다운은 화면에 남은 값이
// 아니라 여기서 만든 값을 읽기 때문이다.
function blankArtifact(slot, set) {
  const main = (reg.validMainStats[slot.key] || ["HP"])[0];
  const pool = reg.validSubStats;
  return {
    set,
    main: { stat: main, value: 0 },
    subs: [0, 1, 2, 3].map((i) => ({ stat: pool[i % pool.length], value: 0 })),
  };
}

const statLabel = (id) => (reg.statTypes.find((s) => s.id === id) || {}).label || id;

// ── 저장된 빌드 (localStorage) ───────────────────────────────────────────
// 저장하는 값은 [내보내기]가 뱉는 JSON 그대로에 이름표만 붙인 것이다. 저장·불러오기가
// export_build/import_build 를 그대로 지나므로 세 가지가 공짜로 따라온다.
//   · 깨진 빌드는 애초에 저장되지 않는다 (export_build 가 왕복하며 검증한다)
//   · 저장된 것은 반드시 다시 읽힌다
//   · 나중에 BUILD_VERSION 이 올라가도 import_build 가 항목별로 이유를 말해 준다
//     — 목록 전체가 못 쓰게 되지 않는다
// 그래서 저장 항목 하나를 그대로 복사해 [가져오기] 창에 붙여넣어도 동작한다.
//
// 키 하나에 전부 넣는다. 빌드마다 키를 쪼개면 목록을 만들 때 localStorage 전체를
// 훑어야 하고 남의 키와 섞인다. 빌드 하나가 1~2KB라 수백 개가 5MB 안에 들어간다.
const STORE_KEY = "gidc.builds.v1";

// localStorage 는 file:// 이나 시크릿 모드에서 접근 자체가 던진다. 없으면 저장 UI만
// 잠그고 나머지는 그대로 돈다 — 계산기는 저장 없이도 쓸 수 있어야 한다.
function storage() {
  try {
    localStorage.getItem(STORE_KEY);
    return localStorage;
  } catch {
    return null;
  }
}

// 읽다 실패하면 조용히 날리지 않고 옆으로 치워 둔다 — 콘솔에서 건져낼 수 있어야 한다.
// 치우지 않으면 다음 저장이 어차피 덮어써서 결과는 같고 흔적만 사라진다.
function loadEntries() {
  const ls = storage();
  const raw = ls && ls.getItem(STORE_KEY);
  if (!raw) return [];
  try {
    const data = JSON.parse(raw);
    if (!Array.isArray(data.entries)) throw new Error("entries 가 없습니다");
    return data.entries.filter((e) => e && e.name && e.character && e.payload);
  } catch (e) {
    try {
      ls.setItem(STORE_KEY + ".broken", raw);
      ls.removeItem(STORE_KEY);
    } catch { /* 공간이 없으면 치우지도 못한다 — 그래도 목록은 비워 두고 계속 간다 */ }
    console.error(`저장된 빌드를 읽지 못해 ${STORE_KEY}.broken 으로 옮겼습니다`, e);
    return [];
  }
}

function saveEntries(entries) {
  const ls = storage();
  if (!ls) throw new Error("이 브라우저에서는 로컬 저장을 쓸 수 없습니다.");
  ls.setItem(STORE_KEY, JSON.stringify(
    { format: "gidc.builds", version: 1, entries }, null, 2));
}

// 매번 읽는다. 캐시해 두면 다른 탭에서 저장한 빌드가 안 보인다 — 몇 KB 파싱이라
// 편집 창을 다시 그릴 때마다 해도 티가 안 난다.
const savedBuildsFor = (character) => loadEntries()
  .filter((e) => e.character === character)
  .sort((a, b) => a.name.localeCompare(b.name, "ko"));

// 이름 짓기는 귀찮은 일이라 기본값을 준다. 같은 캐릭터의 빌드는 대개 무기로 갈리므로
// 무기 이름을 쓰고, 이미 있으면 뒤에 번호를 붙인다.
function defaultBuildName(c) {
  const base = (c.weapon && c.weapon.name) || "빌드";
  const taken = new Set(savedBuildsFor(c.character).map((e) => e.name));
  if (!taken.has(base)) return base;
  for (let i = 2; ; i++) if (!taken.has(`${base} ${i}`)) return `${base} ${i}`;
}

// 저장은 (캐릭터, 이름) 하나를 차지한다. 캐릭터는 지금 슬롯에서 이미 알고 있으니
// 묻지 않고, 사용자가 대는 건 이름뿐이다.
function saveCurrentBuild(c) {
  let payload;
  try {
    payload = JSON.parse(api.export_build(c));      // 엔진 검증 + 정규화
  } catch (e) {
    alert("저장하지 못했습니다 — 빌드가 유효하지 않습니다.\n" + msgOf(e));
    return;
  }

  const name = (prompt(`${c.character} 빌드를 어떤 이름으로 저장할까요?`,
                       editorBuildName || defaultBuildName(c)) || "").trim();
  if (!name) return;

  const entries = loadEntries();
  const at = entries.findIndex((e) => e.character === c.character && e.name === name);
  if (at >= 0 && !confirm(`${c.character} "${name}" 을(를) 덮어씁니다. 계속할까요?`)) return;

  const entry = { name, character: c.character, savedAt: new Date().toISOString(), payload };
  if (at >= 0) entries[at] = entry; else entries.push(entry);

  try {
    saveEntries(entries);
  } catch (e) {
    alert("저장하지 못했습니다 — 저장 공간이 찼을 수 있습니다.\n" + msgOf(e));
    return;
  }
  editorBuildName = name;
  renderEditor();          // 드롭다운에 방금 저장한 이름이 잡히게
}

// 지우는 것은 저장 항목뿐이다 — 슬롯에 적용돼 있는 빌드는 건드리지 않는다.
// 그래서 「이름을 잘못 지었다」가 [저장] 후 [삭제]로 해결된다. 되돌리기가 없으므로
// 캐릭터와 이름을 확인 문구에 그대로 박아 무엇이 사라지는지 보이게 한다.
function deleteSavedBuild(name) {
  const c = party[editing];
  if (!confirm(`저장된 ${c.character} "${name}" 을(를) 지웁니다.\n` +
               `지금 슬롯에 적용된 빌드는 그대로 남습니다. 계속할까요?`)) return;

  const entries = loadEntries()
    .filter((e) => !(e.character === c.character && e.name === name));
  try {
    saveEntries(entries);
  } catch (e) {
    alert("지우지 못했습니다.\n" + msgOf(e));
    return;
  }
  editorBuildName = null;
  renderEditor();          // 드롭다운에서 사라지고 [삭제]가 다시 잠긴다
}

function loadSavedBuild(name) {
  const entry = savedBuildsFor(party[editing].character).find((e) => e.name === name);
  if (!entry) return;

  const text = JSON.stringify(entry.payload, null, 2);
  const out = applyBuildText(text, name);
  if (out.ok) return;

  // 저장할 땐 유효했어도 엔진에서 캐릭터·세트 이름이 바뀌면 깨질 수 있다. 그때는
  // 저장된 JSON을 채운 채 [가져오기] 창을 열어 준다 — 이유가 그 자리에 보이고,
  // 손으로 고쳐 적용할 수 있고, 오류를 띄울 자리를 편집 창에 새로 낼 필요도 없다.
  renderEditor();          // 실패했으므로 드롭다운 선택을 되돌린다
  openShare("import");
  $("sharetext").value = text;
  shareMsg(`저장된 "${name}" 을(를) 불러오지 못했습니다.\n` + out.message, "err");
}

// ── 빌드 JSON 주고받기 ───────────────────────────────────────────────────
// 캐릭터 한 명분만 오간다. 파티 전체가 아닌 이유는 web_api.py 의 BUILD_FORMAT 주석 —
// 상황 질문 답변은 질문 ID가 파티 구성과 엔진 소스 줄 번호에 묶여 있어 들고 나갈 수 없다.
//
// 형식 검사·정규화는 전부 파이썬이 한다(export_build/import_build). 여기서 JSON을
// 직접 뜯으면 캐릭터에 필드가 늘 때마다 조용히 어긋난다.
//
// 열려 있는 빌드 편집 창(editing)의 슬롯을 대상으로 한다 — 그 창에서만 열리는 창이다.
function openShare(mode) {
  if (editing === null) return;
  const c = party[editing];
  const ta = $("sharetext");
  const isExport = mode === "export";

  shareMsg("");
  $("sharetitle").textContent = isExport ? `${c.character} 빌드 내보내기` : "빌드 가져오기";
  $("sharehint").textContent = isExport
    ? "이 JSON을 그대로 넘기면 다른 브라우저에서도 같은 빌드가 됩니다."
    : "받은 빌드 JSON을 붙여넣고 [적용]을 누르세요. 이 슬롯이 통째로 교체됩니다 (캐릭터가 달라도 됩니다).";
  $("sharecopy").hidden = !isExport;
  $("shareapply").hidden = isExport;
  ta.readOnly = isExport;
  ta.value = "";

  if (isExport) {
    try {
      ta.value = api.export_build(c);
    } catch (e) {
      shareMsg("내보내지 못했습니다 — 빌드가 유효하지 않습니다.\n" + msgOf(e), "err");
    }
  }

  $("share").showModal();
  ta.focus();
  if (isExport && ta.value) ta.select();
}

function shareMsg(text, cls = "") {
  const m = $("sharemsg");
  m.textContent = text;
  m.className = cls;
}

// 빌드 JSON 한 덩이를 지금 슬롯에 적용한다. 붙여넣기와 저장된 빌드 불러오기가 같은
// 경로를 타야 검증도 오류 문구도 한 벌로 유지된다. 결과를 어디에 보여줄지는 부르는
// 쪽이 정한다 — 붙여넣기는 창 안에, 불러오기는 창을 열어서.
//
// fromName 은 이 빌드가 어느 저장 항목에서 왔는지 (붙여넣기면 null — 출처를 모른다).
function applyBuildText(text, fromName = null) {
  if (editing === null) return { ok: false, message: "" };
  let out;
  try {
    out = unwrap(api.import_build(text));
  } catch (e) {
    return { ok: false, message: "가져오기 실패:\n" + msgOf(e) };
  }
  if (out.errors.length) return { ok: false, message: out.errors.join("\n") };

  party[editing] = out.build;
  editorBuildName = fromName;
  structuralChange(true);          // 캐릭터·무기가 바뀌면 위젯 구성 자체가 달라진다
  return { ok: true, message: out.warnings.join("\n"), build: out.build };
}

// 오류면 창을 열어 둔 채 이유를 보여준다 — 붙여넣은 JSON이 남아 있어야 고칠 수 있다.
// 경고(파티 JSON에서 한 명만 가져옴 등)는 적용은 하되 창을 닫지 않고 무엇이 빠졌는지 알린다.
function applyShare() {
  const out = applyBuildText($("sharetext").value);
  if (!out.ok) {
    shareMsg(out.message, "err");
  } else if (out.message) {
    shareMsg(`${out.build.character} 빌드를 적용했습니다.\n` + out.message, "ok");
  } else {
    $("share").close();
  }
}

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
// numFrom 부터의 열에 숫자 정렬(tabular-nums)을 준다 — 데미지 표는 첫 열이 히트 이름,
// 둘째 열이 반응 버튼이라 셋째부터가 숫자다.
function fillTable(t, headers, rows, onRow, numFrom) {
  const tr = t.insertRow();
  headers.forEach((h) => tr.append(make("th", { textContent: h })));
  rows.forEach((row, i) => {
    const r = t.insertRow();
    row.forEach((c, j) => {
      const td = r.insertCell();
      if (typeof c === "string") td.textContent = c; else td.append(c);
      if (j >= numFrom) td.className = "num";
    });
    if (onRow) onRow(r, i);
  });
}

// 이미 있는 <table> 안에 그린다.
function table(node, headers, rows, onRow = null, numFrom = 1) {
  node.innerHTML = "";
  fillTable(node, headers, rows, onRow, numFrom);
}

// 새 <table> 을 만들어 돌려준다 (캐릭터마다 표가 여러 개인 데미지 화면용).
function buildTable(headers, rows, onRow = null, numFrom = 1) {
  const t = make("table");
  fillTable(t, headers, rows, onRow, numFrom);
  return t;
}

function renderStats(stats) {
  table($("stats"), ["캐릭터", "공격력", "HP", "방어력", "치확", "치피", "충전"],
    stats.map((s) => [s.name, num(s.atk), num(s.hp), num(s.def),
                      pct(s.critRate), pct(s.critDmg), pct(s.energyRecharge)]));
}

// 캐릭터마다 블록 하나 — 그 캐릭터가 내는 피해가 히트든 반응이든 한자리에 모인다.
// 격변을 히트와 같은 표에 섞지 않는 이유는 열의 의미가 달라서다: 계수도 %피해 보너스도
// 안 타고, 반응 전용 치명타가 없으면 비크리와 크리가 같은 값이 된다.
function renderDamage(damage) {
  const box = $("damage");
  box.innerHTML = "";

  for (const block of damage) {
    box.append(make("div", { className: "dmg-char", textContent: block.char }));

    box.append(buildTable(["히트", "반응", "비크리", "크리", "기댓값"],
      block.hits.map((h) => [h.hit, reactionPicker(block.char, h),
                             num(h.nonCrit), num(h.crit), num(h.expected)]),
      (tr, i) => {
        const open = () => openExplain(block.char, block.hits[i].hit);
        tr.className = "hit";
        tr.tabIndex = 0;
        tr.title = "왜 이 데미지인지 보기";
        // 반응 버튼은 행 클릭을 타고 올라가 설명 창까지 열지 않도록 막는다.
        tr.onclick = (e) => { if (!e.target.closest("button")) open(); };
        tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } };
      }, 2));

    if (!block.reactions.length) continue;

    // 「1회당」인 이유: 로테이션에서 반응이 몇 번 터지는지는 이 계산기의 범위 밖이다.
    box.append(make("div", { className: "dmg-sub", textContent: "반응 피해 (1회당)" }));
    box.append(buildTable(["반응", "피해 원소", "비크리", "크리", "기댓값"],
      block.reactions.map((r) => [r.label, r.element,
                                  num(r.nonCrit), num(r.crit), num(r.expected)]),
      null, 2));
  }
}

// 이 히트에 붙일 수 있는 반응 버튼. 후보는 엔진이 히트 원소와 파티 구성에서 유도해 준다
// — 얼음 히트에 증발을 고를 수 있으면 조용히 틀린 숫자가 나오기 때문이다.
// 후보가 비어 오는 경우: 원소가 없는 히트(물리), 오라를 깔 파티원이 없음,
// 히트가 반응을 내장함(이네파의 달감전 피해 — 골라도 안 바뀌므로 버튼을 내지 않는다).
function reactionPicker(char, h) {
  if (!h.candidates.length) return "";

  const btn = (id, label) => {
    const b = make("button", { type: "button", className: "mini", textContent: label });
    if (h.reaction === id) b.classList.add("on");
    b.onclick = () => {
      if (!hitReactions[char]) hitReactions[char] = {};
      hitReactions[char][h.hit] = id;
      recalc();
    };
    return b;
  };

  const box = make("span", { className: "rx" }, btn("NONE", "무반응"));
  for (const c of h.candidates) box.append(btn(c.id, c.label));
  return box;
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

$("shareclose").onclick = () => $("share").close();
$("shareapply").onclick = () => applyShare();
$("sharecopy").onclick = async () => {
  const ta = $("sharetext");
  ta.select();
  // 클립보드 API는 보안 컨텍스트(https / localhost)에서만 열린다. file:// 로 연 경우
  // 조용히 아무 일도 안 일어나는 대신 선택해 둔 채로 Ctrl+C 를 안내한다.
  try {
    await navigator.clipboard.writeText(ta.value);
    shareMsg("복사했습니다.", "ok");
  } catch {
    shareMsg("클립보드를 쓸 수 없습니다 — 선택된 내용을 Ctrl+C 로 복사하세요.", "err");
  }
};

$("explainclose").onclick = () => $("explain").close();
$("editorclose").onclick = () => closeEditor();
$("editor").addEventListener("close", () => { editing = null; });   // Esc로 닫힌 경우
$("reset").onclick = () => { answers = {}; recalc(); };
$("target").onchange = (e) => { target = e.target.value; recalc(); };
$("enemylv").onchange = (e) => { enemyLevel = Number(e.target.value); recalc(); };

boot();
