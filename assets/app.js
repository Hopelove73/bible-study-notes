/* =========================================================
   圣经精读笔记 · 公共脚本
   进度 / 主题 / 目录 / 任务 / 人物卡 / 测验  全部存 localStorage
   ========================================================= */
(function () {
  "use strict";

  var KEY = {
    theme: "bible.theme",
    tasks: "bible.tasks",
    done: "bible.chapters",
    notes: "bible.notes",
    mastery: "bible.mastery"
  };

  function load(k, d) {
    try { return JSON.parse(localStorage.getItem(k)) || d; } catch (e) { return d; }
  }
  function save(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {}
  }
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  /* ---------- 主题 ---------- */
  var root = document.documentElement;
  root.dataset.theme = load(KEY.theme, "light");
  var tbtn = $("#themeBtn");
  if (tbtn) {
    var paint = function () {
      tbtn.textContent = root.dataset.theme === "dark" ? "浅色" : "深色";
    };
    paint();
    tbtn.addEventListener("click", function () {
      root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
      save(KEY.theme, root.dataset.theme);
      paint();
    });
  }

  /* ---------- 阅读进度条 ---------- */
  var bar = $("#readbar");
  if (bar) {
    var onScroll = function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + "%";
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------- 目录高亮 ---------- */
  var links = $$(".toc-rail a");
  if (links.length) {
    var secs = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); }).filter(Boolean);
    var spy = function () {
      var pos = window.scrollY + 150;
      var cur = secs[0];
      secs.forEach(function (s) {
        if (s.getBoundingClientRect().top + window.scrollY <= pos) cur = s;
      });
      links.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + cur.id); });
    };
    window.addEventListener("scroll", spy, { passive: true });
    spy();
  }

  /* ---------- 本章完成 ---------- */
  var done = load(KEY.done, {});
  var cbtn = $("#doneBtn");
  var chapter = document.body.dataset.chapter;
  if (cbtn && chapter) {
    var paintDone = function () {
      var on = !!done[chapter];
      cbtn.textContent = on ? "✓ 已完成" : "标记本章完成";
      cbtn.classList.toggle("on", on);
    };
    paintDone();
    cbtn.addEventListener("click", function () {
      done[chapter] = !done[chapter];
      save(KEY.done, done);
      paintDone();
    });
  }

  /* ---------- 任务清单 ---------- */
  var tasksEl = $("#taskList");
  if (tasksEl && chapter) {
    var all = load(KEY.tasks, {});
    var state = all[chapter] || {};
    var boxes = $$("input[type=checkbox]", tasksEl);
    var pbar = $("#taskBar");
    var ptext = $("#taskText");
    var paintTask = function () {
      var n = boxes.filter(function (b) { return b.checked; }).length;
      if (pbar) pbar.style.width = (boxes.length ? (n / boxes.length) * 100 : 0) + "%";
      if (ptext) ptext.textContent = n + " / " + boxes.length;
    };
    boxes.forEach(function (b) {
      b.checked = !!state[b.dataset.id];
      b.addEventListener("change", function () {
        state[b.dataset.id] = b.checked;
        all[chapter] = state;
        save(KEY.tasks, all);
        paintTask();
      });
    });
    paintTask();
  }

  /* ---------- 随手记 ---------- */
  var note = $("#quickNote");
  if (note && chapter) {
    var notes = load(KEY.notes, {});
    note.value = notes[chapter] || "";
    var t = null;
    note.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () {
        notes[chapter] = note.value;
        save(KEY.notes, notes);
      }, 400);
    });
  }

  /* ---------- 人物卡 ---------- */
  var mastery = load(KEY.mastery, {});
  var STAR = { 1: "★★★", 2: "★★", 3: "★" };

  function cardHTML(p) {
    var on = mastery[p.id] ? " on" : "";
    return '' +
      '<article class="pcard" data-id="' + p.id + '" data-star="' + p.star + '" data-tags="' + p.tags.join(",") + '">' +
        '<div class="pc-name">' + p.name + '<span class="pc-star">' + STAR[p.star] + '</span></div>' +
        '<div class="pc-role">' + p.role + '</div>' +
        '<p class="pc-one">' + p.one + '</p>' +
        '<div class="pc-meta"><span>首次出现 ' + p.first + '</span><span>关系：' + p.relation + '</span></div>' +
        (p.avoid ? '<div class="pc-avoid">⚠ ' + p.avoid + '</div>' : '') +
        '<div class="pc-master"><button class="mbtn' + on + '" data-master="' + p.id + '">' + (on ? "已掌握" : "标记掌握") + '</button></div>' +
      '</article>';
  }

  function bindMastery(scope) {
    $$("[data-master]", scope).forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.dataset.master;
        mastery[id] = !mastery[id];
        save(KEY.mastery, mastery);
        btn.classList.toggle("on", !!mastery[id]);
        btn.textContent = mastery[id] ? "已掌握" : "标记掌握";
      });
    });
  }

  function renderPeople(el, list) {
    el.innerHTML = list.map(cardHTML).join("");
    bindMastery(el);
  }

  /* 章节页：按 data-chapter 过滤 */
  var chPeople = $("#chapterPeople");
  if (chPeople && window.PEOPLE) {
    var cid = chPeople.dataset.chapter;
    var list = window.PEOPLE.filter(function (p) { return p.chapters.indexOf(cid) > -1; })
      .sort(function (a, b) { return a.star - b.star; });
    renderPeople(chPeople, list);
  }

  /* 人物总表页 */
  var allPeople = $("#allPeople");
  if (allPeople && window.PEOPLE) {
    var q = $("#pSearch"), fStar = $("#fStar"), fTag = $("#fTag");
    var counter = $("#pCount");
    var cur = window.PEOPLE.slice();

    var apply = function () {
      var kw = (q && q.value || "").trim().toLowerCase();
      var st = fStar && fStar.value;
      var tg = fTag && fTag.value;
      cur = window.PEOPLE.filter(function (p) {
        var hay = (p.name + " " + p.aka.join(" ") + " " + p.role + " " + p.tags.join(" ") + " " + p.relation + " " + p.one).toLowerCase();
        if (kw && hay.indexOf(kw) < 0) return false;
        if (st && String(p.star) !== st) return false;
        if (tg && p.tags.indexOf(tg) < 0) return false;
        return true;
      });
      renderPeople(allPeople, cur);
      if (counter) counter.textContent = cur.length;
      renderFlips(cur);
    };

    var flipBox = $("#flipCards");
    function renderFlips(list) {
      if (!flipBox) return;
      var pick = list.slice(0, 8);
      flipBox.innerHTML = pick.map(function (p) {
        return '<div class="flip" tabindex="0">' +
          '<div class="flip-inner">' +
            '<div class="flip-face flip-front"><div class="fq">这是谁？点击翻面</div><div class="fa">' + p.name + '</div></div>' +
            '<div class="flip-back"><div class="fq">' + p.role + '</div><div class="fa">' + p.one + '</div></div>' +
          '</div></div>';
      }).join("");
      $$(".flip", flipBox).forEach(function (f) {
        var go = function () { f.classList.toggle("on"); };
        f.addEventListener("click", go);
        f.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
      });
    }

    if (q) q.addEventListener("input", apply);
    if (fStar) fStar.addEventListener("change", apply);
    if (fTag) fTag.addEventListener("change", apply);
    apply();
  }

  /* ---------- 选择题 ---------- */
  $$(".quiz .q").forEach(function (q) {
    var btns = $$("button", q);
    var fb = $(".fb", q);
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        if (q.dataset.answered) return;
        var ok = b.dataset.ok === "1";
        b.classList.add(ok ? "right" : "wrong");
        if (ok) {
          q.dataset.answered = "1";
          btns.forEach(function (x) { x.disabled = true; });
          if (fb) fb.textContent = "✓ " + (q.dataset.fb || "答对了。");
        } else {
          if (fb) fb.textContent = "再想想——" + (b.dataset.why || "这个选项不符合本章经文。");
        }
      });
    });
  });

  /* ---------- 连线题 ---------- */
  $$(".match").forEach(function (m) {
    var left = $$('.col[data-side="left"] .item', m);
    var right = $$('.col[data-side="right"] .item', m);
    var sel = null, hit = 0, total = left.length;
    var msg = $(".match-msg", m.parentNode);

    left.forEach(function (it) {
      it.addEventListener("click", function () {
        if (it.classList.contains("ok")) return;
        left.forEach(function (x) { x.classList.remove("sel"); });
        it.classList.add("sel");
        sel = it;
      });
    });

    right.forEach(function (it) {
      it.addEventListener("click", function () {
        if (!sel || it.classList.contains("ok")) return;
        if (it.dataset.key === sel.dataset.key) {
          it.classList.add("ok"); sel.classList.add("ok"); sel.classList.remove("sel");
          sel = null; hit++;
          if (msg) msg.textContent = hit === total ? "全部连对 —— 本章人物关系过关。" : "已连对 " + hit + " / " + total + "，继续。";
        } else {
          it.classList.add("bad");
          setTimeout(function () { it.classList.remove("bad"); }, 320);
          if (msg) msg.textContent = "不对，再试一次。";
        }
      });
    });
  });

  /* ---------- 索引页进度 ---------- */
  $$("[data-chapter-progress]").forEach(function (el) {
    var id = el.dataset.chapterProgress;
    if (done[id]) {
      el.innerHTML = '<b>已完成</b> · 1 / 1';
      el.closest(".bookrow").classList.add("done");
    }
  });
})();

/* =========================================================
   模块朗读（Web Speech API · 默认晓晓，无则回退本机中文音色）
   ▶ 开始/暂停继续 · ■ 停止 · 逐句队列 · 当前段落高亮
   ========================================================= */
(function () {
  "use strict";
  if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) return;

  var synth = window.speechSynthesis;
  var voices = [];
  var chosen = null;
  var PREF;
  try { PREF = JSON.parse(localStorage.getItem("bible.speak")) || {}; } catch (e) { PREF = {}; }

  var CIRCLED = { "①":"一","②":"二","③":"三","④":"四","⑤":"五","⑥":"六","⑦":"七",
                  "⑧":"八","⑨":"九","⑩":"十","⑪":"十一","⑫":"十二","⑬":"十三",
                  "⑭":"十四","⑮":"十五","⑯":"十六","⑰":"十七","⑱":"十八","⑲":"十九","⑳":"二十" };

  function pick() {
    if (!voices.length) return;
    var i, v;
    chosen = null;
    if (PREF.voice) {
      for (i = 0; i < voices.length; i++) if (voices[i].name === PREF.voice) chosen = voices[i];
    }
    if (!chosen) {
      for (i = 0; i < voices.length; i++) {
        v = voices[i];
        if (/^zh/i.test(v.lang) && /xiaoxiao|晓晓/i.test(v.name)) { chosen = v; break; }
      }
    }
    if (!chosen) {
      for (i = 0; i < voices.length; i++) {
        v = voices[i];
        if (/^zh/i.test(v.lang) && !v.localService) { chosen = v; break; }
      }
    }
    if (!chosen) {
      for (i = 0; i < voices.length; i++) if (/^zh/i.test(voices[i].lang)) { chosen = voices[i]; break; }
    }
  }
  function refresh() { voices = synth.getVoices() || []; pick(); }
  synth.onvoiceschanged = refresh;
  refresh();

  /* 文本清洗：章:节转可读中文、圈号转序数、压缩空白 */
  function textify(t) {
    t = (t || "").replace(/\s+/g, " ").trim();
    if (!t) return "";
    t = t.replace(/(\d+)\s*[:：]\s*(\d+)\s*[–—\-~至]\s*(\d+)/g, "第$1章第$2节到第$3节");
    t = t.replace(/(\d+)\s*[:：]\s*(\d+(?:\s*[、,，]\s*\d+)*)/g, function (_, c, vs) {
      return "第" + c + "章" + vs.split(/\s*[、,，]\s*/).map(function (n) { return "第" + n + "节"; }).join("、");
    });
    t = t.replace(/[①-⑳]/g, function (m) { return CIRCLED[m] ? "第" + CIRCLED[m] + "，" : m; });
    return t;
  }

  /* 长句按标点切小块（部分引擎对超长 utterance 会截断） */
  function chunk(t) {
    var parts = t.match(/[^。！？；…]+[。！？；…]*/g) || [t];
    var out = [];
    parts.forEach(function (s) {
      s = s.trim();
      if (!s) return;
      while (s.length > 110) {
        var cut = s.lastIndexOf("，", 110);
        if (cut < 40) cut = s.lastIndexOf("、", 110);
        if (cut < 40) cut = s.lastIndexOf(" ", 110);
        if (cut < 40) cut = 110;
        out.push(s.slice(0, cut));
        s = s.slice(cut).replace(/^[，、\s]+/, "");
      }
      if (s) out.push(s);
    });
    return out.length ? out : [t];
  }

  var SEL = ".sec-head h2, h3, h4, p, li, blockquote, dt, dd, summary, tr";

  function visible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }

  function collect(sec) {
    var els = Array.prototype.slice.call(sec.querySelectorAll(SEL));
    var out = [];
    els.forEach(function (el) {
      if (el.closest(".sec-head") && el.tagName !== "H2") return;      /* sec-num / sub 不读 */
      if (el.tagName === "TR" && el.closest("thead")) return;          /* 表头不读 */
      if (el.tagName === "TR") {
        if (el.closest("table").classList.contains("tbl")) { out.push(el); }
        return;
      }
      if (!visible(el)) return;                                       /* 折叠的答案不读 */
      var anc = el.parentElement, nested = false;
      while (anc && anc !== sec) {
        if (anc.matches(SEL)) {
          /* 思维导图树逐层都要读，不做嵌套去重 */
          if (!(el.tagName === "LI" && el.closest(".mm"))) { nested = true; break; }
        }
        anc = anc.parentElement;
      }
      if (!nested) out.push(el);
    });
    return out;
  }

  /* ---------- 播放器 ---------- */
  var st = { sec: null, units: [], chunks: [], ui: -1, ci: -1, paused: false, token: 0, cur: null };

  function setBtn(sec, mode) {
    var ctl = sec._speakCtl;
    if (!ctl) return;
    ctl.btn.textContent = mode === "playing" ? "⏸" : "▶";
    ctl.btn.classList.toggle("on", mode !== "idle");
    ctl.btn.title = mode === "playing" ? "暂停朗读"
                  : mode === "paused" ? "继续朗读"
                  : "朗读本模块（" + (chosen && chosen.name.replace(/Microsoft |Online \(Natural\) - Chinese \(Mainland\)|Online \(Natural\)/g, "").trim() || "系统中文音色") + "）";
    ctl.stop.style.display = mode === "idle" ? "none" : "";
  }

  function highlight(el) {
    if (st.cur && st.cur !== el) st.cur.classList.remove("speaking-unit");
    st.cur = el;
    if (el) {
      el.classList.add("speaking-unit");
      var r = el.getBoundingClientRect();
      if (r.top < 80 || r.bottom > window.innerHeight - 100) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }

  function speakNext() {
    if (st.paused) return;
    var ui = st.ui, ci = st.ci, token = st.token;
    if (ui < 0 || ui >= st.units.length) return finish();
    var list = st.chunks[ui];
    ci += 1;
    if (ci >= list.length) {
      st.ui = ui + 1; st.ci = -1;
      return speakNext();
    }
    st.ci = ci;
    if (ci === 0) highlight(st.units[ui]);
    var u = new SpeechSynthesisUtterance(list[ci]);
    u.lang = "zh-CN";
    if (chosen) u.voice = chosen;
    u.rate = PREF.rate && PREF.rate > 0.5 && PREF.rate < 2 ? PREF.rate : 1;
    u.onend = function () { if (token === st.token) speakNext(); };
    u.onerror = function () { if (token === st.token) speakNext(); };
    st.utt = u;
    synth.speak(u);
  }

  function finish() {
    highlight(null);
    var sec = st.sec;
    st.sec = null; st.ui = -1; st.ci = -1; st.paused = false;
    if (sec) setBtn(sec, "idle");
  }

  function start(sec) {
    if (st.sec && st.sec !== sec) finish();
    var wasThis = st.sec === sec;
    var units = wasThis ? st.units : collect(sec);
    if (!units.length) return;
    st.token += 1;
    synth.cancel();
    st.sec = sec; st.units = units;
    st.chunks = units.map(function (el) { return chunk(textify(el.textContent)); });
    st.ui = wasThis && st.ui >= 0 ? st.ui : 0;
    st.ci = wasThis ? st.ci : -1;
    st.paused = false;
    setBtn(sec, "playing");
    speakNext();
  }

  function stopAll() {
    st.token += 1;
    synth.cancel();
    finish();
  }

  function toggle(sec) {
    if (st.sec === sec && !st.paused) {
      st.paused = true;
      synth.pause();
      setBtn(sec, "paused");
      return;
    }
    if (st.sec === sec && st.paused) {
      st.paused = false;
      setBtn(sec, "playing");
      synth.resume();
      /* 个别引擎 pause 后 resume 丢队列：补一次驱动 */
      setTimeout(function () {
        if (!st.paused && st.sec === sec && !synth.speaking && !synth.pending) speakNext();
      }, 250);
      return;
    }
    start(sec);
  }

  /* ---------- 声音选择面板 ---------- */
  function save() {
    try { PREF = PREF || {}; localStorage.setItem("bible.speak", JSON.stringify(PREF)); } catch (e) {}
  }

  function cleanName(v) {
    return (v.name || "").replace(/Microsoft |Google |Online \(Natural\) - Chinese \(Mainland\)|Online \(Natural\)/g, "").trim() || v.name;
  }

  var panel = null;
  function closePanel() { if (panel) { panel.style.display = "none"; stopAll(); } }

  function openPanel() {
    if (!panel) {
      panel = document.createElement("div");
      panel.className = "speak-panel";
      var box = document.createElement("div");
      box.className = "speak-panel-box";
      panel.appendChild(box);
      panel.addEventListener("click", function (e) { if (e.target === panel) closePanel(); });
      document.body.appendChild(panel);
    }
    var box = panel.firstChild;
    var list = voices.filter(function (v) { return /^zh/i.test(v.lang); });
    if (!list.length) list = voices.slice();
    var html = '<div class="speak-panel-head">选择朗读声音' +
      '<button type="button" class="speak-btn gear" title="关闭">✕</button></div>' +
      '<div class="speak-panel-tip">当前设备可用 ' + list.length + ' 个中文声音。选中的声音会记住在这台设备上。</div>' +
      '<div class="speak-panel-list">';
    list.forEach(function (v) {
      var sel = chosen && v.name === chosen.name;
      html += '<div class="speak-row' + (sel ? " sel" : "") + '" data-v="' + v.name.replace(/"/g, "&quot;") + '">' +
        '<span class="speak-vname">' + cleanName(v) + '</span>' +
        '<span class="speak-vtag">' + (v.localService ? "本地" : "在线") + '</span>' +
        '<button type="button" class="speak-mini" data-act="try">试听</button>' +
        '<button type="button" class="speak-mini" data-act="use">' + (sel ? "已选中" : "使用") + '</button>' +
        '</div>';
    });
    html += '</div><div class="speak-panel-rate">语速 <input type="range" min="0.6" max="1.6" step="0.05" value="' +
      (PREF.rate || 1) + '"> <span>' + (PREF.rate || 1) + '×</span></div>' +
      '<div class="speak-panel-foot"><button type="button" class="speak-mini" data-act="reset">恢复默认（晓晓优先）</button></div>';
    box.innerHTML = html;
    box.querySelector(".speak-panel-head .gear").addEventListener("click", closePanel);
    box.querySelector(".speak-panel-rate input").addEventListener("input", function () {
      PREF.rate = parseFloat(this.value);
      this.nextElementSibling.textContent = this.value + "×";
      save();
    });
    Array.prototype.forEach.call(box.querySelectorAll(".speak-row"), function (row) {
      var vName = row.getAttribute("data-v");
      var v = null;
      list.forEach(function (x) { if (x.name === vName) v = x; });
      if (!v) return;
      var t = row.querySelector('[data-act="try"]');
      t.addEventListener("click", function () {
        synth.cancel();
        var u = new SpeechSynthesisUtterance("耶和华是我的牧者，我必不至缺乏。");
        u.lang = "zh-CN"; u.voice = v; u.rate = PREF.rate || 1;
        synth.speak(u);
      });
      var u2 = row.querySelector('[data-act="use"]');
      u2.addEventListener("click", function () {
        PREF.voice = v.name; save(); pick();
        Array.prototype.forEach.call(box.querySelectorAll(".speak-row"), function (r) { r.classList.remove("sel"); r.querySelector('[data-act="use"]').textContent = "使用"; });
        row.classList.add("sel"); u2.textContent = "已选中";
      });
    });
    var rst = box.querySelector('[data-act="reset"]');
    rst.addEventListener("click", function () {
      delete PREF.voice; delete PREF.rate; save(); pick();
      closePanel(); openPanel();
    });
    panel.style.display = "flex";
  }

  /* ---------- 注入按钮 ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("main section[id]"), function (sec) {
    var head = sec.querySelector(".sec-head");
    if (!head || sec._speakCtl) return;
    var ctl = document.createElement("span");
    ctl.className = "speak-ctl";
    var btn = document.createElement("button");
    btn.type = "button"; btn.className = "speak-btn"; btn.textContent = "▶";
    var stop = document.createElement("button");
    stop.type = "button"; stop.className = "speak-btn stop"; stop.textContent = "■";
    stop.title = "停止朗读"; stop.style.display = "none";
    var gear = document.createElement("button");
    gear.type = "button"; gear.className = "speak-btn gear"; gear.textContent = "⚙";
    gear.title = "选择朗读声音 / 语速";
    ctl.appendChild(btn); ctl.appendChild(stop); ctl.appendChild(gear);
    head.appendChild(ctl);
    sec._speakCtl = { btn: btn, stop: stop, gear: gear };
    btn.addEventListener("click", function () { toggle(sec); });
    stop.addEventListener("click", function () { if (st.sec === sec) stopAll(); });
    gear.addEventListener("click", openPanel);
  });
})();

/* =========================================================
   总目录关键词搜索（只在 index.html 激活）
   支持：书卷简称/全名/英文 + 章号/范围；纯关键词搜章节摘要
   ========================================================= */
(function () {
  "use strict";
  var input = document.getElementById("catSearch");
  if (!input) return;
  var countEl = document.getElementById("catCount");
  var noEl = document.getElementById("catNoResult");
  var root = document.getElementById("books");
  if (!root) return;

  var ABBR = {
    gen:["创","创世","创世记"], exo:["出","出埃及","出埃及记"], lev:["利","利未","利未记"],
    num:["民","民数","民数记"], deu:["申","申命","申命记"], jos:["书","约书亚","约书亚记"],
    jdg:["士","士师","士师记"], rut:["得","路得","路得记"],
    "1sa":["撒上","撒母耳上"], "2sa":["撒下","撒母耳下"],
    "1ki":["王上","列王纪上"], "2ki":["王下","列王纪下"],
    "1ch":["代上","历代志上"], "2ch":["代下","历代志下"],
    ezr:["拉","以斯拉","以斯拉记"], neh:["尼","尼希米","尼希米记"], est:["斯","以斯帖","以斯帖记"],
    job:["伯","约伯","约伯记"], psa:["诗","诗篇"], pro:["箴","箴言"],
    ecc:["传","传道","传道书"], sng:["歌","雅歌"],
    isa:["赛","以赛亚","以赛亚书"], jer:["耶","耶利米","耶利米书"], lam:["哀","耶利米哀歌"],
    ezk:["结","以西结","以西结书"], dan:["但","但以理","但以理书"], hos:["何","何西阿","何西阿书"],
    jol:["珥","约珥","约珥书"], amo:["摩","阿摩司","阿摩司书"], oba:["俄","俄巴底亚","俄巴底亚书"],
    jon:["拿","约拿","约拿书"], mic:["弥","弥迦","弥迦书"], nam:["鸿","那鸿","那鸿书"],
    hab:["哈","哈巴谷","哈巴谷书"], zep:["番","西番雅","西番雅书"], hag:["该","哈该","哈该书"],
    zec:["亚","撒迦利亚","撒迦利亚书"], mal:["玛","玛拉基","玛拉基书"],
    mat:["太","马太","马太福音"], mark:["可","马可","马可福音"], luk:["路","路加","路加福音"],
    jhn:["约","约翰","约翰福音"], act:["徒","使徒行传"], rom:["罗","罗马","罗马书"],
    "1co":["林前","哥林多前","哥林多前书"], "2co":["林后","哥林多后","哥林多后书"],
    gal:["加","加拉太","加拉太书"], eph:["弗","以弗所","以弗所书"], php:["腓","腓立比","腓立比书"],
    col:["西","歌罗西","歌罗西书"], "1th":["帖前","帖撒罗尼迦前"], "2th":["帖后","帖撒罗尼迦后"],
    "1ti":["提前","提摩太前"], "2ti":["提后","提摩太后"], tit:["多","提多","提多书"],
    phm:["门","腓利门","腓利门书"], heb:["来","希伯来","希伯来书"], jas:["雅","雅各","雅各书"],
    "1pe":["彼前","彼得前"], "2pe":["彼后","彼得后"],
    "1jn":["约一","约翰一"], "2jn":["约二","约翰二"], "3jn":["约三","约翰三"],
    jud:["犹","犹大","犹大书"], rev:["启","启示","启示录"]
  };

  var items = [], chipEls = [], groups = [], blocks = [];
  var countHtml = countEl ? countEl.innerHTML : "";

  Array.prototype.forEach.call(root.querySelectorAll("details.bookgroup"), function (g) {
    groups.push({ el: g, open: !!g.open });
    var cnEl = g.querySelector(".bg-name"), enEl = g.querySelector(".bg-en");
    var cn = cnEl ? cnEl.textContent.trim() : "";
    var en = enEl ? enEl.textContent.trim() : "";
    Array.prototype.forEach.call(g.querySelectorAll(".chips a.chip"), function (a) {
      chipEls.push(a);
      if (a.classList.contains("bookpage") || a.classList.contains("overview")) return;
      var m = (a.getAttribute("href") || "").match(/([a-z0-9]+)-\d+\.html$/i);
      if (!m) return;
      var bid = m[1].toLowerCase();
      var aliases = (ABBR[bid] || []).slice();
      aliases.push(bid);              /* 英文 id 也可作简称：gen / rom / psa */
      if (cn) aliases.push(cn);
      if (en) aliases.push(en);
      var num = parseInt(a.textContent.trim(), 10);
      items.push({
        el: a, bid: bid, num: isNaN(num) ? 0 : num,
        title: a.getAttribute("title") || "", cn: cn, en: en, aliases: aliases
      });
    });
  });
  Array.prototype.forEach.call(root.querySelectorAll(".bookgroup.empty, .genregroup, .testament"), function (b) {
    blocks.push({ el: b, display: b.style.display });
  });

  function bookIdsFor(bp) {
    var out = [], seen = {};
    items.forEach(function (it) {
      if (seen[it.bid]) return;
      seen[it.bid] = 1;
      for (var i = 0; i < it.aliases.length; i++) {
        if (it.aliases[i].toLowerCase() === bp) { out.push(it.bid); return; }
      }
    });
    return out;
  }

  function parse(q) {
    var raw = q.trim();
    var m = raw.match(/^(.+?)[\s:：]*(\d+)\s*(?:[-–—~至]\s*(\d+))?\s*章?$/);
    if (m) {
      var bp = m[1].trim().toLowerCase();
      var ids = bp ? bookIdsFor(bp) : [];
      if (ids.length) {
        var a = parseInt(m[2], 10), b = m[3] ? parseInt(m[3], 10) : a;
        if (a > b) { var t = a; a = b; b = t; }
        return { ids: ids, a: a, b: b, text: raw };
      }
    }
    return { ids: [], text: raw };
  }

  function match(it, p) {
    if (p.ids.length) {
      if (p.ids.indexOf(it.bid) < 0) return false;
      return it.num >= p.a && it.num <= p.b;
    }
    var q = p.text.toLowerCase();
    if (!q) return true;
    if (it.title.toLowerCase().indexOf(q) >= 0) return true;
    if (it.cn.toLowerCase().indexOf(q) >= 0) return true;
    if (it.en.toLowerCase().indexOf(q) >= 0) return true;
    if (String(it.num) === q) return true;
    for (var i = 0; i < it.aliases.length; i++) {
      if (it.aliases[i].toLowerCase().indexOf(q) >= 0) return true;
    }
    return false;
  }

  function restore() {
    chipEls.forEach(function (a) {
      a.style.display = ""; a.classList.remove("hit");
      var orig = a.getAttribute("data-href");
      if (orig) a.setAttribute("href", orig);
    });
    groups.forEach(function (g) { g.el.style.display = ""; g.el.open = g.open; });
    blocks.forEach(function (b) { b.el.style.display = b.display; });
    if (countEl) countEl.innerHTML = countHtml;
    if (noEl) noEl.hidden = true;
  }

  function apply() {
    var q = input.value;
    if (!q.trim()) { restore(); return; }
    var p = parse(q);
    var hit = {};
    var n = 0;
    items.forEach(function (it) {
      if (match(it, p)) { hit[it.el] = true; n += 1; }
    });
    chipEls.forEach(function (a) {
      var ok = !!hit[a];
      a.style.display = ok ? "" : "none";
      a.classList.toggle("hit", ok);
      /* 关键词命中时给链接带上定位参数；章号查询与未命中保持原链接 */
      var orig = a.getAttribute("data-href") || a.getAttribute("href") || "";
      a.setAttribute("data-href", orig);
      if (ok && !p.ids.length && p.text) {
        a.setAttribute("href", orig + (orig.indexOf("?") >= 0 ? "&" : "?") +
          "q=" + encodeURIComponent(p.text));
      } else {
        a.setAttribute("href", orig);
      }
    });
    /* 每次搜索先把书卷收起，只展开本次命中的，避免上次展开的残留 */
    groups.forEach(function (g) { g.el.open = false; });
    groups.forEach(function (g) {
      var any = false;
      Array.prototype.forEach.call(g.el.querySelectorAll(".chips a.chip"), function (a) {
        if (hit[a]) any = true;
      });
      g.el.style.display = any ? "" : "none";
      if (any) g.el.open = true;
    });
    Array.prototype.forEach.call(root.querySelectorAll(".genregroup, .testament"), function (b) {
      var any = false;
      Array.prototype.forEach.call(b.querySelectorAll("details.bookgroup"), function (g) {
        if (g.style.display !== "none") any = true;
      });
      b.style.display = any ? "" : "none";
    });
    if (countEl) countEl.innerHTML = '找到 <b>' + n + '</b> 章 · 「' +
      q.trim().replace(/[&<>"]/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
      }) + '」';
    if (noEl) noEl.hidden = n > 0;
  }

  input.addEventListener("input", apply);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { input.value = ""; apply(); input.blur(); }
  });
})();

/* =========================================================
   从总目录搜索跳转来时（?q=关键词）：在正文中定位并高亮该词
   全站生效，仅当 URL 带 q 参数时运行
   ========================================================= */
(function () {
  "use strict";
  var m = location.search.match(/[?&]q=([^&]*)/);
  if (!m) return;
  var q = "";
  try { q = decodeURIComponent(m[1]).trim(); } catch (e) { q = m[1].trim(); }
  if (!q) return;

  var main = document.querySelector("main");
  if (!main) return;

  /* 候选正文元素：标题、段落、列表、表格行、引言；跳过读出答案的 details 内容由浏览器自然处理 */
  var SEL = "h2, h3, h4, p, li, blockquote, dt, dd, summary, tr";
  var nodes = Array.prototype.slice.call(main.querySelectorAll(SEL));
  var lower = q.toLowerCase();
  /* 搜索摘要取自章首 thesis（在 main 之外的题头区），无 thesis 时取分段标题 */
  var thesis = document.querySelector("p.thesis");
  var target = null, targetText = "";
  var thesisHit = !!(thesis && (thesis.textContent || "").toLowerCase().indexOf(lower) >= 0);
  if (thesisHit) {
    target = thesis;
    targetText = thesis.textContent;
  }
  function pick(el) {
    if (thesisHit) return false;   /* thesis 已命中即锁定，摘要就是这段 */
    var t = (el.textContent || "").replace(/\s+/g, " ").trim();
    if (t.toLowerCase().indexOf(lower) < 0) return false;
    if (!target || t.length < targetText.length) { target = el; targetText = t; }
    return true;
  }
  nodes.forEach(pick);

  if (!target) return;

  /* 高亮：把关键词用 <mark> 包起来（只包文本节点，不破坏结构） */
  function markText(el, word) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
    var node, done = 0;
    var low = word.toLowerCase();
    while (node = walker.nextNode()) {
      var txt = node.nodeValue, idx = txt.toLowerCase().indexOf(low);
      if (idx < 0) continue;
      var span = document.createElement("span");
      span.className = "search-hit";
      span.textContent = txt.slice(idx, idx + word.length);
      var rest = document.createTextNode(txt.slice(idx + word.length));
      var before = document.createTextNode(txt.slice(0, idx));
      node.parentNode.replaceChild(rest, node);
      rest.parentNode.insertBefore(span, rest);
      span.parentNode.insertBefore(before, span);
      done++;
      if (done >= 3) break;   /* 每段最多标 3 处，避免满屏高亮 */
    }
  }
  markText(target, q);
  target.classList.add("search-target");

  /* 顶部提示条，说明定位结果并可关闭 */
  var bar = document.createElement("div");
  bar.className = "search-jumpbar no-print";
  bar.innerHTML = '<span>已定位到「' + q.replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
  }) + '」</span><button type="button" title="关闭">✕</button>';
  bar.querySelector("button").addEventListener("click", function () {
    bar.remove();
    target.classList.remove("search-target");
    Array.prototype.forEach.call(main.querySelectorAll(".search-hit"), function (s) {
      s.replaceWith(document.createTextNode(s.textContent));
    });
  });
  document.body.appendChild(bar);

  setTimeout(function () {
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 120);
})();
