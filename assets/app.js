/* 국방기술과제 인벤토리 - front-end (vanilla JS, no build step) */
(function () {
  'use strict';
  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmt = (n) => (n == null ? '–' : Number(n).toLocaleString('ko-KR', { maximumFractionDigits: 2 }));
  const FIELD_ORDER = ['인공지능', '유·무인 복합', '양자', '우주', '에너지', '첨단소재', '사이버·네트워크', '센서·전자기전', '추진', 'WMD 대응'];
  const TYPE_ORDER = ['기초연구', '응용연구', '응용/시험', '시험개발', '무기체계 패키지형', '선도형 핵심기술', '핵심SW', '선행핵심기술', '국제공동기술개발', '미래도전국방기술', '민·군기술협력'];
  const EDITIONS = ['2022', '2023', '2024', '2025', '2026'];
  const EDITION_LABEL = { 2022: '’22-’36', 2023: '’23-’37', 2024: '’24-’38', 2025: '’25-’39', 2026: '’26-’40' };
  const STATUS_CLASS = { '진행 중': 'st-run', '종료': 'st-end', '착수 예정': 'st-plan' };

  let DATA = null, TAX = null, projects = [], byId = {};
  const state = { q: '', field: '', stech: '', type: '', status: '', edition: '', latest: false, sort: 'inventory_id', asc: true, shown: 100 };

  // ------------------------------------------------------------ bootstrap
  Promise.all([fetch('data/inventory.json').then((r) => r.json()), fetch('data/taxonomy.json').then((r) => r.json())])
    .then(([inv, tax]) => {
      DATA = inv; TAX = tax; projects = inv.projects; projects.forEach((p) => (byId[p.inventory_id] = p));
      initFilters(); renderDashboard(); renderTaxonomy(); renderAbout(); initChanges();
      window.addEventListener('hashchange', route); route();
    })
    .catch((e) => { $('main').innerHTML = '<p class="empty">데이터를 불러오지 못했습니다. GitHub Pages 또는 로컬 웹서버(예: <code>python -m http.server</code>)에서 열어 주세요.<br>' + esc(e) + '</p>'; });

  function route() {
    const h = (location.hash || '#dashboard').slice(1);
    const [tab, arg] = h.split('/');
    const known = ['dashboard', 'inventory', 'taxonomy', 'changes', 'about'];
    const t = known.includes(tab) ? tab : (tab.startsWith('KDTI') ? 'inventory' : 'dashboard');
    $$('.view').forEach((v) => (v.hidden = v.id !== 'view-' + t));
    $$('.tabs a').forEach((a) => a.classList.toggle('active', a.dataset.tab === t));
    if (t === 'inventory') renderTable();
    if (t === 'changes') renderChanges();
    if (tab.startsWith('KDTI') && byId[tab]) openModal(tab);
    if (t === 'taxonomy' && arg) { const el = document.getElementById('tax-' + decodeURIComponent(arg)); if (el) { el.open = true; el.scrollIntoView({ block: 'start' }); } }
  }

  // ------------------------------------------------------------ dashboard
  function renderDashboard() {
    const s = DATA.stats;
    const tiles = [
      { v: s.total_projects, l: '전체 과제 수', s: '’22~’25년판에서 식별된 고유 과제' },
      { v: s.by_edition['2025'], l: '’25-’39 기획서 과제 목록', s: '최신 전체 목록(예산 포함)' },
      { v: s.by_status['진행 중'] || 0, l: '진행 중', s: '2026년 기준 사업기간 내' },
      { v: s.by_status['착수 예정'] || 0, l: '착수 예정', s: '2027년 이후 착수' },
      { v: s.ai_projects, l: '인공지능 분야 연계 과제', s: '국방전략기술 분류 기준' },
      { v: Math.round(s.budget_total_2025_master), l: '예산 합계(억원)', s: '’25-’39 과제 목록 644건' },
    ];
    $('#stat-tiles').innerHTML = tiles.map((t) => `<div class="stat"><div class="v">${fmt(t.v)}</div><div class="l">${t.l}</div><div class="s">${t.s}</div></div>`).join('');
    const byField = FIELD_ORDER.map((f) => [f, s.by_field[f] || 0]);
    bars('#chart-field', byField, { cls: '' });
    bars('#chart-type', TYPE_ORDER.filter((t) => s.by_program_type[t]).map((t) => [t, s.by_program_type[t]]), { cls: 'alt' });
    bars('#chart-edition', EDITIONS.filter((y) => s.by_edition[y]).map((y) => [EDITION_LABEL[y] + ' (' + y + '년판)', s.by_edition[y]]), { cls: 'warm' });
    bars('#chart-budget', FIELD_ORDER.map((f) => [f, Math.round(s.budget_by_field_2025_master[f] || 0)]).concat([['미연계', Math.round(s.budget_by_field_2025_master['미분류'] || 0)]]), { cls: '', unit: '억원' });
    const ai = {};
    projects.filter((p) => p.field === '인공지능').forEach((p) => { ai[p.strategic_tech || '미상'] = (ai[p.strategic_tech || '미상'] || 0) + 1; });
    bars('#chart-ai', Object.entries(ai).sort((a, b) => b[1] - a[1]), { cls: '' });
    const l4 = TAX.ai_lv4_summary_2026;
    if (l4) {
      const row = (o) => Object.entries(o).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${fmt(v)}</td></tr>`).join('');
      $('#ai-lv4').innerHTML = `<figcaption style="font-weight:600;margin-bottom:8px">’26-’40 기획서 인공지능 분야 기술개발소요(Lv.4) 자동 집계</figcaption>
        <p class="src">30개 국방전략기술 → 100개 세부기술 → 300개 구성기술 아래에 도출된 기술개발소요를 확보시기·사업추진방안·확보여부로 집계한 값(총 ${fmt(l4.total)}건, 텍스트 패턴 집계이므로 참고용).</p>
        <div class="grid-2" style="margin:0"><table class="inv" style="min-width:0"><thead><tr><th>확보시기</th><th class="num">건수</th></tr></thead><tbody>${row(l4.by_timing)}</tbody></table>
        <table class="inv" style="min-width:0"><thead><tr><th>사업추진방안</th><th class="num">건수</th></tr></thead><tbody>${row(l4.by_approach)}</tbody></table>
        <table class="inv" style="min-width:0"><thead><tr><th>확보여부</th><th class="num">건수</th></tr></thead><tbody>${row(l4.by_need)}</tbody></table></div>`;
    }
  }
  function bars(sel, rows, opt) {
    const max = Math.max(1, ...rows.map((r) => r[1]));
    $(sel).innerHTML = '<div class="bars">' + rows.map(([k, v]) => `<div class="lbl">${esc(k)}</div><div class="track" title="${esc(k)}: ${fmt(v)}${opt.unit || ''}"><div class="bar ${opt.cls}" style="width:${(v / max) * 100}%"></div></div><div class="val">${fmt(v)}</div>`).join('') + '</div>';
  }

  // ------------------------------------------------------------ inventory table
  function initFilters() {
    const opt = (sel, vals) => { const el = $(sel); vals.forEach((v) => { const o = document.createElement('option'); o.value = v; o.textContent = v; el.appendChild(o); }); };
    opt('#f-field', FIELD_ORDER.concat(['(국방전략기술 미연계)']));
    opt('#f-type', TYPE_ORDER.filter((t) => projects.some((p) => p.program_type === t)));
    opt('#f-status', ['진행 중', '착수 예정', '종료']);
    opt('#f-edition', EDITIONS.filter((y) => DATA.stats.by_edition[y]).map((y) => y));
    $$('#f-edition option').forEach((o) => { if (o.value) o.textContent = EDITION_LABEL[o.value] + ' (' + o.value + '년판)'; });
    fillStech();
    $('#q').addEventListener('input', (e) => { state.q = e.target.value.trim().toLowerCase(); state.shown = 100; renderTable(); });
    $('#f-field').addEventListener('change', (e) => { state.field = e.target.value; state.stech = ''; fillStech(); state.shown = 100; renderTable(); });
    [['#f-stech', 'stech'], ['#f-type', 'type'], ['#f-status', 'status'], ['#f-edition', 'edition']].forEach(([s, k]) => $(s).addEventListener('change', (e) => { state[k] = e.target.value; state.shown = 100; renderTable(); }));
    $('#f-latest').addEventListener('change', (e) => { state.latest = e.target.checked; renderTable(); });
    $('#f-reset').addEventListener('click', () => { Object.assign(state, { q: '', field: '', stech: '', type: '', status: '', edition: '', latest: false, shown: 100 }); $('#q').value = ''; ['#f-field', '#f-stech', '#f-type', '#f-status', '#f-edition'].forEach((s) => ($(s).value = '')); $('#f-latest').checked = false; fillStech(); renderTable(); });
    $$('#tbl th').forEach((th) => th.addEventListener('click', () => { const k = th.dataset.k; if (state.sort === k) state.asc = !state.asc; else { state.sort = k; state.asc = true; } renderTable(); }));
    $('#more').addEventListener('click', () => { state.shown += 200; renderTable(); });
    $('#m-close').addEventListener('click', closeModal);
    $('#modal').addEventListener('click', (e) => { if (e.target.id === 'modal') closeModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
  }
  function fillStech() {
    const el = $('#f-stech'); el.innerHTML = '<option value="">국방전략기술 전체</option>';
    const set = new Set(projects.filter((p) => p.strategic_tech && (!state.field || p.field === state.field)).map((p) => p.strategic_tech));
    const order = []; TAX.fields.forEach((f) => f.techs.forEach((t) => order.push(t.name)));
    Array.from(set).sort((a, b) => order.indexOf(a) - order.indexOf(b)).forEach((v) => { const o = document.createElement('option'); o.value = v; o.textContent = v; el.appendChild(o); });
  }
  function filtered() {
    return projects.filter((p) => {
      if (state.field === '(국방전략기술 미연계)') { if (p.field) return false; } else if (state.field && p.field !== state.field) return false;
      if (state.stech && p.strategic_tech !== state.stech) return false;
      if (state.type && p.program_type !== state.type) return false;
      if (state.status && p.status !== state.status) return false;
      if (state.edition && !p.editions[state.edition]) return false;
      if (state.latest && !p.in_latest_master_list) return false;
      if (state.q) {
        const hay = [p.inventory_id, p.name, ...(p.name_variants || []), p.sub_tech, p.strategic_tech, p.field, p.legacy_2022_tech, ...(p.linked_core_techs || [])].join(' ').toLowerCase();
        if (!hay.includes(state.q)) return false;
      }
      return true;
    });
  }
  function renderTable() {
    const rows = filtered();
    const k = state.sort, dir = state.asc ? 1 : -1;
    rows.sort((a, b) => { const x = a[k], y = b[k]; if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1; return (x > y ? 1 : x < y ? -1 : 0) * dir; });
    $$('#tbl th').forEach((th) => { th.classList.toggle('sorted', th.dataset.k === k); th.classList.toggle('asc', th.dataset.k === k && state.asc); });
    $('#count').textContent = `${fmt(rows.length)}건 / 전체 ${fmt(projects.length)}건`;
    const slice = rows.slice(0, state.shown);
    $('#tbl tbody').innerHTML = slice.map((p) => `<tr data-id="${p.inventory_id}">
      <td><code>${p.inventory_id}</code></td>
      <td class="name-cell">${esc(p.name)}${p.sub_tech ? `<span class="sub-line">세부기술: ${esc(p.sub_tech)}</span>` : ''}</td>
      <td>${esc(p.program_type || '–')}${p.program_subtype ? `<span class="sub-line">${esc(p.program_subtype)}</span>` : ''}</td>
      <td>${p.start_year ? p.start_year + '–' + p.end_year : '–'}</td>
      <td>${esc(p.lead_type || '–')}</td>
      <td class="num">${fmt(p.budget_100m_krw)}</td>
      <td>${p.field ? esc(p.field) + '<span class="sub-line">' + esc(p.strategic_tech || '') + '</span>' : '<span class="src">미연계</span>'}</td>
      <td><span class="badge ${STATUS_CLASS[p.status] || ''}">${esc(p.status)}</span>${p.status_note ? '<span class="badge warn" title="' + esc(p.status_note) + '">최신목록 미수록</span>' : ''}</td>
      <td>${editionBadges(p)}</td></tr>`).join('') || '<tr><td colspan="9" class="empty">조건에 맞는 과제가 없습니다.</td></tr>';
    $$('#tbl tbody tr[data-id]').forEach((tr) => tr.addEventListener('click', () => { location.hash = '#' + tr.dataset.id; }));
    $('#more').hidden = rows.length <= state.shown;
  }
  const editionBadges = (p) => EDITIONS.filter((y) => y !== '2026').map((y) => `<span class="badge ed ${p.editions[y] ? 'on' : ''}" title="${EDITION_LABEL[y]} 기획서">${y.slice(2)}</span>`).join('');

  // ------------------------------------------------------------ project detail
  function openModal(id) {
    const p = byId[id]; if (!p) return;
    const kv = [
      ['인벤토리 ID', `<code>${p.inventory_id}</code>`],
      ['사업구분', esc(p.program_type || '–') + (p.program_subtype ? ' / ' + esc(p.program_subtype) : '')],
      ['사업기간', p.start_year ? `${p.start_year}–${p.end_year}` + (p.duration_months ? ` (${p.duration_months}개월)` : '') : '–'],
      ['주관형태', esc(p.lead_type || '–')],
      ['예산(억원)', fmt(p.budget_100m_krw)],
      ['국방전략기술 분야', p.field ? esc(p.field) : '<span class="src">미연계(제3장 과제 목록에만 수록)</span>'],
      ['국방전략기술', esc(p.strategic_tech || '–')],
      ['세부기술', esc(p.sub_tech || '–')],
      ['상태', `<span class="badge ${STATUS_CLASS[p.status] || ''}">${esc(p.status)}</span> ${p.status_note ? '<span class="badge warn">' + esc(p.status_note) + '</span>' : ''}`],
      ['수록 기획서', p.editions_listed.map((y) => EDITION_LABEL[y] + ' (' + y + ')').join(' · ')],
    ];
    if (p.legacy_2022_field) kv.push(['’22-’36 체계 분류', esc(p.legacy_2022_field) + ' › ' + esc(p.legacy_2022_tech || '')]);
    if (p.linked_core_techs && p.linked_core_techs.length) kv.push(['연계 핵심기술/국방기술', p.linked_core_techs.map(esc).join('<br>')]);
    if (p.name_variants.length > 1) kv.push(['과제명 표기(연도별)', p.name_variants.map(esc).join('<br>')]);
    const edRows = Object.keys(p.editions).sort().map((y) => { const e = p.editions[y]; return `<tr><td>${EDITION_LABEL[y]} (${y})</td><td>${e.project_no ?? e.project_no_ch3 ?? '–'}</td><td>${esc(e.stage || '–')}</td><td>${esc(e.period || '–')}</td><td>${esc(e.field || e.legacy_field || '–')}${e.strategic_tech ? ' › ' + esc(e.strategic_tech) : e.legacy_tech ? ' › ' + esc(e.legacy_tech) : ''}${e.sub_tech ? ' › ' + esc(e.sub_tech) : ''}</td><td>${e.status_tag ? esc(e.status_tag) : ''}${e.budget_100m_krw != null ? ' ' + fmt(e.budget_100m_krw) + '억원' : ''}</td></tr>`; }).join('');
    const subst = p.changes.filter((c) => c.item !== '과제번호');
    $('#m-body').innerHTML = `<h2>${esc(p.name)}</h2>
      <dl class="kv">${kv.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>
      <h3>기획서 연도별 수록 내역</h3>
      <table><thead><tr><th>기획서</th><th>과제번호</th><th>사업구분</th><th>기간</th><th>분류</th><th>비고</th></tr></thead><tbody>${edRows}</tbody></table>
      <h3>연도별 변경 사항 ${subst.length ? '' : '<span class="src">(과제번호 재부여 외 변경 없음)</span>'}</h3>
      ${subst.length ? '<ul>' + subst.map((c) => `<li>${c.from_edition}→${c.to_edition}년판 <b>${esc(c.item)}</b>: <span class="before">${esc(c.before)}</span> → <span class="after">${esc(c.after)}</span></li>`).join('') + '</ul>' : ''}
      ${p.description ? `<h3>개요</h3><p>${esc(p.description)}</p>` : ''}`;
    $('#modal').hidden = false; document.body.style.overflow = 'hidden';
  }
  function closeModal() { if ($('#modal').hidden) return; $('#modal').hidden = true; document.body.style.overflow = ''; if (location.hash.startsWith('#KDTI')) history.replaceState(null, '', '#inventory'); }

  // ------------------------------------------------------------ taxonomy
  function renderTaxonomy() {
    const chips = (ids) => ids.length ? ids.map((id) => `<button class="chip" data-id="${id}" title="${esc(byId[id] ? byId[id].name : id)}">${esc(byId[id] ? shorten(byId[id].name) : id)}</button>`).join('') : '<span class="src">연계 과제 없음</span>';
    $('#tax').innerHTML = TAX.fields.map((f) => `<details class="tax-field" id="tax-${esc(f.name)}"${f.name === '인공지능' ? ' open' : ''}><summary>${esc(f.name)}<span class="cnt">국방전략기술 ${f.techs.length}개 · 연계 과제 ${f.techs.reduce((a, t) => a + t.projects.length, 0)}건</span></summary>
      ${f.techs.map((t) => `<div class="tax-tech"><h3>${esc(t.name)} <span class="src">(${t.projects.length}건)</span></h3><p class="desc">${esc(t.desc || '')} ${t.desc_source ? `<span class="src">— ${EDITION_LABEL[t.desc_source]} 기획서</span>` : ''}</p>
        ${t.subs.map((s) => `<div class="tax-sub"><h4>${esc(s.code)}. ${esc(s.name)} <span class="src">${s.desc_source === '2026' ? '’26-’40 세부기술(Lv.2)' : '’25-’39 세부기술'}</span></h4>
          ${s.desc ? `<p class="desc">${esc(s.desc)}</p>` : ''}${s.desc_2025 && s.desc_source === '2026' ? `<p class="desc src">’25-’39 정의: ${esc(s.desc_2025)}</p>` : ''}
          ${s.lv3 && s.lv3.length ? `<ul class="tax-lv3">${s.lv3.map((m) => `<li><b>${esc(m.code)} ${esc(m.name)}</b> — ${esc(m.desc)}</li>`).join('')}</ul>` : ''}
          <div>${chips(s.projects)}</div></div>`).join('')}
        ${(() => { const mapped = new Set(t.subs.flatMap((s) => s.projects)); const rest = t.projects.filter((id) => !mapped.has(id)); return rest.length ? `<div class="tax-sub"><h4>세부기술 미표시 연계 과제</h4><div>${chips(rest)}</div></div>` : ''; })()}
      </div>`).join('')}</details>`).join('');
    $('#legacy').innerHTML = TAX.legacy_2022.fields.map((f) => `<details class="tax-field"><summary>${esc(f.name)}<span class="cnt">국방전략기술 ${f.techs.length}개 · 핵심기술 ${f.techs.reduce((a, t) => a + t.core_techs.length, 0)}개</span></summary>
      ${f.techs.map((t) => `<div class="tax-tech"><h3>${esc(t.name)}</h3><p class="desc">${esc(t.desc)}</p>
        ${t.core_techs.map((k) => `<div class="tax-sub"><h4>${esc(k.name)}</h4><p class="desc">${esc(k.desc)}</p>${k.projects.length ? '<div>' + chips(k.projects) + '</div>' : ''}</div>`).join('')}</div>`).join('')}</details>`).join('');
    $$('#tax .chip, #legacy .chip').forEach((b) => b.addEventListener('click', () => { location.hash = '#' + b.dataset.id; }));
  }
  const shorten = (s) => (s.length > 34 ? s.slice(0, 33) + '…' : s);

  // ------------------------------------------------------------ changes
  function initChanges() {
    const el = $('#c-field'); FIELD_ORDER.forEach((f) => { const o = document.createElement('option'); o.value = f; o.textContent = f; el.appendChild(o); });
    ['#c-item', '#c-field', '#c-dropped'].forEach((s) => $(s).addEventListener('change', renderChanges));
  }
  function renderChanges() {
    const item = $('#c-item').value, field = $('#c-field').value, dropped = $('#c-dropped').checked;
    const rows = projects.filter((p) => {
      if (field && p.field !== field) return false;
      if (dropped) return !!p.status_note;
      const ch = p.changes.filter((c) => (item ? c.item === item : c.item !== '과제번호'));
      return ch.length > 0;
    });
    $('#changes').innerHTML = rows.slice(0, 400).map((p) => {
      const ch = p.changes.filter((c) => (item ? c.item === item : c.item !== '과제번호'));
      return `<div class="chg"><h4 data-id="${p.inventory_id}"><code>${p.inventory_id}</code> ${esc(p.name)} <span class="src">${esc(p.program_type || '')} · ${p.editions_listed.join('/')}</span>${p.status_note ? ' <span class="badge warn">최신목록 미수록</span>' : ''}</h4>
        ${ch.length ? '<ul>' + ch.map((c) => `<li>${c.from_edition}→${c.to_edition} <b>${esc(c.item)}</b>: <span class="before">${esc(c.before)}</span> → <span class="after">${esc(c.after)}</span></li>`).join('') + '</ul>' : `<ul><li>${esc(p.status_note || '')} (마지막 수록: ${EDITION_LABEL[p.latest_edition]} 기획서, 기간 ${p.start_year}–${p.end_year})</li></ul>`}</div>`;
    }).join('') || '<p class="empty">해당하는 변경 사항이 없습니다.</p>';
    if (rows.length > 400) $('#changes').insertAdjacentHTML('beforeend', `<p class="empty">${fmt(rows.length)}건 중 400건만 표시합니다. 필터를 좁혀 주세요.</p>`);
    $$('#changes h4').forEach((h) => h.addEventListener('click', () => { location.hash = '#' + h.dataset.id; }));
  }

  // ------------------------------------------------------------ about
  function renderAbout() {
    const m = DATA.meta, s = DATA.stats;
    const edRows = Object.entries(m.editions).map(([y, e]) => `<tr><td>${esc(e.title)}</td><td>${esc(e.published)}</td><td>${e.pages_total}쪽</td><td>${fmt(s.by_edition[y])}</td><td>${esc(e.coverage)}</td></tr>`).join('');
    const map = [
      ['Use Case ID', 'inventory_id', '사이트 고유 식별자(KDTI-####). 기획서 과제번호는 매년 재부여되어 editions.{연도}.project_no 에 보관'],
      ['Use Case Name', 'name', '과제명(최신 기획서 표기). 연도별 표기 차이는 name_variants'],
      ['Bureau / Component', 'program_type, program_subtype, lead_type', '사업구분(기초연구·응용연구·시험개발·무기체계 패키지형·미래도전국방기술 등)과 주관형태(산학연·국과연 등)'],
      ['Topic Area', 'field › strategic_tech › sub_tech', '10대 국방전략기술 분야 › 30개 국방전략기술 › 세부기술'],
      ['Development Stage / Date Initiated / Deployed', 'status, start_year, end_year', '사업기간으로부터 2026년 기준 상태(착수 예정·진행 중·종료) 산출'],
      ['Contracting Usage / Vendor', 'lead_type', '산학연(업체·대학·정출연) / 국과연 주관 구분'],
      ['Problem Solved / Benefits', 'strategic_tech, sub_tech, linked_core_techs', '과제가 확보하려는 국방전략기술·세부기술·핵심기술 명세(기술체계 탭)'],
      ['Is High-Impact', '—', '해당 없음(공개본에 영향도 구분 없음). 예산(budget_100m_krw)과 사업구분으로 대체 참고'],
      ['Retired / Previously Reported', 'status_note, editions_listed', '최신 과제 목록(’25-’39)에 미수록된 과제를 표시하고, 과거 기획서 수록 이력을 보관'],
    ];
    $('#about').innerHTML = `<h2>자료 개요</h2>
      <p>이 사이트는 국방기술진흥연구소가 매년 발간하는 「국방기술기획서(일반본)」 ’22-’36 · ’23-’37 · ’24-’38 · ’25-’39 · ’26-’40 다섯 권에 수록된 국방기술과제를 한 곳에 모은 인벤토리입니다. 구성 방식은 미 연방정부 관리예산처(OMB)의 <a href="https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory/blob/main/Reporting%20Instructions/Reporting%20Instructions.md" rel="noopener">2025 AI Use Case Inventory 보고 지침</a>과 <a href="https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory" rel="noopener">통합 인벤토리 저장소</a>를 참고했습니다. 하나의 과제가 한 행이 되고, 과제 식별자·명칭·소관(사업구분)·주제 분야·개발 단계·기간을 기본 항목으로 두며, 연도별 변경 이력을 함께 보관합니다.</p>
      <h2>병합 원칙(최신자료 우선)</h2>
      <ul>${m.notes.map((n) => `<li>${esc(n)}</li>`).join('')}</ul>
      <h2>기획서별 추출 범위</h2>
      <table><thead><tr><th>기획서</th><th>발간</th><th>분량</th><th>수록 과제(추출)</th><th>추출 범위</th></tr></thead><tbody>${edRows}</tbody></table>
      <p class="src">원문 PDF(권당 20~32MB)는 Google Drive 연동으로 본문 앞부분만 텍스트 변환이 가능했습니다. 전체 PDF 텍스트를 data/source 에 넣고 <code>scripts/</code> 파서를 다시 실행하면 나머지 장(제3장 과제 목록, 부록 과제카드)까지 같은 형식으로 확장할 수 있습니다.</p>
      <h2>OMB AI Use Case Inventory 항목과의 대응</h2>
      <table><thead><tr><th>OMB 항목</th><th>본 인벤토리 필드</th><th>설명</th></tr></thead><tbody>${map.map((r) => `<tr><td>${esc(r[0])}</td><td><code>${esc(r[1])}</code></td><td>${esc(r[2])}</td></tr>`).join('')}</tbody></table>
      <h2>원문 PDF 텍스트 변환</h2>
      <p>전체 PDF를 반영하려면 <a href="tools/pdf2text.html">브라우저용 PDF 텍스트 변환기</a>로 각 권을 .txt로 바꾼 뒤 <code>data/source/</code>에 넣고 빌드를 다시 실행합니다. 변환은 사용자의 브라우저 안에서만 이루어지며 파일이 외부로 전송되지 않습니다.</p>
      <h2>데이터 파일</h2>
      <ul><li><code>data/inventory.json</code> — 과제별 전체 필드(연도별 이력 포함)</li><li><code>data/inventory.csv</code> — 1행 1과제 평면 표(UTF-8 BOM)</li><li><code>data/taxonomy.json</code> — 10대 분야 30개 국방전략기술 체계(’26-’40 인공지능 Lv.3 포함)와 ’22-’36 체계</li><li><code>data/intermediate/</code> — 기획서별 파싱 결과</li></ul>
      <h2>유의 사항</h2>
      <ul><li>PDF 텍스트 변환 과정에서 표의 열이 섞인 경우가 있어 일부 과제명·세부기술명에 오탈자가 남아 있을 수 있습니다.</li>
      <li>과제 동일성은 과제명을 정규화해 판정했으며, 명칭이 크게 바뀐 과제는 별도 과제로 남을 수 있습니다(연도별 변화 탭의 ‘최신 과제 목록 미수록’ 참고).</li>
      <li>’26-’40 기획서는 인공지능 분야 기술체계(제2장)만 반영되었고, 제3장 과제 목록은 반영되지 않았습니다. 따라서 과제 목록의 최신 기준은 ’25-’39 기획서입니다.</li></ul>`;
  }
})();
