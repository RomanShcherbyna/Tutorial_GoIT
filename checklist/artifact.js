// Static build: ticks live in this browser only, so state goes to localStorage
// under one key. The server build keeps the same shapes, so behaviour matches.
(function () {
  var C = DATA.checklist, T = DATA.translations, DOCS = DATA.documents;
  var STATUS = { todo: 'не начато', doing: 'в работе', done: 'готово', skip: 'не нужно' };
  var KEY = 'lpb-checklist-state';
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { state = {}; }
  var filter = { key: 'all', val: null }, query = '';

  function esc(s) {
    return (s == null ? '' : String(s)).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function st(id) { return state[id] || 'todo'; }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { }
  }
  function sel(id) {
    return '<select class="st" data-id="' + esc(id) + '" aria-label="Статус">' +
      Object.keys(STATUS).map(function (s) {
        return '<option value="' + s + '"' + (s === st(id) ? ' selected' : '') +
          '>' + STATUS[s] + '</option>';
      }).join('') + '</select>';
  }

  function lanes(f, idPrefix) {
    var L = [['pl', 'Polski'], ['ua', 'Українська'], ['en', 'English']]
      .filter(function (p) { return f[p[0]]; });
    if (!L.length) return '';
    return '<div class="lanes' + (L.length === 1 ? ' one' : '') + '">' +
      L.map(function (p) {
        var cid = idPrefix + '-' + p[0];
        return '<div class="lane"><h4>' + p[1] +
          '<button class="copy" type="button" data-copy="' + cid + '">копировать</button>' +
          '</h4><pre id="c-' + cid + '">' + esc(f[p[0]]) + '</pre></div>';
      }).join('') + '</div>';
  }

  function fixHtml(f, num) {
    var steps = (f.steps && f.steps.length)
      ? '<ol class="steps">' + f.steps.map(function (x) {
        return '<li>' + esc(x) + '</li>';
      }).join('') + '</ol>' : '';
    return '<article class="fix s-' + f.severity + ' is-' + st(f.id) +
      '" data-id="' + esc(f.id) + '" data-sev="' + f.severity + '">' +
      '<div class="fixhead"><span class="num">' + num + '.</span>' +
      '<span class="mark">' + esc(f.severity_label) + '</span>' +
      '<span class="fid">' + esc(f.id) + '</span>' + sel(f.id) + '</div>' +
      '<p class="action">' + esc(f.action || f.title) + '</p>' +
      '<p class="where"><b>Где править</b> &nbsp;' + esc(f.where) + '</p>' +
      (f.current ? '<div class="evidence">' + esc(f.current) + '</div>' : '') +
      (f.why ? '<p class="why">' + esc(f.why) + '</p>' : '') + steps +
      (f.done_when ? '<p class="why"><b>Готово, когда:</b> ' + esc(f.done_when) + '</p>' : '') +
      lanes(f, f.id) +
      (f.note ? '<p class="note">' + esc(f.note) + '</p>' : '') + '</article>';
  }

  function groupHtml(g) {
    var links = Object.keys(g.urls || {}).map(function (k) {
      return '<a href="' + esc(g.urls[k]) + '" target="_blank" rel="noopener">' +
        k.toUpperCase() + '</a>';
    }).join('');
    var badges = '';
    if (g.blockers) badges += '<span class="badge b-blocker">' + g.blockers + ' блокеров</span>';
    if (g.from_documents) badges += '<span class="badge b-doc">' + g.from_documents + ' из документов</span>';
    return '<section class="grp is-' + st(g.key) + '" data-key="' + esc(g.key) + '">' +
      '<header class="grphead"><button class="toggle" type="button" aria-expanded="false">' +
      '<span class="tw-arrow">▸</span><span class="gtitle">' + esc(g.title) + '</span>' +
      (g.url_label ? '<code class="gurl">' + esc(g.url_label) + '</code>' : '') +
      '<span class="gcount">' + g.count + ' правок</span>' + badges + '</button>' +
      '<div class="ghead-right">' + (links ? '<span class="links">' + links + '</span>' : '') +
      sel(g.key) + '</div></header>' +
      (g.desc ? '<p class="gdesc">' + esc(g.desc) + '</p>' : '') +
      '<div class="fixes" hidden>' +
      (g.documents && g.documents.length
        ? '<p class="gdocs"><b>Документы:</b> ' +
          g.documents.map(esc).join(' · ') + '</p>' : '') +
      '<p class="gsub">Тут исправить:</p>' +
      g.fixes.map(function (f, i) { return fixHtml(f, i + 1); }).join('') +
      '</div></section>';
  }

  function chips() {
    var h = '<button class="chip" data-k="all" aria-pressed="true">Все страницы <i>' +
      C.total_pages + '</i></button>';
    C.severities.forEach(function (s) {
      if (s.count) h += '<button class="chip" data-k="sev" data-v="' + s.key +
        '" aria-pressed="false">' + s.label + ' <i>' + s.count + '</i></button>';
    });
    ['todo', 'doing', 'done'].forEach(function (s) {
      h += '<button class="chip" data-k="status" data-v="' + s +
        '" aria-pressed="false">' + STATUS[s] + ' <i class="cnt-' + s + '"></i></button>';
    });
    document.getElementById('chips').innerHTML = h;
  }

  function openGroup(g, open) {
    g.querySelector('.fixes').hidden = !open;
    var b = g.querySelector('.toggle');
    b.setAttribute('aria-expanded', String(open));
    b.querySelector('.tw-arrow').textContent = open ? '▾' : '▸';
  }

  function applyFilter() {
    var q = query.trim().toLowerCase(), shown = 0;
    [].forEach.call(document.querySelectorAll('.grp'), function (g) {
      var anyFix = false;
      [].forEach.call(g.querySelectorAll('.fix'), function (el) {
        var okF = filter.key !== 'sev' || el.dataset.sev === filter.val;
        var okQ = !q || el.textContent.toLowerCase().indexOf(q) !== -1;
        el.hidden = !(okF && okQ);
        if (okF && okQ) anyFix = true;
      });
      var okG = filter.key !== 'status' || st(g.dataset.key) === filter.val;
      var okQg = !q || g.textContent.toLowerCase().indexOf(q) !== -1;
      var show = okG && okQg && (filter.key === 'sev' ? anyFix : true);
      g.hidden = !show;
      if (show) shown++;
      if (show && q && anyFix) openGroup(g, true);
    });
    progress(shown);
  }

  function progress(shown) {
    var c = { todo: 0, doing: 0, done: 0, skip: 0 };
    C.groups.forEach(function (g) { c[st(g.key)]++; });
    var closed = c.done + c.skip;
    var pct = C.total_pages ? Math.round(closed / C.total_pages * 100) : 0;
    document.getElementById('barfill').style.width = pct + '%';
    document.getElementById('pstat').innerHTML =
      '<span><b>' + closed + '</b> из <b>' + C.total_pages + '</b> страниц закрыто (' + pct + '%)</span>' +
      '<span>в работе: <b>' + c.doing + '</b></span>' +
      '<span>не начато: <b>' + c.todo + '</b></span>' +
      '<span>правок внутри: <b>' + C.total_fixes + '</b></span>' +
      (shown !== undefined && shown !== C.total_pages ? '<span>показано: <b>' + shown + '</b></span>' : '');
    ['todo', 'doing', 'done'].forEach(function (s) {
      var el = document.querySelector('.cnt-' + s);
      if (el) el.textContent = c[s];
    });
  }

  function renderDocs() {
    document.getElementById('doclist').innerHTML = DOCS.map(function (d) {
      var kb = Math.max(1, Math.round(d.size / 1024)) + ' КБ';
      return '<a href="' + d.href + '" download="' + esc(d.name) + '"><span>' +
        esc(d.name) + '</span><span class="sz">' + kb + ' · скачать</span></a>';
    }).join('');

    document.getElementById('doctexts').innerHTML = T.documents.map(function (doc) {
      var blocks = doc.blocks.map(function (b) {
        return '<div class="blk"><span class="n">' + b.n + '</span>' +
          lanes(b, doc.doc + '-' + b.n) + '</div>';
      }).join('');
      var notes = (doc.notes && doc.notes.length)
        ? '<div class="fixes"><article class="fix s-high"><p class="ftitle">' +
        'Замечания к документу (' + doc.notes.length + ')</p><ol class="steps">' +
        doc.notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') +
        '</ol></article></div>' : '';
      return '<section class="doc grp"><header class="grphead">' +
        '<button class="toggle" type="button" aria-expanded="false">' +
        '<span class="tw-arrow">▸</span><span class="gtitle">' + esc(doc.title) + '</span>' +
        '<span class="gcount">' + doc.blocks.length + ' блоков</span>' +
        (doc.target_path ? '<span class="badge b-doc">' + esc(doc.target_path) + '</span>' : '') +
        (doc.notes && doc.notes.length ? '<span class="badge b-blocker">' +
          doc.notes.length + ' замечаний</span>' : '') +
        '</button></header>' +
        '<div class="fixes docblocks" hidden>' + notes + blocks + '</div></section>';
    }).join('');
  }

  // ---- events -------------------------------------------------------------
  document.addEventListener('click', function (e) {
    var t = e.target.closest('.toggle');
    if (t) {
      var g = t.closest('.grp');
      openGroup(g, g.querySelector('.fixes').hidden);
      return;
    }
    var cp = e.target.closest('.copy');
    if (cp) {
      var pre = document.getElementById('c-' + cp.dataset.copy);
      if (pre) navigator.clipboard.writeText(pre.textContent).then(function () {
        cp.textContent = 'скопировано';
        setTimeout(function () { cp.textContent = 'копировать'; }, 1200);
      });
      return;
    }
    var chip = e.target.closest('#chips button');
    if (chip) {
      [].forEach.call(document.querySelectorAll('#chips button'), function (x) {
        x.setAttribute('aria-pressed', String(x === chip));
      });
      filter = { key: chip.dataset.k, val: chip.dataset.v || null };
      applyFilter();
      return;
    }
    var tab = e.target.closest('.tabs button');
    if (tab) {
      [].forEach.call(document.querySelectorAll('.tabs button'), function (x) {
        x.setAttribute('aria-selected', String(x === tab));
      });
      document.getElementById('p-tasks').classList.toggle('on', tab.dataset.tab === 'tasks');
      document.getElementById('p-docs').classList.toggle('on', tab.dataset.tab === 'docs');
    }
  });

  document.addEventListener('change', function (e) {
    if (!e.target.classList.contains('st')) return;
    state[e.target.dataset.id] = e.target.value;
    save();
    var el = document.querySelector('[data-key="' + CSS.escape(e.target.dataset.id) + '"]')
      || document.querySelector('.fix[data-id="' + CSS.escape(e.target.dataset.id) + '"]');
    if (el) el.className = el.className.replace(/is-\w+/, 'is-' + e.target.value);
    applyFilter();
  });

  document.getElementById('q').addEventListener('input', function (e) {
    query = e.target.value;
    applyFilter();
  });
  document.getElementById('theme').addEventListener('click', function () {
    var r = document.documentElement;
    var dark = r.getAttribute('data-theme') === 'dark' ||
      (!r.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    var next = dark ? 'light' : 'dark';
    r.setAttribute('data-theme', next);
    try { localStorage.setItem('lpb-theme', next); } catch (e) { }
  });
  addEventListener('scroll', function () {
    document.getElementById('totop').classList.toggle('on', scrollY > 800);
  }, { passive: true });
  document.getElementById('totop').addEventListener('click', function () {
    scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  });

  try {
    var th = localStorage.getItem('lpb-theme');
    if (th) document.documentElement.setAttribute('data-theme', th);
  } catch (e) { }

  // ---- go -----------------------------------------------------------------
  document.getElementById('list').innerHTML = C.groups.map(groupHtml).join('');
  chips();
  renderDocs();
  if (C.excluded && C.excluded.fixes) {
    var ex = document.getElementById('excluded');
    ex.textContent = 'Не входит в этот список: ' +
      C.excluded.pages.map(function (p) { return p.title + ' (' + p.count + ')'; }).join(', ') +
      ' — ' + C.excluded.reason;
    ex.hidden = false;
  }
  applyFilter();
})();
