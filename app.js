const el = (id) => document.getElementById(id);

async function getJSON(path, params) {
  const q = new URLSearchParams(params).toString();
  const resp = await fetch(`/api/${path}?${q}`);
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

function drawPitch(layout = {}) {
  // Simple pitch rectangle (0..100 scale like WS)
  return {
    xaxis: {
      range: [0, 100],
      showgrid: false, zeroline: false, visible: false
    },
    yaxis: {
      range: [0, 100],
      showgrid: false, zeroline: false, visible: false, scaleanchor: "x", scaleratio: 1
    },
    paper_bgcolor: "#0f1115",
    plot_bgcolor: "#0f1115",
    margin: { l: 20, r: 20, t: 30, b: 20 },
    ...layout
  };
}

function toMarker(name, x, y, size=14, label) {
  return {
    x: [x], y: [y], mode: "markers+text",
    marker: { size: size, color: "#3b82f6", line: { color: "white", width: 2 } },
    text: [label || name], textposition: "top center",
    hovertemplate: `${name}<extra></extra>`
  };
}

function lineTrace(xs, ys, width=2, color="#e5e7eb", text) {
  return {
    x: xs, y: ys, mode: "lines",
    line: { width: width, color: color },
    hovertemplate: (text ? `${text}<extra></extra>` : "<extra></extra>")
  };
}

async function render() {
  const url = el("url").value.trim();
  const team = el("team").value.trim();
  const viz = el("viz").value;

  if (!url || !team) {
    alert("Please provide match URL and Team");
    return;
  }

  try {
    if (viz === "pass-network") {
      const data = await getJSON("pass-network", { url, team });
      const traces = [];
      // links
      for (const l of data.links) {
        const n1 = data.nodes.find(n => n.playerId === l.source);
        const n2 = data.nodes.find(n => n.playerId === l.target);
        if (!n1 || !n2) continue;
        traces.push(lineTrace([n1.x, n2.x], [n1.y, n2.y], Math.max(1, Math.min(8, l.count/2))));
      }
      // nodes
      for (const n of data.nodes) {
        traces.push(toMarker(n.name, n.x, n.y, 16, n.shirtNo || ""));
      }
      Plotly.newPlot("plot", traces, drawPitch({ title: "Pass Network" }), {displayModeBar:false});
    }

    if (viz === "box-passes") {
      const meta = await getJSON("match", { url });
      const who = (meta.home === team) ? meta.home : meta.away;
      if (!who) throw new Error("Team name not found in match meta.");

      const res = await getJSON("box-passes", { url, team });
      const lines = [];
      for (const p of res.passes) {
        lines.push(lineTrace([p.x, p.endX], [p.y, p.endY], 2, "#22c55e"));
      }
      Plotly.newPlot("plot", lines, drawPitch({ title: "Successful Box Passes" }), {displayModeBar:false});
    }

    if (viz === "shots") {
      const res = await getJSON("shots", { url, team });
      const goals = {
        x: res.goals.map(d => d.x),
        y: res.goals.map(d => d.y),
        mode: "markers",
        marker: { size: res.goals.map(d => Math.max(8, d.xG*60)), color: "#ef4444", line:{color:"black",width:1} },
        name: "Goals", type: "scatter"
      };
      const shots = {
        x: res.shots.map(d => d.x),
        y: res.shots.map(d => d.y),
        mode: "markers",
        marker: { size: res.shots.map(d => Math.max(6, d.xG*60)), color: "#e5e7eb", line:{color:"gray",width:1} },
        name: "Shots", type: "scatter"
      };
      Plotly.newPlot("plot", [shots, goals], drawPitch({ title: "Shots & Goals" }), {displayModeBar:false});
    }
  } catch (e) {
    console.error(e);
    alert("Error: " + e.message);
  }
}

document.getElementById("go").addEventListener("click", render);
