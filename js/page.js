/* Does Parliament notice disasters, and whose? UK disasters 1910 to 2020 on a plain MapLibre base map (OpenFreeMap Positron),
 * sized by deaths and coloured by the Commons attention that followed, with a monthly sparkline in each popup.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => n == null ? 'n/a' : Number(n).toLocaleString('en-GB');
  const SEQ = ['#C9C2B4', '#C9A27A', '#B4652E', '#7A2A22'];
  const TCOL = { 'Mining': '#4A4038', 'Transport': '#2F6A9E', 'Fire or explosion': '#B4652E', 'Crowd crush': '#7A4FA0', 'Bombing or shooting': '#A23B4B', 'Other': '#3B8B6A' };
  const TLAB = { mining: 'Mining', rail: 'Rail', air: 'Air', sea: 'Sea and river', fire: 'Fire', explosion: 'Explosion', crowd: 'Crowd crush', violence: 'Bombing or shooting', flood: 'Flood', health: 'Disease outbreak', other: 'Other' };
  let map = null, D = null, mode = qs.get('mode') || 'xpd';
  const types = new Set(Object.keys(TCOL)); let fromY = 1900, toY = 2030, showExt = true;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function colorExpr() {
    if (mode === 'type') return ['match', ['get', 'tg'], ...Object.entries(TCOL).flat(), '#888'];
    return ['step', ['get', 'xpd'], SEQ[0], 0.25, SEQ[1], 1, SEQ[2], 4, SEQ[3]];
  }
  function key() {
    const t = document.getElementById('keyTitle'), b = document.getElementById('keyRows');
    if (mode === 'type') { t.textContent = 'Kind of disaster'; b.innerHTML = Object.entries(TCOL).map(([k, c]) => `<div class="row"><span class="dot" style="background:${c}"></span>${k}</div>`).join(''); }
    else { t.textContent = 'Extra Commons contributions per death, five years'; b.innerHTML = [['under ¼', 0], ['¼ to 1', 1], ['1 to 4', 2], ['4 or more', 3]].map(([l, i]) => `<div class="row"><span class="dot" style="background:${SEQ[i]}"></span>${l}</div>`).join(''); }
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  function filt() {
    const tf = ['in', ['get', 'tg'], ['literal', [...types]]];
    const yf = ['all', ['>=', ['get', 'y'], fromY], ['<=', ['get', 'y'], toY]];
    const xf = showExt ? ['>=', ['get', 'x'], 0] : ['==', ['get', 'x'], 0];
    map.setFilter('pts', ['all', ['==', ['get', 'm'], 1], tf, yf, xf]);
    map.setFilter('fpts', ['all', ['==', ['get', 'm'], 0], tf, yf, xf]);
    map.setFilter('lbl', ['all', ['==', ['get', 'm'], 1], tf, yf, xf]);
    map.setFilter('xpts', ['all', ['>=', ['get', 'y'], fromY], ['<=', ['get', 'y'], toY]]);
    const n = D.events.filter(e => e.m === 1 && (showExt || !e.x) && types.has(e.tg) && e.y >= fromY && e.y <= toY).length;
    document.getElementById('nShown').textContent = n;
  }
  function refresh() { map.setPaintProperty('pts', 'circle-color', colorExpr()); key(); }
  function spark(s, b) {
    const W = 280, H = 70, n = s.length, mx = Math.max(1, ...s, b * 2);
    const x = i => 4 + i * (W - 8) / (n - 1), y = v => H - 12 - (H - 20) * v / mx;
    const bars = s.map((v, i) => v ? `<rect x="${(x(i) - 1.3).toFixed(1)}" y="${y(v).toFixed(1)}" width="2.6" height="${(H - 12 - y(v)).toFixed(1)}" fill="${i >= 24 ? '#8C3B2E' : '#8E8778'}"/>` : '').join('');
    return `<svg class="spk" viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Monthly contributions from two years before to five years after"><line x1="${x(24) - 2}" x2="${x(24) - 2}" y1="2" y2="${H - 12}" stroke="#6B655B" stroke-dasharray="2 2"/>${bars}<line x1="4" x2="${W - 4}" y1="${H - 12}" y2="${H - 12}" stroke="#6B655B"/><text x="4" y="${H - 1}" font-size="9" fill="#6B655B">-2 years</text><text x="${x(24)}" y="${H - 1}" font-size="9" fill="#6B655B" text-anchor="middle">event</text><text x="${W - 4}" y="${H - 1}" font-size="9" fill="#6B655B" text-anchor="end">+5 years</text><text x="${W - 4}" y="10" font-size="9" fill="#6B655B" text-anchor="end">peak ${mx > 1 ? fmt(Math.max(...s)) : 0} a month</text></svg>`;
  }
  function popup(p, ll) {
    const s = typeof p.s === 'string' ? JSON.parse(p.s) : p.s;
    let h = `<b class="t">${esc(p.n)}</b><div class="nt">${esc(p.d)} · ${esc(TLAB[p.ty] || p.ty)} · ${esc(p.rg)}</div><table>`;
    h += `<tr><td>Deaths</td><td><b>${fmt(p.dt)}</b> <span class="nt">(${p.src === 'list' ? 'Wikipedia list' : p.src === 'wikidata' ? 'Wikidata' : 'Wikipedia article, checked'})</span></td></tr>`;
    h += `<tr><td>Search term</td><td>${p.kd === 'in' ? '"in ' + esc(p.t) + '"' : '"' + esc(p.t) + '"'}</td></tr>`;
    h += `<tr><td>Usual level</td><td>${p.b.toFixed(2)} contributions a month</td></tr>`;
    h += `<tr><td>Five years after</td><td><b>${fmt(p.C)}</b> contributions (${fmt(Math.round(p.E))} expected at the usual level)</td></tr>`;
    h += `<tr><td>First three months</td><td>${fmt(p.P)}</td></tr>`;
    if (p.h != null && p.h !== 'null') h += `<tr><td>Half the extra by</td><td>month ${p.h}</td></tr>`;
    h += '</table>' + spark(s, p.b);
    if (p.fl === 'seat') h += '<p class="nt">The search word is also a Commons seat name, which adds a steady level of mentions; the usual level allows for it.</p>';
    if (p.m === 0) h += '<p class="nt">Left out of the main analysis: the search word has other common meanings in debate.</p>';
    if (+p.x === 1) h += '<p class="nt">Added later: its search word was found after the first results, and it is in the extended analysis only.</p>';
    h += `<p class="nt">Hansard (Open Parliament Licence v3.0), Commons spoken contributions per month. <a href="https://hansard.parliament.uk/search?searchTerm=${encodeURIComponent('"' + (p.kd === 'in' ? 'in ' : '') + p.t + '"')}" target="_blank" rel="noopener">Search Hansard</a></p>`;
    new maplibregl.Popup({ maxWidth: '320px', anchor: small ? 'bottom' : undefined, focusAfterOpen: false }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function popupX(p, ll) {
    const h = `<b class="t">${esc(p.n)}</b><div class="nt">${esc(p.y)}${p.dt != null && p.dt !== 'null' ? ' · ' + fmt(p.dt) + ' deaths' : ''}</div><p class="nt">Not in the analysis: ${esc(p.why)}.</p>`;
    new maplibregl.Popup({ maxWidth: '300px', focusAfterOpen: false }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function setup() {
    const feats = D.events.map((e, i) => ({ type: 'Feature', properties: Object.assign({ i, sz: Math.sqrt(e.dt) }, e, { s: JSON.stringify(e.s) }), geometry: { type: 'Point', coordinates: [e.lon, e.lat] } }));
    feats.sort((a, b) => b.properties.dt - a.properties.dt);
    const xf = D.excluded.map((e, i) => ({ type: 'Feature', properties: Object.assign({ i }, e), geometry: { type: 'Point', coordinates: [e.lon, e.lat] } }));
    map.addSource('e', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Hansard: Open Parliament Licence v3.0; Wikipedia (CC BY-SA); Wikidata (CC0)' });
    map.addSource('x', { type: 'geojson', data: { type: 'FeatureCollection', features: xf } });
    const rad = ['interpolate', ['linear'], ['zoom'], 4, ['+', 3, ['*', small ? 0.55 : 0.75, ['get', 'sz']]], 8, ['+', 5, ['*', 1.0, ['get', 'sz']]], 13, ['+', 8, ['*', 1.3, ['get', 'sz']]]];
    map.addLayer({ id: 'xpts', type: 'circle', source: 'x', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3, 9, 5, 13, 7], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#8E8778', 'circle-stroke-width': 1.4 } });
    map.addLayer({ id: 'fpts', type: 'circle', source: 'e', filter: ['==', ['get', 'm'], 0], paint: { 'circle-radius': rad, 'circle-color': '#D8D2C6', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2 } });
    map.addLayer({ id: 'pts', type: 'circle', source: 'e', filter: ['==', ['get', 'm'], 1], paint: { 'circle-radius': rad, 'circle-color': colorExpr(), 'circle-stroke-color': ['case', ['==', ['get', 'x'], 1], '#24211D', '#fff'], 'circle-stroke-width': ['case', ['==', ['get', 'x'], 1], 2, 1.3], 'circle-opacity': 0.92 } });
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'e', minzoom: 7, layout: { 'text-field': ['concat', ['get', 't'], ' ', ['to-string', ['get', 'y']]], 'text-size': 11.5, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.2], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#24211D', 'text-halo-color': '#fff', 'text-halo-width': 1.5 } });
    ['pts', 'fpts'].forEach(l => { map.on('click', l, e => popup(e.features[0].properties, e.lngLat)); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    map.on('click', 'xpts', e => { if (map.queryRenderedFeatures(e.point, { layers: ['pts', 'fpts'] }).length) return; popupX(e.features[0].properties, e.lngLat); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyP').addEventListener('change', e => vis(['pts'], e.target.checked));
    document.getElementById('lyN').addEventListener('change', e => { showExt = e.target.checked; filt(); });
    document.getElementById('lyF').addEventListener('change', e => vis(['fpts'], e.target.checked));
    document.getElementById('lyX').addEventListener('change', e => vis(['xpts'], e.target.checked));
    document.getElementById('lyL').addEventListener('change', e => vis(['lbl'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && l.id !== 'lbl').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    document.querySelectorAll('input[data-t]').forEach(c => c.addEventListener('change', () => { c.checked ? types.add(c.dataset.t) : types.delete(c.dataset.t); filt(); }));
    const dec = document.getElementById('dec');
    dec.addEventListener('change', () => { const v = dec.value.split('-').map(Number); fromY = v[0]; toY = v[1]; filt(); });
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    refresh(); filt();
  }
  function go(i) {
    const p = D.events[i]; fold(true);
    map.flyTo({ center: [p.lon, p.lat], zoom: small ? 8.5 : 9, duration: 1200, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.3 : 0.22))] });
    map.once('moveend', () => popup(Object.assign({}, p), [p.lon, p.lat]));
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.events.map((p, i) => ({ n: p.n, nn: norm(p.n + ' ' + p.t), i, s: p.y }));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.n)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.n; sug.style.display = 'none'; go(it.i); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const i = D.events.findIndex(p => p.id === a.dataset.go); if (i < 0) return;
      document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); go(i); }));
  }
  fetch('data/site.json').then(r => r.json()).then(d => {
    D = d;
    const mo = { bounds: [[-8.3, 49.9], [1.9, 58.8]], fitBoundsOptions: { padding: small ? 10 : { top: 40, bottom: 40, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    if (qs.get('event')) { const i = D.events.findIndex(p => p.id === qs.get('event')); if (i >= 0) go(i); }
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov-top,.lp,.keys,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
