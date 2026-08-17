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
let icons = null;         // icons.json — 한글 이름 → 게임 아이콘 파일명 (tools/build_icon_map.py)
let party = [];           // 빌드시트 spec 배열
let answers = {};
// 히트별 상황 반응 — { 캐릭터명: { 히트명: "VAPORIZE" } }.
// 파티가 바뀌어 불가능해진 선택은 엔진이 무반응으로 되돌려 보내므로(_selected_reaction)
// 여기서 지우지 않는다. 버튼의 눌림 상태는 저장값이 아니라 엔진이 되돌려준 값으로 그린다.
let hitReactions = {};
// 달·별 반응의 치명타 — { 반응id: { 캐릭터명: true } }. 참여자마다 판정이 따로 굴러가므로
// 파티 단위 스위치로 묶으면 「전원 크리」와 「전원 비크리」 두 조합만 표현된다.
// 참여자가 바뀌어 사라진 이름은 엔진이 무시하므로(_crit_chars) 여기서 지우지 않는다.
// 계열마다 따로 둔다 — 달감전과 별 확산은 서로 다른 피해 인스턴스다.
let lunarCrits = {};
let stellarCrits = {};
// 파티 공용 반응 계열. 키는 엔진의 damage 딕셔너리 키이자 설명 payload 의 kind 값이다
// (web_api._PARTY_REACTION_FAMILIES와 같은 키를 쓴다). 계열이 늘면 여기 한 줄만 추가한다.
const PARTY_REACTIONS = [
  { kind: "lunar",   label: "달반응",  crits: () => lunarCrits },
  { kind: "stellar", label: "별 반응", crits: () => stellarCrits },
];
const partyReactionFamily = (kind) => PARTY_REACTIONS.find((f) => f.kind === kind);
// 데미지 표에 보일 캐릭터. null = 아직 손대지 않음 = 파티 전원(파티원이 늘면 같이 는다).
// 칩을 한 번이라도 건드리면 Set 으로 굳고, 그 뒤로는 새 파티원이 저절로 끼어들지 않는다 —
// 딜러 둘을 나란히 보려고 골라 뒀는데 버퍼를 넣었다고 표가 흔들리면 곤란하다.
// 빈 Set 은 「전원」이 아니라 「아무도 안 봄」이다. 엔진의 빈 targets 와 뜻이 다르다.
let dmgTargets = null;
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

// 숫자 입력에 「어디까지 넣을 수 있는가」를 붙인다. 상한이 input의 max 속성에만
// 있으면 화면에 안 보여서, 넘겨 친 뒤에야(혹은 조용히 잘린 뒤에야) 알게 된다.
//
// button: [최대] 버튼을 단다. 값을 넣고 입력의 change 이벤트를 그대로 태우므로
//   반영 경로가 둘로 갈리지 않는다 — 부르는 쪽은 onchange만 달아 두면 된다.
//   상황 질문처럼 상한이 매번 다른(그래서 최대치가 얼마인지도 모르는) 입력에만 준다.
// bonus: 상한 위에 얹히는 몫(명함 특성 상승 +3). 상자의 max를 13으로 올리지 않는
//   이유는, 그러면 10과 13이 똑같은 결과를 내는 두 입력이 되어 무엇이 참인지 알 수
//   없게 되기 때문이다. 손으로 올리는 값은 10까지고, 나머지는 엔진이 더한다.
function numField(input, max, { min = null, button = false, bonus = 0, bonusFrom = "" } = {}) {
  input.max = max;
  if (min !== null) input.min = min;

  // 상한은 「+3/13」처럼 한 덩이로 적는다 — 얹히는 몫과 그래서 얼마가 되는지가
  // 나란히 붙어 있어야 읽힌다. 얹히는 몫이 없으면 그냥 「/10」이다.
  const lim = make("span", { className: "lim" });
  if (bonus) {
    lim.title = `기본 ${max} + ${bonusFrom}의 +${bonus} = 실효 최대 ${max + bonus} ` +
                `(손으로 올리는 값은 ${max}까지 — 나머지는 엔진이 더한다)`;
    lim.append(make("span", { className: "bon", textContent: `+${bonus}` }));
  }
  lim.append(min === null ? `/${max + bonus}` : `${min}~${max}`);
  const box = make("span", { className: "numf" }, input, lim);

  if (button) {
    const btn = make("button", { type: "button", className: "mini", textContent: "최대",
                                 title: `최대치 ${max} 를 채웁니다` });
    btn.disabled = input.disabled;
    btn.onclick = () => {
      input.value = max;
      input.dispatchEvent(new Event("change"));
    };
    box.append(btn);
  }
  return box;
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
    settings: { hitReactions, lunarCrits, stellarCrits, targets: selectedTargets(), ...extra },
  };
}

// 지금 고른 대상 — 손대지 않았으면(null) 파티 전원으로 편다. 엔진에는 이렇게 편 목록을
// 보낸다. 일부만 골랐을 때 나머지 캐릭터의 히트 평가를 엔진이 실제로 건너뛰게 하려면
// 「빈 목록 = 전원」에 기대지 말고 이름을 다 적어 보내야 한다.
function selectedTargets() {
  return partyNames().filter((n) => !dmgTargets || dmgTargets.has(n));
}

// 이름으로 접은 파티. 같은 캐릭터를 두 슬롯에 넣어도 대상으로서는 한 사람이다 —
// 엔진도 targets 를 이름으로 거른다(_damage).
const partyNames = () => [...new Set(party.map((c) => c.character))];

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
    status_.textContent = "Pyodide 런타임 내려받는 중…";
    const py = await loadPyodide();

    const tRuntime = performance.now();
    status_.textContent = "엔진 번들 푸는 중…";
    const zip = await (await fetch("engine.zip", { cache: "no-cache" })).arrayBuffer();
    py.unpackArchive(zip, "zip");

    status_.textContent = "엔진 임포트 중…";
    api = py.pyimport("gidc.web_api");
    reg = unwrap(api.get_registries());

    // 아이콘 맵은 그림이 아니라 파일명 표(15KB)다. 없어도 계산은 그대로 돌아가고
    // 카드가 글자 폴백으로 뜰 뿐이라, 실패해도 초기화를 멈추지 않는다.
    icons = await fetch("icons.json").then((r) => (r.ok ? r.json() : null)).catch(() => null);

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

// ── 왼쪽 탭 ──────────────────────────────────────────────────────────────
// 파티와 상황 질문은 둘 다 「입력」이고 오른쪽 칸(스탯·데미지)이 그 결과다.
// 세로로 늘어놓으면 답을 보려고 계속 스크롤하게 되므로 한 자리를 나눠 쓴다.
// 탭을 저절로 바꾸지는 않는다 — 계산할 때마다 화면이 옮겨 다니면 편집하던 자리를 잃는다.
const TABS = ["party", "questions"];

function showTab(name) {
  for (const t of TABS) {
    const on = t === name;
    const btn = $(`tabbtn-${t}`);
    btn.setAttribute("aria-selected", on ? "true" : "false");
    // 고르지 않은 탭은 Tab 키 순회에서 빼 둔다 — 탭 사이는 화살표로 옮기는 것이 관례다.
    btn.tabIndex = on ? 0 : -1;
    $(`tab-${t}`).hidden = !on;
  }
}

function wireTabs() {
  TABS.forEach((name, i) => {
    const btn = $(`tabbtn-${name}`);
    btn.onclick = () => showTab(name);
    btn.onkeydown = (e) => {
      const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      e.preventDefault();
      const next = TABS[(i + step + TABS.length) % TABS.length];
      showTab(next);
      $(`tabbtn-${next}`).focus();
    };
  });
  showTab("party");
}

// ── 파티 ─────────────────────────────────────────────────────────────────
function renderParty() {
  const box = $("party");
  box.innerHTML = "";

  party.forEach((c, i) => box.append(buildCard(c, i)));

  // 추가하는 캐릭터는 맨몸으로 들어온다 — 무기도 성유물도 없는 기본 스펙.
  // 프리셋으로 넣으면 남이 짜 둔 빌드가 딸려 와서, 내 빌드를 넣으려면 먼저 지워야 한다.
  // 목록은 등록된 캐릭터 전부다 (프리셋이 있든 없든).
  if (party.length < MAX_PARTY) {
    const add = make("button", { type: "button", textContent: "+ 캐릭터 추가" });
    add.onclick = () => openCharPicker(null, (name) => {
      party.push(unwrap(api.blank_sheet(name)));
      structuralChange();
    });
    box.append(make("div", { className: "slot" }, add));
  }

  // 탭 이름 옆에 붙는 값이라 짧게 — 자세한 것은 각 패널 안에서 말한다.
  $("partycount").textContent = `${party.length}/${MAX_PARTY}`;

  renderTargets();
}

// 데미지 대상 칩. 상황 질문의 다중 선택 위젯(widget)과 같은 모양을 쓴다 —
// <select multiple>을 안 쓰는 이유는 거기 적어 두었다.
function renderTargets() {
  const box = $("targets");
  box.innerHTML = "";

  // 파티에서 빠진 사람은 선택에서도 지운다. 손대지 않은 상태(null)는 그대로 둔다 —
  // 여기서 Set 으로 굳혀 버리면 그 뒤에 추가한 캐릭터가 표에 안 나온다.
  if (dmgTargets) {
    const alive = new Set(partyNames());
    for (const n of [...dmgTargets]) if (!alive.has(n)) dmgTargets.delete(n);
  }

  const picked = new Set(selectedTargets());
  for (const name of partyNames()) {
    const cb = make("input", { type: "checkbox", checked: picked.has(name) });
    const chip = make("label", { className: "chip" + (picked.has(name) ? " on" : "") },
                      cb, make("span", { textContent: name }));
    cb.onchange = () => {
      // 첫 클릭에서 「전원」이 명시적인 목록으로 굳는다.
      if (!dmgTargets) dmgTargets = new Set(partyNames());
      if (cb.checked) dmgTargets.add(name); else dmgTargets.delete(name);
      chip.classList.toggle("on", cb.checked);
      syncCardSelection();
      recalc();          // 대상 바꾸기는 구조 변경이 아니다 — 답변을 날리지 않는다
    };
    box.append(chip);
  }
}

// 카드의 선택 표시와 데미지 대상은 같은 상태를 본다. 칩을 눌렀을 때 파티를 통째로
// 다시 그리면 방금 누른 칩이 포커스를 잃으므로, 표시만 갈아 준다.
function syncCardSelection() {
  $("party").querySelectorAll(".bc").forEach((el, i) => {
    const on = !!(dmgTargets && party[i] && dmgTargets.has(party[i].character));
    el.classList.toggle("on", on);
    el.setAttribute("aria-selected", on ? "true" : "false");
  });
}

// ── 빌드 카드 ───────────────────────────────────────────────────────────
// 디자인 원본: Genshin Card Design/design_handoff_build_card/ (시안 1a). 모양·치수·상태는
// 그 README 가 확정값이고 여기서는 그대로 옮긴다. 카드가 말하는 것은 「무엇을 끼웠는가」
// 뿐이다 — 계산된 스탯과 성유물 주/부옵션은 넣지 않는다.
const SLOT_ORDER = [
  ["flower",  "꽃",   "꽃"],
  ["feather", "깃털", "깃"],
  ["sands",   "시계", "시"],
  ["goblet",  "성배", "잔"],
  ["circlet", "왕관", "관"],
];

const ELEMENT_COLOR = {
  불: "#d9603f", 물: "#3f8fd9", 얼음: "#3aa9c4", 번개: "#9a6fd0",
  바람: "#3fb094", 바위: "#c1922c", 풀: "#5da33f",
};

// 아이콘은 우리 서버를 거치지 않는다 — 브라우저가 CDN 에서 직접 받는다.
// yatta 쪽이 파일이 2.5배 작아 1순위고(21KB 대 41KB), 실패하면 enka 로 한 번 갈아탄다.
// 성유물만 yatta 에서 하위 경로에 있다 (enka 는 전부 평면).
const ICON_URL  = "https://gi.yatta.moe/assets/UI/";
const RELIC_URL = ICON_URL + "reliquary/";
const ICON_ALT  = "https://enka.network/ui/";

function iconOf(kind, name, slot) {
  const entry = icons && icons[kind] && icons[kind][name];
  const key = kind === "artifacts" ? entry && entry[slot] : entry;
  if (!key) return null;
  return { url: (kind === "artifacts" ? RELIC_URL : ICON_URL) + key + ".png",
           alt: ICON_ALT + key + ".png" };
}

// ── 캐릭터 선택 창 ───────────────────────────────────────────────────────
// [+ 캐릭터 추가]와 빌드 편집 창의 캐릭터 교체가 함께 쓴다. 드롭다운 대신 초상화
// 격자로 고르게 하는 이유: 이름만으로는 어느 캐릭터인지 한눈에 안 들어오고,
// 목록이 길어질수록(지금도 14명) 스크롤하며 글자를 읽는 쪽이 더 느리다.
let charPickerCurrent = null;   // 지금 이 슬롯에 있는 캐릭터 — 격자에서 테두리로 표시
let charPickerOnPick = null;    // (name) => void — 고른 뒤 부를 콜백

function openCharPicker(current, onPick) {
  charPickerCurrent = current;
  charPickerOnPick = onPick;
  $("charpickersearch").value = "";
  renderCharPicker("");
  $("charpicker").showModal();
  $("charpickersearch").focus();
}

function closeCharPicker() {
  charPickerOnPick = null;
  $("charpicker").close();
}

// 5성/4성만 있고 3성 이하는 없다 — 성급별 배경 색만 갈라 둔다(실제 게임의 금색/보라 카드 느낌).
const RARITY_BG = {
  5: ["#8a6a2f", "#4a3813"],
  4: ["#6a4f8a", "#382a4a"],
};

function renderCharPicker(filter) {
  const grid = $("charpickergrid");
  grid.innerHTML = "";
  const q = filter.trim().toLowerCase();
  const list = reg.characters.filter((c) => !q || c.name.toLowerCase().includes(q));

  if (!list.length) {
    grid.append(make("div", { className: "cp-empty", textContent: "일치하는 캐릭터가 없습니다." }));
    return;
  }

  for (const c of list) {
    const btn = make("button", {
      type: "button",
      className: "cp-item" + (c.name === charPickerCurrent ? " cur" : ""),
      title: c.name,
    });
    btn.style.setProperty("--ec", ELEMENT_COLOR[c.element] || "#8a8a8a");
    const [bg1, bg2] = RARITY_BG[c.rarity] || RARITY_BG[4];
    btn.style.setProperty("--cp-bg1", bg1);
    btn.style.setProperty("--cp-bg2", bg2);

    const src = iconOf("characters", c.name);
    if (src) {
      const img = make("img", { alt: "", loading: "lazy", decoding: "async" });
      img.dataset.alt = src.alt;
      // 카드 타일의 tile()과 같은 이유 — CDN이 죽어도 격자 칸의 크기·이름표는 남는다.
      img.onerror = () => {
        if (img.dataset.alt) { img.src = img.dataset.alt; img.dataset.alt = ""; return; }
        img.remove();
      };
      img.src = src.url;
      btn.append(img);
    }
    btn.append(
      make("span", { className: "badge", textContent: c.element.slice(0, 1) }),
      make("span", { className: "label", textContent: c.name }));

    btn.onclick = () => {
      const fn = charPickerOnPick;
      closeCharPicker();
      if (fn) fn(c.name);
    };
    grid.append(btn);
  }
}

function buildCard(c, i) {
  const meta = reg.characters.find((x) => x.name === c.character) || {};
  const card = make("div", { className: "bc", tabIndex: 0, role: "button" });
  card.style.setProperty("--ec", ELEMENT_COLOR[meta.element] || "#8a8a8a");

  // 데미지 대상을 「골라 둔」 상태에서만 선택 표시를 켠다. 손대지 않았을 때(=전원)
  // 네 장이 전부 원소색을 두르면 표시가 아무것도 구분해 주지 못한다.
  const picked = dmgTargets && dmgTargets.has(c.character);
  card.classList.toggle("on", !!picked);
  card.setAttribute("aria-selected", picked ? "true" : "false");

  card.append(cardTop(c, i, meta), cardGear(c));

  // 카드 전체가 빌드 편집 히트영역이다. 액션 버튼은 자기 클릭을 여기까지 올리지 않는다.
  card.onclick = () => openEditor(i);
  card.onkeydown = (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openEditor(i); }
  };
  return card;
}

function cardTop(c, i, meta) {
  const name = make("span", { className: "nm", textContent: c.character, title: c.character });
  const rowA = make("div", { className: "rowa" }, name);
  if (meta.element) rowA.append(make("span", { className: "tag", textContent: meta.element }));
  rowA.append(make("span", { className: "con", textContent: `C${c.constellation}`,
                             title: `운명의 자리 ${c.constellation}` }));

  const rowB = make("div", { className: "rowb" },
    make("span", { className: "lv", textContent: `Lv.${c.level}` }));
  for (const t of talents(c, meta)) {
    rowB.append(make("span", { className: "tal", title: t.title },
      make("span", { className: "lb", textContent: t.label }),
      make("b", { className: t.bonus ? "up" : "", textContent: t.text })));
  }

  const act = make("div", { className: "act" });
  for (const [label, title, fn] of [
    ["편집", "빌드 편집", () => openEditor(i)],
    ["삭제", "파티에서 제외", () => { closeEditor(); party.splice(i, 1); structuralChange(); }],
  ]) {
    const b = make("button", { type: "button", textContent: label, title });
    b.onclick = (e) => { e.stopPropagation(); fn(); };
    act.append(b);
  }

  return make("div", { className: "top" },
    tile("av", c.character.slice(0, 1), iconOf("characters", c.character), c.character),
    make("div", { className: "mid" }, rowA, rowB), act);
}

// 특성 셋. 명함으로 오르는 특성은 실효 레벨을 적고, 손으로 올린 값은 title 로 남긴다 —
// 상승 폭과 어느 명함이 올렸는지는 캐릭터마다 다르므로(모나는 C5가 스킬, 나비아는 반대)
// 규칙을 여기 베끼지 않고 엔진이 준 talentUp 표만 읽는다.
function talents(c, meta) {
  const up = meta.talentUp || {};
  return [
    ["평", "일반 공격",      c.naLevel,    up.na],
    ["E",  "원소전투 스킬",  c.skillLevel, up.skill],
    ["Q",  "원소폭발",       c.burstLevel, up.burst],
  ].map(([label, full, base, cno]) => {
    const bonus = cno && c.constellation >= cno ? (up.step || 0) : 0;
    return {
      label, bonus,
      text: bonus ? `${base + bonus}▲` : String(base),
      title: bonus
        ? `${full}: 손 ${base} + C${cno} 명함 +${bonus} = 실효 ${base + bonus}`
        : `${full}: ${base}`,
    };
  });
}

// 장비 행 — 무기와 성유물 5부위. 이름은 어느 것도 글자로 적지 않는다(툴팁에만).
// 한글 이름은 길이 편차가 커서(「판정」~「위대한 사막 현자의 대답」) 글자로 적으면
// 폭이 흔들리거나 잘려서 「페보니우스 검」과 「페보니우스 비전」이 같아진다.
function cardGear(c) {
  const w = c.weapon;
  const gear = make("div", { className: "gear" },
    tile("slot23", w ? w.name.slice(0, 1) : "무", w && iconOf("weapons", w.name),
         w ? `무기 — ${w.name} · R${w.refinement} · Lv.${w.level}` : "무기 — 비어 있음", !w),
    make("span", { className: "wlv", textContent: w ? `Lv.${w.level}·R${w.refinement}` : "" }),
    make("span", { className: "sep" }));

  const arts = c.artifacts || {};
  const slots = make("span", { className: "slots" });
  let filled = 0;
  for (const [key, label, short] of SLOT_ORDER) {
    const set = arts[key] && setLabel(arts[key].set);
    if (set) filled += 1;
    slots.append(tile("slot23", short, set && iconOf("artifacts", set, label),
                      set ? `${label} — ${set}` : `${label} — 비어 있음`, !set));
  }
  gear.append(slots,
    make("span", { className: "cnt", textContent: `${filled}/5`, title: `성유물 ${filled}/5 부위` }),
    make("span", { className: "sp" }));
  return gear;
}

// 폴백 글자를 이미지 뒤에 깔고 그 위에 이미지를 얹는다. 아이콘이 없거나(맵에 키가 없다)
// 못 받아도 타일의 크기와 글자는 남는다.
function tile(cls, fallback, src, title, empty = false) {
  // 폴백 글자는 눈으로 볼 때만 쓰는 것이다 — 읽어 주는 쪽에는 title 에 온전한 이름이
  // 있으므로, 여기까지 읽으면 「에 에스코피에」처럼 앞글자가 덧붙는다.
  const fb = make("span", { textContent: fallback });
  fb.setAttribute("aria-hidden", "true");
  const t = make("span", { className: `tile ${cls}${empty ? " empty" : ""}` }, fb);
  if (title) t.title = title;
  if (src) {
    const img = make("img", { alt: "", loading: "lazy", decoding: "async" });
    img.dataset.alt = src.alt;

    // 아이콘은 배경이 뚫린 PNG 라, 그림이 온 뒤에도 글자를 그대로 두면 뒤에서 비쳐 보인다.
    // 그래서 뜬 순간 글자를 감추고, 못 받으면 다시 드러낸다.
    img.onload = () => t.classList.add("has-img");
    // CDN 이 죽어도 카드가 무너지지 않게 — 한 번은 다른 CDN 으로 갈아타 보고,
    // 그것도 실패하면 이미지만 투명해져 글자가 남는다(높이 변화 0).
    img.onerror = () => {
      t.classList.remove("has-img");
      if (img.dataset.alt) { img.src = img.dataset.alt; img.dataset.alt = ""; return; }
      img.style.opacity = 0;
    };
    // src 는 핸들러를 단 뒤에 준다 — 캐시에 있는 그림은 붙이자마자 끝나 버려서,
    // 순서가 뒤바뀌면 load 를 놓치고 글자가 계속 남는다.
    img.src = src.url;
    t.append(img);
  }
  return t;
}

// 성유물 세트는 엔진이 enum 이름(GOLDEN_TROUPE)으로 준다. 아이콘 맵과 툴팁이 쓰는 것은
// 한글 라벨이라 레지스트리 표로 옮긴다 — 이름 대응을 JS 가 따로 들고 있지 않게.
function setLabel(id) {
  const found = reg.artifactSets.find((s) => s.id === id);
  return found ? found.label : null;
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

  // 캐릭터 교체. 카드에는 이름만 있고 고르는 자리가 없어서(카드는 보여주기만 한다)
  // 슬롯의 캐릭터를 바꾸는 자리는 여기다. 버튼을 누르면 [+ 캐릭터 추가]와 같은
  // 초상화 선택 창이 뜬다.
  const swap = make("button", { type: "button", textContent: c.character });
  swap.title = "이 슬롯의 캐릭터를 바꾼다 (빌드는 맨몸으로 다시 시작한다)";
  swap.onclick = () => openCharPicker(c.character, (name) => { swapCharacter(editing, name); });
  d.append(make("div", { className: "art-share" },
    make("span", { className: "name", textContent: "캐릭터" }), swap));

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

  const lv = make("input", { type: "number", value: c.level, min: 1 });
  lv.style.width = "4rem";
  lv.onchange = () => {
    c.level     = Number(lv.value);
    c.ascension = phaseFor(c.level, c.ascension);
    structuralChange(true);        // 레벨이 바뀌면 돌파 선택지 자체가 달라진다
  };
  row.append(make("label", { textContent: "레벨" }, numField(lv, reg.maxLevel)));

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

  // 명함 — 특성 레벨을 올리는 근거라, 바뀌면 특성 입력 옆의 「+3」도 따라 바뀌어야
  // 한다. 그래서 레벨과 같이 창을 다시 그린다.
  const con = make("input", { type: "number", value: c.constellation, min: 0 });
  con.style.width = "4rem";
  con.onchange = () => { c.constellation = Number(con.value); structuralChange(true); };
  row.append(make("label", { textContent: "명함" }, numField(con, 6)));

  // 특성 레벨 — 상자에 치는 것은 손으로 올리는 기본 레벨(1~10)이고, 명함 상승분은
  // 엔진이 그 위에 더한다. 어느 명함이 어느 특성을 올리는지는 캐릭터마다 달라
  // (모나는 C5가 스킬·C3가 폭발, 나비아는 반대) 엔진이 준 표를 읽는다.
  const up = meta.talentUp || {};
  for (const [key, label, at] of [
    ["naLevel", "평타", up.na], ["skillLevel", "E", up.skill], ["burstLevel", "Q", up.burst],
  ]) {
    const inp = make("input", { type: "number", value: c[key], min: 1 });
    inp.style.width = "4rem";
    inp.onchange = () => { c[key] = Number(inp.value); structuralChange(); };
    // 그 명함에 실제로 이르렀을 때만 적는다 — 아직 안 열린 +3을 최대치에 얹으면
    // 화면의 숫자가 이 빌드의 것이 아니게 된다.
    const on = at && c.constellation >= at;
    row.append(make("label", { textContent: label },
      numField(inp, reg.maxTalentLevel,
               { bonus: on ? up.step : 0, bonusFrom: `명함 ${at}` })));
  }
  d.append(row);

  // 획득 가능 특성 (니콜의 마도 등)
  if (meta.unlockableTraits && meta.unlockableTraits.length) {
    const trow = make("div", { className: "row" });
    // 상황 질문의 다중 선택과 같은 칩이다 — 켜진 것이 한눈에 보이고, 글자든 여백이든
    // 칩 안 아무 데나 누르면 토글된다.
    for (const t of meta.unlockableTraits) {
      const info = reg.traits.find((x) => x.id === t);
      const on = (c.traits || []).includes(t);
      const cb = make("input", { type: "checkbox", checked: on });
      const chip = make("label", { className: "chip" + (on ? " on" : "") },
                        cb, make("span", { textContent: info ? info.label : t }));
      cb.onchange = () => {
        c.traits = cb.checked ? [...(c.traits || []), t]
                              : (c.traits || []).filter((x) => x !== t);
        chip.classList.toggle("on", cb.checked);
        structuralChange();
      };
      trow.append(chip);
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
    structuralChange(true);   // 레벨/돌파/재련 입력의 활성 여부와 선택지가 바뀐다
  };
  const rsel = opt([1, 2, 3, 4, 5], c.weapon ? c.weapon.refinement : 1,
                   (x) => x, (x) => "재련 " + x);
  rsel.disabled = !c.weapon;
  rsel.onchange = () => { if (c.weapon) { c.weapon.refinement = Number(rsel.value); structuralChange(); } };
  wrow.append(make("label", { textContent: "무기" }, wsel), rsel);
  d.append(wrow);

  // 무기 레벨 / 돌파 — 캐릭터 레벨과 같은 규칙이고, 상한만 성급으로 갈린다
  // (1·2성은 Lv.70/4돌파에서 끝난다). 무기가 없으면 잠가 두되 숨기지는 않는다.
  const wrule = weaponRule(c.weapon && c.weapon.name);
  const wlrow = make("div", { className: "row" });

  const wlv = make("input", {
    type: "number", value: c.weapon ? c.weapon.level : "", min: 1,
  });
  wlv.style.width = "4rem";
  wlv.disabled = !c.weapon;        // numField가 [최대] 버튼도 같이 잠근다 — 먼저 정해야 한다
  wlv.onchange = () => {
    if (!c.weapon) return;
    c.weapon.level = Number(wlv.value);
    Object.assign(c.weapon, weaponLevelFor(c.weapon));
    structuralChange(true);        // 레벨이 바뀌면 돌파 선택지 자체가 달라진다
  };
  wlrow.append(make("label", { textContent: "무기 레벨" }, numField(wlv, wrule.maxLevel)));

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
    setQuestionCount("", "파티를 편성하세요");
    $("dmgtarget").textContent = "";
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

  // 엔진은 빈 targets 를 「전원」으로 읽는다(_damage). 하나도 안 고른 상태를 그쪽에
  // 표현할 방법이 없어서 그 한 경우만 여기서 비운다.
  const picked = selectedTargets();
  renderDamage(picked.length ? out.damage : { chars: [], lunar: [], stellar: [] });

  const who = !picked.length ? "선택 없음"
            : picked.length === partyNames().length ? "전원"
            : picked.join(", ");
  $("dmgtarget").textContent = `— ${who} · 히트를 누르면 근거`;
  if (out.errors.length) {
    setQuestionCount("오류", "빌드 오류");
  } else {
    setQuestionCount(
      out.pending.length ? `미답 ${out.pending.length}` : "",
      `총 ${out.questions.length}개 중 미답 ${out.pending.length}개 · 계산 ${ms.toFixed(0)}ms`);
  }
}

// 탭에는 눈에 걸릴 것(미답 개수)만 짧게 걸고, 자세한 줄은 패널 안에 둔다.
// 다 답했으면 탭에서 지운다 — 「미답 0」이 계속 붙어 있으면 배지가 아니라 장식이 된다.
function setQuestionCount(badge, detail) {
  $("qcount").textContent = badge;
  $("qinfo").textContent = detail;
}

// ── 질문 ─────────────────────────────────────────────────────────────────
function renderQuestions(questions, pending, stale) {
  const pendingSet = new Set(pending), staleSet = new Set(stale);
  const box = $("questions");
  box.innerHTML = "";

  for (const q of questions) {
    // 예/아니오 질문은 카드 통째가 체크박스의 라벨이다 — 작은 네모를 정확히 겨눌
    // 필요 없이 아무 데나 누르면 켜지고 꺼진다. (다른 종류는 카드 안에 드롭다운·숫자
    // 입력이 들어가므로 카드 클릭을 가로채면 오히려 방해가 된다.)
    const tap = q.kind === "bool";
    const div = make(tap ? "label" : "div",
      { className: "q" + (tap ? " tap" : "") + (pendingSet.has(q.id) ? " pending" : "") });

    // 라벨 안에 라벨을 넣을 수 없어 문구는 <div>로 둔다 (칩·체크박스는 각자 라벨이다).
    // 성유물 질문의 착용자는 엔진이 문구 앞머리에 접어 보낸다 — 「[스커크·진사 왕생록
    // 4세트] …」. 같은 세트를 두 명이 끼면 문구가 완전히 같아지기 때문이다.
    const label = make("div", { className: "qp", textContent: q.prompt });
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
    // 스택 수·인원처럼 상한이 질문마다 다르다. 화면에 범위를 적어 두지 않으면
    // 몇까지 되는지 알 수 없어 최대치로 맞춰 보는 것부터 못 한다.
    const e = make("input", { type: "number", value: cur !== undefined ? cur : q.min });
    e.onchange = () => bump(Number(e.value));
    return numField(e, q.max, { min: q.min, button: true });
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

// 원마는 EM 스케일 버프(방식 B)와 반응 배율의 재료라, 값이 안 보이면 반응 피해가 왜
// 그 숫자인지 화면에서 이을 수가 없다. 다른 스탯과 달리 %가 아닌 실수치다.
function renderStats(stats) {
  table($("stats"), ["캐릭터", "공격력", "HP", "방어력", "원마", "치확", "치피", "충전"],
    stats.map((s) => [s.name, num(s.atk), num(s.hp), num(s.def), num(s.em),
                      pct(s.critRate), pct(s.critDmg), pct(s.energyRecharge)]));
}

// 캐릭터마다 블록 하나 — 그 캐릭터가 내는 피해가 히트든 반응이든 한자리에 모인다.
// 격변을 히트와 같은 표에 섞지 않는 이유는 열의 의미가 달라서다: 계수도 %피해 보너스도
// 안 타고, 반응 전용 치명타가 없으면 비크리와 크리가 같은 값이 된다.
function renderDamage(damage) {
  const box = $("damage");
  box.innerHTML = "";

  for (const block of damage.chars) {
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
    // 반응 행도 히트 행과 똑같이 눌러서 설명을 연다. 격변은 원마와 반응 보너스만으로
    // 숫자가 정해지는데 그 원마가 어디서 왔는지는 표만 봐서는 이을 수가 없다.
    box.append(buildTable(["반응", "피해 원소", "비크리", "크리", "기댓값"],
      block.reactions.map((r) => [r.label, r.element,
                                  num(r.nonCrit), num(r.crit), num(r.expected)]),
      (tr, i) => {
        const open = () => openExplainReaction(block.char, block.reactions[i]);
        tr.className = "hit";
        tr.tabIndex = 0;
        tr.title = "왜 이 데미지인지 보기";
        tr.onclick = open;
        tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } };
      }, 2));
  }

  for (const fam of PARTY_REACTIONS) renderPartyReaction(box, damage[fam.kind], fam);
}

// 파티 공용 반응 피해(달반응·별 반응)는 캐릭터 블록 밖에 둔다 — 트리거할 수 있는 파티원
// 여럿이 각자 피해를 넣고 그 가중합이 파티의 값이라, 누구 한 명의 블록에 넣으면 그 사람이
// 낸 피해로 읽힌다.
// 행이 비어 있으면 아무것도 그리지 않는다(전환 캐릭터가 없거나, 트리거를 아직 안 골랐다).
// 별 초전도는 여기 뜨지 않는다 — 반응 피해가 없어 엔진이 후보에서 빼기 때문이다
// (core.reaction.stellar_candidates). 초전도 행이 사라진 것은 별 초전도가 그것을 대체해서다.
function renderPartyReaction(box, rows, fam) {
  if (!rows || !rows.length) return;

  box.append(make("div", { className: "dmg-char", textContent: `${fam.label} (파티 공용)` }));
  box.append(make("div", { className: "dmg-sub",
    textContent: "반응 피해 (1회당, 트리거 가능한 파티원의 가중합)" }));
  // 「비크리/크리」 두 열을 두지 않는 이유: 치명타가 참여자마다 따로 굴러가므로 그 둘은
  // 2^N 조합 중 양 끝 하나씩일 뿐이다. 대신 조합을 직접 고르게 하고(치명타 열),
  // 고른 값(선택 피해)과 확률 기댓값을 나란히 둔다.
  box.append(buildTable(["반응", "피해 원소", "치명타", "선택 피해", "기댓값"],
    rows.map((r) => [r.label, r.element, critPicker(r, fam), num(r.selected), num(r.expected)]),
    (tr, i) => {
      const open = () => openExplainPartyRow(rows[i], fam.kind);
      tr.className = "hit";
      tr.tabIndex = 0;
      tr.title = "누가 얼마씩 넣었는지 보기";
      // 치명타 버튼은 행 클릭을 타고 올라가 설명 창까지 열지 않도록 막는다(히트 표와 같다).
      tr.onclick = (e) => { if (!e.target.closest("button")) open(); };
      tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } };
    }, 2));
}

// 참여자마다 치명타 토글 하나. 눌러 켜진 사람만 터진 것으로 계산한다.
// 눌림 상태는 저장값이 아니라 엔진이 되돌려준 share.critOn 으로 그린다 — 참여자가 바뀌어
// 사라진 이름이 남아 있어도 화면이 거짓말을 하지 않는다(reactionPicker와 같은 이유).
function critPicker(r, fam) {
  const box = make("span", { className: "rx" });
  const crits = fam.crits();
  for (const s of r.shares) {
    const b = make("button", { type: "button", className: "mini", textContent: s.char });
    if (s.critOn) b.classList.add("on");
    b.title = `${s.char} 치명타 ${s.critOn ? "켜짐" : "꺼짐"} — 비크리 ${num(s.nonCrit)} / 크리 ${num(s.crit)}`;
    b.onclick = () => {
      if (!crits[r.reaction]) crits[r.reaction] = {};
      crits[r.reaction][s.char] = !s.critOn;
      recalc();
    };
    box.append(b);
  }
  return box;
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

// ── 히트·반응 설명 ────────────────────────────────────────────────────────
// 행을 누르면 "왜 이 숫자인가"를 계산을 한 번 더 돌려서 받아 온다.
// 본 계산에 얹지 않고 따로 부르는 이유가 둘이다.
//
//  · settings.explain 은 히트 '이름'만 받는다. 같은 이름의 히트를 두 캐릭터가
//    가질 수 있어 targets 로 캐릭터를 좁혀야 엉뚱한 사람 설명이 나오지 않는다.
//    본 계산의 targets 를 건드리면 데미지 표까지 그 한 명으로 줄어든다.
//  · explain 을 켜면 엔진이 버프 기여를 기록하느라 느려진다. 누를 때만 켜면 된다.
//
// 답변(answers)은 지금 화면 그대로 넘긴다 — 표에 보이는 그 숫자를 설명해야 한다.
function runExplain(char, title, extra) {
  let out;
  try {
    out = unwrap(api.run_calculation(sheet({ targets: [char], ...extra }), answers));
  } catch (e) {
    fail("설명 계산 실패", e);
    return;
  }
  renderExplain(char, title, out.explain);
  $("explain").showModal();
}

const openExplain = (char, hit) => runExplain(char, hit, { explain: hit });

// 확산은 피해 원소별로 네 행이라 반응 이름만으로는 행이 특정되지 않는다 — 원소까지 보낸다.
const openExplainReaction = (char, r) =>
  runExplain(char, `${r.label} · ${r.element} 피해`,
             { explainReaction: { char, reaction: r.reaction, element: r.element } });

// 달·별 반응 행은 파티 공용이라 「누구의 설명인가」가 없다. char 는 **어느 참여자의 상세를
// 볼지**를 고르는 값이고, 데미지 표에서 처음 열 때는 가중치가 가장 큰 참여자를 준다
// (shares 는 피해 내림차순이다). 창 안의 참여자 표에서 다시 열면 그 사람으로 바뀐다.
//
// kind 는 계열을 가른다 — 엔진이 그것으로 후보 유도와 컨텍스트 빌더를 고르므로, 표에 있던
// 그 행과 같은 계열을 넘겨야 같은 숫자가 나온다(web_api._PARTY_REACTION_FAMILIES).
//
// title 을 부르는 쪽이 만드는 이유: 처음 열 때는 아직 페이로드가 없어 표의 행에서 짜야
// 하고, 다시 열 때는 페이로드의 ex.hit 이 이미 같은 문구다. 두 경로의 제목이 달라지면
// 같은 창인데 이름이 바뀐 것처럼 보인다.
const openExplainParty = (kind, reaction, title, element, char) =>
  runExplain(char, title,
             { explainReaction: { kind, char, reaction, element } });

// 처음 열 때 보여줄 상세의 주인은 순위 배수가 가장 큰 사람이다. shares 는 파티 순서라
// 첫 원소가 1등이 아니다 — 순위는 weight 가 말한다(치명타 선택에 따라 옮겨 다닌다).
const openExplainPartyRow = (r, kind) => openExplainParty(
  kind, r.reaction, `${r.label} (${r.element} 피해)`, r.element,
  r.shares.length ? r.shares.reduce((a, b) => (b.weight > a.weight ? b : a)).char : null);

// 파티 공용 반응 계열인지 — 달반응이든 별 반응이든 창의 모양이 같다(가중합 + 참여자 표).
const isPartyReaction = (ex) => !!ex && PARTY_REACTIONS.some((f) => f.kind === ex.kind);

function renderExplain(char, title, ex) {
  const partyRow = isPartyReaction(ex);
  // 파티 공용이라 앞에 사람 이름을 세우면 그 사람이 낸 피해로 읽힌다.
  $("explaintitle").textContent = partyRow ? `${title} · 파티 가중합` : `${char} · ${title}`;
  const body = $("explainbody");
  body.innerHTML = "";

  // 표에 있던 행이 사라지는 경우 — 답변이 바뀌어 히트 구성이 달라졌거나, 파티가 바뀌어
  // 그 반응이 더는 불가능해졌을 때다(엔진이 불가능한 반응은 설명하지 않는다).
  if (!ex) {
    body.append(make("div", { textContent:
      "이 행의 설명을 만들지 못했습니다. 답변이나 파티가 바뀌어 히트·반응이 사라졌을 수 있습니다 — 표를 다시 확인하세요." }));
    return;
  }

  const reaction = ex.kind === "reaction";
  // 맨 위 숫자는 **표에 있던 그 숫자**여야 한다 — 파티 공용 반응 행은 가중합이고, ex.result 는
  // 아래 상세의 주인 한 명 몫이라 다른 값이다. 이 계열은 비크리/크리 대신 「고른 조합」과
  // 기댓값을 적고, 양 끝값(전원 비크리 ~ 전원 크리)을 범위로 덧붙인다.
  const r = ex.result;
  body.append(make("div", { className: "ex-res", textContent: partyRow
    ? `선택 피해 ${num(ex.total.selected)} · 기댓값 ${num(ex.total.expected)}`
    : `비크리 ${num(r.nonCrit)} · 크리 ${num(r.crit)} · 기댓값 ${num(r.expected)}` }));
  if (partyRow) {
    body.append(make("div", { className: "ex-kind",
      textContent: `치명타 조합의 범위: 전원 비크리 ${num(ex.total.allNonCrit)} ~ 전원 크리 ${num(ex.total.allCrit)}` }));
  }
  // 어떤 보너스가 왜 안 걸리는지는 결국 이 줄로 갈린다 (원소 없는 평타 = 물리라 냉기 보너스가 안 붙는다).
  // 격변은 스킬 종류가 없는 대신, 버프 원장을 어느 히트에서 읽었는지를 밝힌다.
  body.append(make("div", { className: "ex-kind", textContent: partyRow
    ? `${ex.element} 피해 · ${partyReactionFamily(ex.kind).label} (파티 가중합)`
    : reaction
    ? `${ex.element} 피해 · 격변 반응 (버프는 「${ex.carrier}」에서 읽음)`
    : `${ex.element} · ${ex.skillType}` }));

  // 스탯 조립도 피해 보너스 풀도 통째로 접히는 이유를 유저가 눈치로 알아내게 두지 않는다.
  if (reaction) {
    body.append(make("div", { className: "ex-note", textContent:
      "격변은 계수·스탯·%피해 보너스·방어력 배율을 타지 않는다. 원마·반응 보너스·내성만 걸린다." }));
  }
  if (partyRow) {
    const label = partyReactionFamily(ex.kind).label;
    body.append(make("div", { className: "ex-note", textContent:
      `${label} 피해는 트리거할 수 있는 파티원 각자의 피해를 가중합한 값이다. 계수·스탯·%피해 보너스·방어력 배율은 타지 않고, 원마·${label} 기초 피해 증가·반응 피해 보너스·고저차가 걸린다. 치명타는 참여자마다 따로 굴러가므로 누가 터졌는지는 데미지 표의 치명타 버튼에서 고른다 — 가중치는 지분이 아니라 순위 배수라서, 크리로 피해 대소가 역전되면 1등 배수도 그 사람에게 옮겨간다.` }));
    body.append(shareSection(ex));
  }

  const noun = reaction || partyRow ? "반응" : "히트";
  body.append(section(partyRow
    ? `공식 — 「${ex.char}」 몫이 이렇게 계산됐다 (가중치 적용 전)`
    : "공식 — 이 순서로 곱해져 숫자가 됐다", formulaTable(ex.formula)));
  if (ex.stats.length) body.append(applySection("스탯 조립", ex.stats, statBlock, noun));
  for (const g of ex.groups) body.append(applySection(g.label, g.fields, fieldBlock, noun));
}

function section(title, ...kids) {
  return make("div", { className: "ex-sec" }, make("h3", { textContent: title }), ...kids);
}

// 가중치 내역 — 누가 어떤 순위 배수로 얼마를 넣었는지. 아래 상세는 이 중 한 명의 것이므로
// 행을 눌러 주인을 바꿀 수 있다(현재 주인은 굵게 표시).
// 배수는 「선택 피해」 내림차순 순위로 붙고 정규화하지 않는다(1등 100%, 2등 50%, 3·4등 8.3%).
// 행 순서는 파티 순서로 고정이다 — 순위는 가중치 열이 말한다. 합계를 적는 이유는 이 값이
// 지분이 아니라 배수라서 합이 1이 아니라는 사실이 보여야 하기 때문이다.
function shareSection(ex) {
  const shares = ex.shares || [];
  const sum = shares.reduce((a, s) => a + s.weight, 0);
  // 치명타 열은 여기서는 **읽기 전용**이다 — 토글은 데미지 표에 있다. 창 안에 또 두면
  // 같은 값을 두 군데서 바꾸게 되고, 창을 다시 그릴 때마다 초점이 튄다.
  const t = buildTable(["캐릭터", "순위 배수", "치명타", "비크리", "크리", "선택 피해", "기여"],
    shares.map((s) => [s.char, pct(s.weight), s.critOn ? "터짐" : "—",
                       num(s.nonCrit), num(s.crit), num(s.selected),
                       num(s.weight * s.selected)]),
    (tr, i) => {
      const s = shares[i];
      tr.className = s.char === ex.char ? "hit on" : "hit";
      tr.tabIndex = 0;
      tr.title = `「${s.char}」 몫의 근거 보기`;
      // 반응 식별자는 페이로드가 갖고 있다 — 표시명에서 되짚지 않는다.
      const open = () => openExplainParty(ex.kind, ex.reaction, ex.hit, ex.element, s.char);
      tr.onclick = open;
      tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } };
    }, 2);
  return section(`참여자 순위 배수 (합 ${pct(sum)} — 지분이 아니라 배수라 1이 아니다)`, t);
}

// 이 히트(반응)에 실제로 들어가는 것만 펼치고, 나머지는 접어 둔다.
// 지우지 않는 이유 — 걸릴 줄 알았던 버프가 왜 안 걸렸는지가 대개 알고 싶은 것이다.
function applySection(title, items, render, noun = "히트") {
  const on  = items.filter((x) => x.applied);
  const off = items.filter((x) => !x.applied);
  const sec = section(title, ...on.map(render));

  if (off.length) {
    const box = make("details", { className: "ex-off" },
      make("summary", { textContent: `이 ${noun}엔 안 걸림 ${off.length}개` }));
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
$("charpickerclose").onclick = () => closeCharPicker();
$("charpicker").addEventListener("close", () => { charPickerOnPick = null; });   // Esc로 닫힌 경우
$("charpickersearch").oninput = (e) => renderCharPicker(e.target.value);
$("reset").onclick = () => { answers = {}; recalc(); };
$("enemylv").onchange = (e) => { enemyLevel = Number(e.target.value); recalc(); };
wireTabs();

boot();
