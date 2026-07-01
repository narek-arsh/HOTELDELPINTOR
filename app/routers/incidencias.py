<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#9E312C">
<title>Hotel del Pintor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
:root {
  --red: #9E312C; --red-dark: #7A241F; --red-bg: #F6E6E5;
  --ink: #222222; --slate: #5A5A5A; --border: #E5E5E5;
  --bg: #F7F7F8; --surface: #fff; --r: 3px; --r2: 4px;
}
body { font-family: 'Manrope', -apple-system, sans-serif; background: var(--bg); color: var(--ink); min-height: 100vh; }

.header { background: var(--red); padding: 20px 20px 24px; text-align: center; }
.header img { width: 70px; height: 70px; object-fit: contain; margin-bottom: 10px; border-radius: 50%; background: #fff; padding: 6px; }
.header h1 { color: #fff; font-size: 16px; font-weight: 700; }
.header p { color: rgba(255,255,255,0.75); font-size: 12px; margin-top: 3px; }

.lang-bar { background: var(--red-dark); display: flex; justify-content: center; gap: 6px; padding: 8px; }
.lang-btn { background: none; border: 1px solid rgba(255,255,255,0.3); border-radius: 3px; color: rgba(255,255,255,0.7); font-size: 11px; font-weight: 700; padding: 4px 12px; cursor: pointer; font-family: inherit; }
.lang-btn.active { background: #fff; color: var(--red); border-color: #fff; }

.content { max-width: 480px; margin: 0 auto; padding: 24px 16px; }

.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r2); padding: 16px; margin-bottom: 12px; cursor: pointer; transition: border-color 0.15s; }
.card:active { opacity: 0.85; }
.card.sel { border-color: var(--red); background: var(--red-bg); }
.card-icon { font-size: 28px; margin-bottom: 8px; }
.card-title { font-size: 15px; font-weight: 700; color: var(--ink); margin-bottom: 3px; }
.card-desc { font-size: 12px; color: var(--slate); }

.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 10px; font-weight: 700; color: var(--slate); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 5px; }
.field input, .field textarea, .field select {
  width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--r);
  font-size: 14px; font-family: inherit; color: var(--ink); background: var(--surface); outline: none; -webkit-appearance: none;
}
.field input:focus, .field textarea:focus { border-color: var(--red); }
.field textarea { resize: none; line-height: 1.5; }

.type-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.type-btn { padding: 12px 10px; border-radius: var(--r); border: 1px solid var(--border); background: var(--surface); cursor: pointer; font-size: 12px; font-weight: 500; color: var(--slate); text-align: left; line-height: 1.3; font-family: inherit; }
.type-btn.sel { border-color: var(--red); background: var(--red-bg); color: var(--red); font-weight: 700; }

.btn { display: block; width: 100%; padding: 13px; border: none; border-radius: var(--r); font-size: 14px; font-weight: 700; cursor: pointer; font-family: inherit; }
.btn-primary { background: var(--red); color: #fff; }
.btn-primary:active { opacity: 0.85; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-secondary { background: var(--surface); border: 1px solid var(--border); color: var(--slate); margin-top: 8px; }

.err { color: var(--red); font-size: 12px; margin-top: 6px; }
.step { display: none; }
.step.active { display: block; }

.success { text-align: center; padding: 40px 20px; }
.success-icon { font-size: 52px; margin-bottom: 16px; }
.success h2 { font-size: 20px; font-weight: 700; color: var(--ink); margin-bottom: 8px; }
.success p { color: var(--slate); font-size: 14px; line-height: 1.5; }
.success .codigo { margin-top: 20px; background: var(--red-bg); border-radius: var(--r2); padding: 12px 16px; display: inline-block; }
.success .codigo span { font-size: 18px; font-weight: 700; color: var(--red); letter-spacing: 1px; }

.section-label { font-size: 10px; font-weight: 700; color: var(--slate); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px; display: block; }
.opt-label { font-size: 11px; color: var(--slate); margin-top: 6px; }

.foto-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px; }
.foto-thumb { position: relative; aspect-ratio: 1; border-radius: var(--r2); overflow: hidden; border: 1px solid var(--border); }
.foto-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.foto-thumb .foto-del { position: absolute; top: 3px; right: 3px; width: 20px; height: 20px; border-radius: 50%; background: rgba(0,0,0,0.6); color: #fff; border: none; font-size: 13px; font-weight: 700; cursor: pointer; line-height: 1; }
.foto-grid:empty { margin-bottom: 0; display: none; }
</style>
</head>
<body>

<div class="header">
  <img src="/logo-login.png" alt="Hotel del Pintor">
  <h1 id="h-title">Hotel del Pintor</h1>
  <p id="h-subtitle">¿Cómo podemos ayudarte?</p>
</div>

<div class="lang-bar">
  <button class="lang-btn active" onclick="setLang('es')">🇪🇸 ES</button>
  <button class="lang-btn" onclick="setLang('en')">🇬🇧 EN</button>
</div>

<div class="content">

  <!-- STEP 1: Tipo de solicitud -->
  <div id="step1" class="step active">
    <span class="section-label" id="lbl-tipo-solicitud">¿Qué necesitas?</span>
    <div class="card" id="card-mant" onclick="selSolicitud('mantenimiento')">
      <div class="card-icon">🔧</div>
      <div class="card-title" id="lbl-mant-title">Algo no funciona</div>
      <div class="card-desc" id="lbl-mant-desc">Avería, rotura o problema técnico en la habitación</div>
    </div>
    <div class="card" id="card-limp" onclick="selSolicitud('limpieza')">
      <div class="card-icon">🧹</div>
      <div class="card-title" id="lbl-limp-title">Limpieza o reposición</div>
      <div class="card-desc" id="lbl-limp-desc">Toallas, amenities, cambio de ropa de cama u otras necesidades</div>
    </div>
  </div>

  <!-- STEP 2a: Detalles mantenimiento -->
  <div id="step2-mant" class="step">
    <span class="section-label" id="lbl-tipo-averia">¿Qué tipo de avería?</span>
    <div class="type-grid" id="tipo-grid"></div>
    <div id="otro-box" style="display:none;margin-top:10px">
      <div class="field">
        <label class="field-label" id="lbl-desc-obligatoria">Descripción *</label>
        <textarea id="f-desc-mant" rows="3" placeholder=""></textarea>
      </div>
    </div>
    <div class="field" style="margin-top:14px">
      <label class="field-label" id="lbl-notas-mant">Notas adicionales</label>
      <textarea id="f-notas-mant" rows="2" placeholder=""></textarea>
    </div>
    <div class="field">
      <label class="field-label" id="lbl-nombre">Tu nombre <span class="opt-label" id="lbl-opcional">(opcional)</span></label>
      <input type="text" id="f-nombre-mant" placeholder="">
    </div>
    <div class="field">
      <label class="field-label" id="lbl-fotos-mant">Fotos <span class="opt-label">(opcional, máx. 3)</span></label>
      <input type="file" id="f-fotos-mant" accept="image/*" capture="environment" multiple style="display:none" onchange="onFotosSel(event,'mant')">
      <div class="foto-grid" id="fotos-grid-mant"></div>
      <button type="button" class="btn btn-secondary" style="margin-top:0" onclick="document.getElementById('f-fotos-mant').click()" id="btn-add-foto-mant">+ Añadir foto</button>
    </div>
    <div id="err-mant" class="err" style="display:none"></div>
    <button type="button" class="btn btn-primary" id="btn-send-mant" onclick="enviarMant()"></button>
    <button type="button" class="btn btn-secondary" onclick="goBack()"></button>
  </div>

  <!-- STEP 2b: Detalles limpieza -->
  <div id="step2-limp" class="step">
    <span class="section-label" id="lbl-que-necesitas">¿Qué necesitas exactamente?</span>
    <div class="field">
      <textarea id="f-desc-limp" rows="4" placeholder=""></textarea>
    </div>
    <div class="field">
      <label class="field-label" id="lbl-nombre-limp">Tu nombre <span class="opt-label">(opcional)</span></label>
      <input type="text" id="f-nombre-limp" placeholder="">
    </div>
    <div class="field">
      <label class="field-label">Fotos <span class="opt-label">(opcional, máx. 3)</span></label>
      <input type="file" id="f-fotos-limp" accept="image/*" capture="environment" multiple style="display:none" onchange="onFotosSel(event,'limp')">
      <div class="foto-grid" id="fotos-grid-limp"></div>
      <button type="button" class="btn btn-secondary" style="margin-top:0" onclick="document.getElementById('f-fotos-limp').click()" id="btn-add-foto-limp">+ Añadir foto</button>
    </div>
    <div id="err-limp" class="err" style="display:none"></div>
    <button type="button" class="btn btn-primary" id="btn-send-limp" onclick="enviarLimp()"></button>
    <button type="button" class="btn btn-secondary" onclick="goBack()"></button>
  </div>

  <!-- STEP 3: Confirmación -->
  <div id="step3" class="step">
    <div class="success">
      <div class="success-icon">✓</div>
      <h2 id="lbl-enviado">¡Solicitud enviada!</h2>
      <p id="lbl-enviado-desc">Nos pondremos en contacto lo antes posible.</p>
      <div class="codigo" id="codigo-box" style="display:none">
        <div style="font-size:11px;color:var(--slate);margin-bottom:4px" id="lbl-tu-codigo">Tu código de referencia</div>
        <span id="codigo-valor"></span>
      </div>
      <button type="button" class="btn btn-secondary" onclick="resetForm()" style="margin-top:24px;max-width:200px;margin-left:auto;margin-right:auto" id="btn-nueva"></button>
    </div>
  </div>

</div>

<script>
const API = "https://hoteldelpintor-production.up.railway.app";
const token = location.pathname.split('/h/')[1]?.split('/')[0];
let habitacion = null;
let tipoSolSel = null;
let tipoMantSel = null;
let lang = 'es';
let fotosMant = [];
let fotosLimp = [];

const T = {
  es: {
    subtitle: "¿Cómo podemos ayudarte?",
    tipo_solicitud: "¿Qué necesitas?",
    mant_title: "Algo no funciona",
    mant_desc: "Avería, rotura o problema técnico en la habitación",
    limp_title: "Limpieza o reposición",
    limp_desc: "Toallas, amenities, cambio de ropa de cama u otras necesidades",
    tipo_averia: "¿Qué tipo de avería?",
    desc_obligatoria: "Descripción *",
    desc_placeholder: "Describe el problema con detalle...",
    notas_mant: "Notas adicionales",
    notas_placeholder: "Cualquier detalle relevante...",
    nombre: "Tu nombre",
    opcional: "(opcional)",
    nombre_placeholder: "Ej: Juan García",
    enviar: "Enviar solicitud",
    volver: "Volver",
    enviado: "¡Solicitud enviada!",
    enviado_desc: "Nos pondremos en contacto lo antes posible. Gracias por avisarnos.",
    tu_codigo: "Tu código de referencia",
    nueva: "Nueva solicitud",
    err_tipo: "Por favor selecciona el tipo de avería.",
    err_desc: "Por favor describe el problema.",
    err_conexion: "Error de conexión. Inténtalo de nuevo.",
    que_necesitas: "¿Qué necesitas exactamente?",
    limp_placeholder: "Ej: Toallas limpias, jabón, cambio de sábanas...",
    tipos: {
      bombilla: "💡 Bombilla fundida",
      puerta: "🚪 Puerta / cerradura",
      fontaneria: "🚿 Fontanería",
      calefaccion: "❄️ Clima / Calefacción",
      mueble: "🪑 Mobiliario",
      otro: "❓ Otro",
    }
  },
  en: {
    subtitle: "How can we help you?",
    tipo_solicitud: "What do you need?",
    mant_title: "Something's not working",
    mant_desc: "Breakdown, damage or technical issue in your room",
    limp_title: "Cleaning or supplies",
    limp_desc: "Towels, amenities, bed linen change or other needs",
    tipo_averia: "What type of issue?",
    desc_obligatoria: "Description *",
    desc_placeholder: "Describe the problem in detail...",
    notas_mant: "Additional notes",
    notas_placeholder: "Any other relevant details...",
    nombre: "Your name",
    opcional: "(optional)",
    nombre_placeholder: "e.g. John Smith",
    enviar: "Send request",
    volver: "Back",
    enviado: "Request sent!",
    enviado_desc: "We will attend to your request as soon as possible. Thank you for letting us know.",
    tu_codigo: "Your reference code",
    nueva: "New request",
    err_tipo: "Please select the type of issue.",
    err_desc: "Please describe the problem.",
    err_conexion: "Connection error. Please try again.",
    que_necesitas: "What exactly do you need?",
    limp_placeholder: "e.g. Clean towels, soap, bed linen change...",
    tipos: {
      bombilla: "💡 Burnt bulb",
      puerta: "🚪 Door / lock",
      fontaneria: "🚿 Plumbing",
      calefaccion: "❄️ A/C / Heating",
      mueble: "🪑 Furniture",
      otro: "❓ Other",
    }
  }
};

function onFotosSel(e, tipo) {
  const arr = tipo === 'mant' ? fotosMant : fotosLimp;
  for (const f of e.target.files) { if (arr.length < 3) arr.push(f); }
  e.target.value = '';
  renderFotosGridHuesped(tipo);
}

function quitarFoto(tipo, idx) {
  const arr = tipo === 'mant' ? fotosMant : fotosLimp;
  arr.splice(idx, 1);
  renderFotosGridHuesped(tipo);
}

function renderFotosGridHuesped(tipo) {
  const arr = tipo === 'mant' ? fotosMant : fotosLimp;
  const grid = document.getElementById(tipo === 'mant' ? 'fotos-grid-mant' : 'fotos-grid-limp');
  const btn = document.getElementById(tipo === 'mant' ? 'btn-add-foto-mant' : 'btn-add-foto-limp');
  grid.innerHTML = arr.map((f, i) => {
    const url = URL.createObjectURL(f);
    return `<div class="foto-thumb"><img src="${url}"><button type="button" class="foto-del" onclick="quitarFoto('${tipo}',${i})">×</button></div>`;
  }).join('');
  if (btn) btn.style.display = arr.length >= 3 ? 'none' : 'block';
}

async function subirFotosHuesped(incidenciaId, fotos) {
  for (const f of fotos) {
    try {
      const fd = new FormData();
      fd.append('file', f);
      await fetch(`${API}/h/${token}/fotos/${incidenciaId}`, { method: 'POST', body: fd });
    } catch {}
  }
}

function t(key) { return T[lang][key] || key; }

function setLang(l) {
  lang = l;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  applyTranslations();
}

function applyTranslations() {
  document.getElementById('h-subtitle').textContent = t('subtitle');
  document.getElementById('lbl-tipo-solicitud').textContent = t('tipo_solicitud');
  document.getElementById('lbl-mant-title').textContent = t('mant_title');
  document.getElementById('lbl-mant-desc').textContent = t('mant_desc');
  document.getElementById('lbl-limp-title').textContent = t('limp_title');
  document.getElementById('lbl-limp-desc').textContent = t('limp_desc');
  document.getElementById('lbl-tipo-averia').textContent = t('tipo_averia');
  document.getElementById('lbl-desc-obligatoria').textContent = t('desc_obligatoria');
  document.getElementById('f-desc-mant').placeholder = t('desc_placeholder');
  document.getElementById('lbl-notas-mant').childNodes[0].textContent = t('notas_mant') + ' ';
  document.getElementById('f-notas-mant').placeholder = t('notas_placeholder');
  document.getElementById('lbl-nombre').childNodes[0].textContent = t('nombre') + ' ';
  document.getElementById('lbl-opcional').textContent = t('opcional');
  document.getElementById('f-nombre-mant').placeholder = t('nombre_placeholder');
  document.getElementById('btn-send-mant').textContent = t('enviar');
  document.getElementById('btn-send-limp').textContent = t('enviar');
  document.getElementById('lbl-que-necesitas').textContent = t('que_necesitas');
  document.getElementById('f-desc-limp').placeholder = t('limp_placeholder');
  document.getElementById('lbl-nombre-limp').childNodes[0].textContent = t('nombre') + ' ';
  document.getElementById('f-nombre-limp').placeholder = t('nombre_placeholder');
  document.getElementById('lbl-enviado').textContent = t('enviado');
  document.getElementById('lbl-enviado-desc').textContent = t('enviado_desc');
  document.getElementById('lbl-tu-codigo').textContent = t('tu_codigo');
  document.getElementById('btn-nueva').textContent = t('nueva');

  // Rebuild tipo grid with new language
  if (tipoSolSel === 'mantenimiento') buildTipoGrid();
  // Back buttons
  document.querySelectorAll('.btn-secondary[onclick="goBack()"]').forEach(b => b.textContent = t('volver'));
}

function buildTipoGrid() {
  const tipos = ['bombilla','puerta','fontaneria','calefaccion','mueble','otro'];
  document.getElementById('tipo-grid').innerHTML = tipos.map(tp =>
    `<button type="button" class="type-btn ${tipoMantSel===tp?'sel':''}" onclick="selTipoMant('${tp}')">${t('tipos')[tp]}</button>`
  ).join('');
}

function showStep(id) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function selSolicitud(tipo) {
  tipoSolSel = tipo;
  document.getElementById('card-mant').classList.toggle('sel', tipo === 'mantenimiento');
  document.getElementById('card-limp').classList.toggle('sel', tipo === 'limpieza');
  if (tipo === 'mantenimiento') {
    buildTipoGrid();
    showStep('step2-mant');
  } else {
    showStep('step2-limp');
  }
}

function selTipoMant(tp) {
  tipoMantSel = tp;
  document.getElementById('otro-box').style.display = tp === 'otro' ? 'block' : 'none';
  buildTipoGrid();
}

function goBack() {
  tipoMantSel = null;
  document.getElementById('card-mant').classList.remove('sel');
  document.getElementById('card-limp').classList.remove('sel');
  showStep('step1');
}

async function enviarMant() {
  const err = document.getElementById('err-mant');
  err.style.display = 'none';
  if (!tipoMantSel) { err.textContent = t('err_tipo'); err.style.display = 'block'; return; }
  const desc = document.getElementById('f-desc-mant').value.trim();
  if (tipoMantSel === 'otro' && !desc) { err.textContent = t('err_desc'); err.style.display = 'block'; return; }
  const notas = document.getElementById('f-notas-mant').value.trim();
  const nombre = document.getElementById('f-nombre-mant').value.trim();
  const btn = document.getElementById('btn-send-mant');
  btn.disabled = true;
  try {
    const r = await fetch(`${API}/h/${token}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        tipo_solicitud: 'mantenimiento',
        tipo: tipoMantSel,
        descripcion: tipoMantSel === 'otro' ? desc : (notas || null),
        nombre_huesped: nombre || null,
        idioma: lang,
      })
    });
    const d = await r.json();
    if (!r.ok) { err.textContent = d.detail || t('err_conexion'); err.style.display = 'block'; return; }
    if (fotosMant.length) await subirFotosHuesped(d.id, fotosMant);
    mostrarExito(d.codigo);
  } catch { err.textContent = t('err_conexion'); err.style.display = 'block'; }
  finally { btn.disabled = false; }
}

async function enviarLimp() {
  const err = document.getElementById('err-limp');
  err.style.display = 'none';
  const desc = document.getElementById('f-desc-limp').value.trim();
  const nombre = document.getElementById('f-nombre-limp').value.trim();
  const btn = document.getElementById('btn-send-limp');
  btn.disabled = true;
  try {
    const r = await fetch(`${API}/h/${token}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        tipo_solicitud: 'limpieza',
        descripcion: desc || null,
        nombre_huesped: nombre || null,
        idioma: lang,
      })
    });
    const d = await r.json();
    if (!r.ok) { err.textContent = d.detail || t('err_conexion'); err.style.display = 'block'; return; }
    if (fotosLimp.length) await subirFotosHuesped(d.id, fotosLimp);
    mostrarExito(d.codigo);
  } catch { err.textContent = t('err_conexion'); err.style.display = 'block'; }
  finally { btn.disabled = false; }
}

function mostrarExito(codigo) {
  document.getElementById('codigo-valor').textContent = codigo;
  document.getElementById('codigo-box').style.display = 'inline-block';
  showStep('step3');
}

function resetForm() {
  tipoSolSel = null; tipoMantSel = null;
  ['f-desc-mant','f-notas-mant','f-nombre-mant','f-desc-limp','f-nombre-limp'].forEach(id => {
    document.getElementById(id).value = '';
  });
  fotosMant = []; fotosLimp = [];
  renderFotosGridHuesped('mant'); renderFotosGridHuesped('limp');
  document.getElementById('otro-box').style.display = 'none';
  showStep('step1');
}

// Init
window.addEventListener('load', async () => {
  applyTranslations();
  try {
    const r = await fetch(`${API}/h/${token}/info`);
    if (r.ok) {
      const d = await r.json();
      habitacion = d.habitacion;
      document.getElementById('h-title').textContent = `Hotel del Pintor · Hab. ${habitacion}`;
    }
  } catch {}
});
</script>
</body>
</html>
