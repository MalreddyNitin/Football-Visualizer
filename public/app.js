const $ = (id) => document.getElementById(id);

async function getJSON(path, params) {
  const q = new URLSearchParams(params).toString();
  const r = await fetch(`/api/${path}?${q}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function pitchLayout(extra = {}) {
  return {
    xaxis: { range: [0, 100], showgrid:false, zeroline:false, visible:false },
    yaxis: { range: [0, 100], showgrid:false, zeroline:false, visible:false, scaleanchor:'x', scaleratio:1 },
    paper_bgcolor: '#0f1115',
    plot_bgcolor: '#0f1115',
    font: { color: '#e5e7eb' },
    margin: { l:20, r:20, t:40, b:20 },
    ...extra
  };
}

function nodeTrace(n) {
  return {
    x: [n.x], y: [n.y], mode: 'markers+text', type:'scatter',
    marker: { size: 18, color: '#3b82f6', line:{ color:'#fff', width:2 }},
    text: [n.shirtNo || ''], textposition:'top center',
    hovertemplate: `${n.name}<extra></extra>`
  };
}

function lineTrace(a, b, width=2, color='#e5e7eb', hover='') {
  return {
    x: [a.x, b.x], y: [a.y, b.y], mode: 'lines', type:'scatter',
    line: { width, color }, hovertemplate: hover ? `${hover}<extra></extra>` : '<extra></extra>'
  };
}

async function maybeLoadPlayers(url, team) {
  try {
    const players = await getJSON('players', { url, team });
    const sel = $('player');
    sel.innerHTML = '';
    for (const p of players) {
      const opt = document.createElement('option');
      opt.value = p.playerId;
      opt.textContent = `${p.shirtNo ?? ''} ${p.name}`;
      sel.appendChild(opt);
    }
    $('player-wrap').classList.toggle('hidden', players.length === 0);
  } catch (e) {
    console.warn('players load failed', e);
    $('player-wrap').classList.add('hidden');
  }
}

async function render() {
  const url = $('url').value.trim();
  const team = $('team').value.trim();
  const viz = $('viz').value;

  if (!url || !team) {
    alert('Please enter match URL and Team.');
    return;
  }

  // update players list (useful for player-specific views later)
  maybeLoadPlayers(url, team);

  try {
    if (viz === 'pass-network') {
      const data = await getJSON('pass-network', { url, team });
      const traces = [];
      // edges
      for (const e of data.links) {
        const s = data.nodes.find(n => n.playerId === e.source);
        const t = data.nodes.find(n => n.playerId === e.target);
        if (!s || !t) continue;
        traces.push(lineTrace(s, t, Math.max(1, Math.min(8, e.count / 2)), '#9ca3af', `${e.count} passes`));
      }
      // nodes
      for (const n of data.nodes) traces.push(nodeTrace(n));
      Plotly.newPlot('plot', traces, pitchLayout({ title: `Pass Network – ${team}` }), {displayModeBar:false});
      return;
    }

    if (viz === 'box-passes') {
      const res = await getJSON('box-passes', { url, team });
      const lines = res.passes.map(p => lineTrace({x:p.x,y:p.y},{x:p.endX,y:p.endY},2,'#22c55e','Successful box pass'));
      Plotly.newPlot('plot', lines, pitchLayout({ title: `Successful Box Passes – ${team}` }), {displayModeBar:false});
      return;
    }

    if (viz === 'shots') {
      const res = await getJSON('shots', { url, team });
      const shots = {
        x: res.shots.map(d => d.x),
        y: res.shots.map(d => d.y),
        mode: 'markers',
        type: 'scatter',
        name: 'Shots',
        marker: { size: res.shots.map(d => Math.max(6, (d.xG || 0.07)*60)), color:'#e5e7eb', line:{color:'#666', width:1} }
      };
      const goals = {
        x: res.goals.map(d => d.x),
        y: res.goals.map(d => d.y),
        mode: 'markers',
        type: 'scatter',
        name: 'Goals',
        marker: { size: res.goals.map(d => Math.max(8, (d.xG || 0.2)*60)), color:'#ef4444', line:{color:'#000', width:1} }
      };
      Plotly.newPlot('plot', [shots, goals], pitchLayout({ title: `Shots & Goals – ${team}` }), {displayModeBar:false});
      return;
    }
  } catch (e) {
    console.error(e);
    alert('Error: ' + e.message);
  }
}

$('go').addEventListener('click', render);
