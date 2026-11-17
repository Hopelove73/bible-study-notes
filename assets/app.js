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
    ctl.appendChild(btn); ctl.appendChild(stop);
    head.appendChild(ctl);
    sec._speakCtl = { btn: btn, stop: stop };
    btn.addEventListener("click", function () { toggle(sec); });
    stop.addEventListener("click", function () { if (st.sec === sec) stopAll(); });
  });
})();
