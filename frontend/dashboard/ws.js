// Socket.IO client — connects to Flask/copiloto_server on :5000
const socket = io(window.location.origin, {
  reconnectionDelay: 1000,
  reconnectionDelayMax: 10000,
  reconnectionAttempts: Infinity,
});

socket.on('connect', () => {
  console.log('[WS] Conectado al copiloto_server');
});

socket.on('disconnect', (reason) => {
  console.warn('[WS] Desconectado:', reason);
});

socket.on('connect_error', (err) => {
  console.error('[WS] Error de conexión:', err.message);
});

// FPS update
socket.on('fps_update', (data) => {
  console.log('[WS] fps_update', data);
  const el = document.getElementById('stat-fps');
  if (el) el.textContent = data.fps ?? data;
});

// Latencia E2E
socket.on('latency_update', (data) => {
  console.log('[WS] latency_update', data);
  const el = document.getElementById('stat-lat');
  if (el) el.textContent = data.latency ?? data;
});

// Detección: stat + overlay
socket.on('detection', (data) => {
  console.log('[WS] detection', data);
  const statEl = document.getElementById('stat-det');
  const overlayEl = document.getElementById('cam-det-overlay');
  const count = data.count ?? data;
  if (statEl) statEl.textContent = count;
  if (overlayEl) overlayEl.textContent = `Det: ${count}`;
});

// Placa detectada: ROI, confianza, historial
socket.on('plate_detected', (data) => {
  console.log('[WS] plate_detected', data);
  const plate = data.plate ?? data.text ?? '---';
  const conf  = data.confidence ?? data.conf ?? 0;
  const time  = new Date().toTimeString().slice(0, 5);

  const plateEl = document.getElementById('roi-plate-text');
  const confEl  = document.getElementById('roi-conf');
  const histEl  = document.getElementById('hist-list');

  if (plateEl) plateEl.textContent = plate;
  if (confEl)  confEl.textContent  = `conf: ${(conf * 100).toFixed(1)}%`;

  if (histEl) {
    const li = document.createElement('li');
    li.innerHTML =
      `<span class="plate-tag">${plate}</span>` +
      `<span class="conf-tag">${time} · ${(conf * 100).toFixed(1)}%</span>`;
    histEl.prepend(li);
    // Keep at most 50 entries
    while (histEl.children.length > 50) {
      histEl.removeChild(histEl.lastChild);
    }
  }
});

// LLM result
socket.on('llm_result', (data) => {
  console.log('[WS] llm_result', data);
  const el = document.getElementById('llm-box');
  if (el) el.value = data.text ?? data;
});

// Node status — updates nav dots
socket.on('node_status', (data) => {
  console.log('[WS] node_status', data);
  // data expected: { pi5: true/false, server: true/false, pi4: true/false }
  const map = {
    pi5:    'dot-pi5',
    server: 'dot-server',
    pi4:    'dot-pi4',
  };
  Object.entries(map).forEach(([key, id]) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (data[key]) {
      el.classList.add('up');
    } else {
      el.classList.remove('up');
    }
  });
});

// Stream Pi5 — reconexión automática
(function () {
  const img     = document.getElementById('cam-stream');
  const overlay = document.getElementById('stream-reconnect-overlay');
  if (!img || !overlay) return;

  img.onerror = () => {
    overlay.style.display = 'flex';
    setTimeout(() => {
      const base = img.src.split('?')[0];
      img.src = base + '?t=' + Date.now();
    }, 3000);
  };
  img.onload = () => { overlay.style.display = 'none'; };
})();

// OCR rate
socket.on('ocr_rate', (data) => {
  console.log('[WS] ocr_rate', data);
  const rate  = data.rate ?? data;
  const pct   = Math.min(100, Math.max(0, rate * 100));
  const statEl = document.getElementById('stat-ocr');
  const tasaEl = document.getElementById('tasa-val');
  const barEl  = document.getElementById('tasa-bar');
  if (statEl) statEl.textContent = `${pct.toFixed(1)}%`;
  if (tasaEl) tasaEl.textContent = `${pct.toFixed(1)}%`;
  if (barEl)  barEl.style.width  = `${pct}%`;
});
