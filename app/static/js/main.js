/* VU LMS — Main JavaScript */

// ── Sidebar toggle ─────────────────────────────────────────
var sidebarCollapsed = false;
function toggleSidebar() {
  var sidebar = document.getElementById('sidebar');
  var main = document.getElementById('mainContent');
  if (!sidebar) return;
  sidebarCollapsed = !sidebarCollapsed;
  if (sidebarCollapsed) {
    sidebar.classList.add('collapsed');
    if (main) main.classList.add('sidebar-collapsed');
  } else {
    sidebar.classList.remove('collapsed');
    if (main) main.classList.remove('sidebar-collapsed');
  }
}

// ── User dropdown ──────────────────────────────────────────
function toggleDropdown() {
  var menu = document.getElementById('dropdownMenu');
  if (menu) menu.classList.toggle('open');
}
document.addEventListener('click', function(e) {
  var dd = document.getElementById('userDropdown');
  var menu = document.getElementById('dropdownMenu');
  if (dd && menu && !dd.contains(e.target)) menu.classList.remove('open');
});

// ── Query expand/collapse with AJAX answers ───────────────
var loadedQueries = new Set();
function toggleQuery(qid, el) {
  var panel = document.getElementById('panel-' + qid);
  if (!panel) return;
  var isOpen = el.classList.contains('open-panel');
  // Close all
  document.querySelectorAll('.query-item.open-panel').forEach(function(item) {
    item.classList.remove('open-panel');
    var p = item.querySelector('[id^="panel-"]');
    if (p) p.style.display = 'none';
  });
  if (!isOpen) {
    el.classList.add('open-panel');
    panel.style.display = 'block';
    loadAnswers(qid);
  }
}

function loadAnswers(qid) {
  if (loadedQueries.has(qid)) return;
  loadedQueries.add(qid);
  var container = document.getElementById('answers-' + qid);
  if (!container) return;
  fetch('/api/query/' + qid)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.error) { container.textContent = 'Could not load answers.'; return; }
      if (!data.answers.length) {
        container.innerHTML = '<p class="no-answers-yet"><i class="fas fa-comment-slash"></i> No answers posted yet.</p>';
        return;
      }
      var html = '';
      data.answers.forEach(function(a) {
        html += '<div class="answer-card-inline">' +
          '<div class="ans-meta">' +
          '<span class="ans-instructor"><i class="fas fa-chalkboard-teacher"></i> ' + esc(a.instructor) + '</span>' +
          '<span class="ans-time">' + a.created_at.slice(0,16) + '</span>' +
          '</div><div class="ans-body">' + esc(a.body) + '</div></div>';
      });
      container.innerHTML = html;
    })
    .catch(function() { container.textContent = 'Could not load answers.'; });
}

function esc(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#039;')
    .replace(/\n/g,'<br>');
}

// ── Tab navigation ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.tab-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var tab = btn.dataset.tab;
      var nav = btn.closest('.tab-nav');
      if (!nav) return;
      nav.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      // Find adjacent tab-content siblings
      var sibling = nav.nextElementSibling;
      while (sibling) {
        if (sibling.classList.contains('tab-content')) sibling.classList.remove('active');
        sibling = sibling.nextElementSibling;
      }
      var content = document.getElementById('tab-' + tab);
      if (content) content.classList.add('active');
    });
  });

  // Filter pills (status filter)
  document.querySelectorAll('.filter-pills').forEach(function(container) {
    container.querySelectorAll('.filter-pill[data-filter]').forEach(function(pill) {
      pill.addEventListener('click', function() {
        container.querySelectorAll('.filter-pill[data-filter]').forEach(function(p) { p.classList.remove('active'); });
        pill.classList.add('active');
        var filter = pill.dataset.filter;
        var queryList = container.closest('.card, .tab-content, .card-body');
        if (!queryList) queryList = document.body;
        queryList.querySelectorAll('.query-item[data-status]').forEach(function(item) {
          item.style.display = (filter === 'all' || item.dataset.status === filter) ? '' : 'none';
        });
      });
    });
  });

  // Auto-dismiss alerts
  document.querySelectorAll('.alert').forEach(function(alert) {
    setTimeout(function() {
      alert.style.transition = 'opacity .4s';
      alert.style.opacity = '0';
      setTimeout(function() { alert.remove(); }, 400);
    }, 5000);
  });
});

// ── Table search ───────────────────────────────────────────
function filterTable(tableId, query) {
  var q = query.toLowerCase();
  var rows = document.querySelectorAll('#' + tableId + ' tbody tr');
  rows.forEach(function(row) {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// ── Admin tab helper (for sidebar links) ──────────────────
function openAdminTab(tab) {
  setTimeout(function() {
    var btn = document.querySelector('[data-tab="' + tab + '"]');
    if (btn) btn.click();
  }, 100);
}
