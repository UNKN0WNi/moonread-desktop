/* global pywebview */
var book = null;
var idx = 0;
var read = document.getElementById('read');
var page = document.getElementById('page');

function esc(s) {
  var d = document.createElement('div');
  d.textContent = s == null ? '' : String(s);
  return d.innerHTML;
}

function showEmpty() {
  page.innerHTML =
    '<div class="empty"><div class="logo">月</div><h1>MoonRead</h1>' +
    '<p>轻量的 Windows EPUB 阅读器</p>' +
    '<button class="btn primary big" id="emptyOpen">选择一本 EPUB</button>' +
    '<p class="hint">也可以把 .epub 文件直接拖进这个窗口</p></div>';
  document.getElementById('emptyOpen').onclick = openFile;
  document.getElementById('bookTitle').textContent = 'MoonRead';
  document.getElementById('bookAuthor').textContent = '把 EPUB 拖进窗口，或点左上角打开';
  document.getElementById('tocList').innerHTML = '';
  document.getElementById('pos').textContent = '';
}

function applyBook(data) {
  book = data;
  idx = data.saved_index || 0;
  if (idx >= data.chapters.length) idx = 0;
  document.getElementById('bookTitle').textContent = data.title;
  document.getElementById('bookAuthor').textContent =
    (data.author ? data.author + ' · ' : '') +
    data.chapters.length + ' 章 · 约 ' + data.chars.toLocaleString() + ' 字';
  buildToc();
  render();
  if (data.chapters.length) {
    document.getElementById('bookAuthor').title = data.path || '';
  }
}

function render() {
  if (!book) return;
  var c = book.chapters[idx];
  var html = '<h2>' + esc(c.title) + '</h2>';
  for (var i = 0; i < c.paras.length; i++) {
    html += '<p' + (i === 0 ? ' class="first"':'') + '>' + esc(c.paras[i]) + '</p>';
  }
  page.innerHTML = html;
  read.scrollTop = 0;
  document.getElementById('pos').textContent = (idx + 1) + ' / ' + book.chapters.length + ' 章';
  document.getElementById('prev').disabled = idx <= 0;
  document.getElementById('next').disabled = idx >= book.chapters.length - 1;
  var nodes = document.querySelectorAll('.toc-item');
  for (var j = 0; j < nodes.length; j++) {
    nodes[j].classList.toggle('active', Number(nodes[j].dataset.idx) === idx);
  }
  if (window.pywebview && pywebview.api.save_progress) {
    pywebview.api.save_progress(book.key, idx);
  }
}

function goto(i) {
  if (book && i >= 0 && i < book.chapters.length) { idx = i; render(); }
}

function buildToc() {
  var box = document.getElementById('tocList');
  box.innerHTML = '';
  for (var i = 0; i < book.toc.length; i++) {
    var t = book.toc[i];
    if (t.idx == null) continue;
    var b = document.createElement('button');
    b.className = 'toc-item' + (t.level > 0 ? ' lv' + Math.min(t.level, 2) : '');
    b.textContent = t.title || ('第 ' + (t.idx + 1) + ' 章');
    b.dataset.idx = t.idx;
    b.onclick = (function (k) { return function () { goto(k); }; })(t.idx);
    box.appendChild(b);
  }
}

async function openFile() {
  if (!window.pywebview) { alert('请在桌面应用中打开'); return; }
  var path = await pywebview.api.open_file();
  if (!path) return;
  await loadPath(path);
}

async function loadPath(path) {
  document.getElementById('bookAuthor').textContent = '正在打开…';
  var data = await pywebview.api.load_epub(path);
  if (data.error) {
    alert('打开失败：' + data.error);
    showEmpty();
    return;
  }
  applyBook(data);
}

document.getElementById('openBtn').onclick = openFile;
document.getElementById('prev').onclick = function () { goto(idx - 1); };
document.getElementById('next').onclick = function () { goto(idx + 1); };
document.getElementById('tocBtn').onclick = function () {
  document.getElementById('side').classList.toggle('hide');
};
function savePrefs() {
  if (!window.pywebview || !pywebview.api.set_prefs) return;
  pywebview.api.set_prefs({
    night: document.body.classList.contains('night'),
    font_size: parseFloat(getComputedStyle(page).fontSize)
  });
}
document.getElementById('smaller').onclick = function () {
  var s = parseFloat(getComputedStyle(page).fontSize); if (s > 14) page.style.fontSize = (s - 2) + 'px'; savePrefs();
};
document.getElementById('bigger').onclick = function () {
  var s = parseFloat(getComputedStyle(page).fontSize); if (s < 30) page.style.fontSize = (s + 2) + 'px'; savePrefs();
};
document.getElementById('night').onclick = function () { document.body.classList.toggle('night'); savePrefs(); };
document.addEventListener('keydown', function (e) {
  if (e.key === 'ArrowLeft') goto(idx - 1);
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); goto(idx + 1); }
});

/* 拖拽：从桌面拖 .epub 进窗口 */
var mask = document.getElementById('dropmask');
var dragDepth = 0;
window.addEventListener('dragenter', function (e) { e.preventDefault(); dragDepth++; mask.classList.add('show'); });
window.addEventListener('dragover', function (e) { e.preventDefault(); });
window.addEventListener('dragleave', function (e) { e.preventDefault(); dragDepth--; if (dragDepth <= 0) { dragDepth = 0; mask.classList.remove('show'); } });
window.addEventListener('drop', async function (e) {
  e.preventDefault(); dragDepth = 0; mask.classList.remove('show');
  if (!e.dataTransfer.files.length) return;
  var f = e.dataTransfer.files[0];
  if (!/\.epub$/i.test(f.name)) { alert('只支持 .epub 文件'); return; }
  var buf = await f.arrayBuffer();
  var bytes = new Uint8Array(buf);
  var binary = '';
  for (var i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  document.getElementById('bookAuthor').textContent = '正在打开…';
  var data = await pywebview.api.load_epub_bytes(btoa(binary), f.name);
  if (data.error) { alert('打开失败：' + data.error); showEmpty(); return; }
  applyBook(data);
});

/* pywebview 就绪后，接收 Python 侧传入的启动文件 */
window.addEventListener('pywebviewready', async function () {
  var prefs = await pywebview.api.get_prefs();
  if (prefs && prefs.night) document.body.classList.add('night');
  if (prefs && prefs.font_size) page.style.fontSize = prefs.font_size + 'px';
  var startup = await pywebview.api.get_startup_path();
  if (startup) await loadPath(startup);
  else showEmpty();
});
