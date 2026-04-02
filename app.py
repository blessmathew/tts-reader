
"""
Edge TTS Reader — Single File (Chunked Streaming)
===================================================
Install:  pip install edge-tts flask
Run:      python tts_reader.py
Browser:  http://localhost:5050
Phone:    http://192.168.1.34:5050  (same Wi-Fi)
"""
 
import asyncio, io, re
from flask import Flask, request, jsonify, Response
 
app = Flask(__name__)
 
VOICES = [
    {"id": "en-US-AriaNeural",    "label": "Aria (US Female)"},
    {"id": "en-US-GuyNeural",     "label": "Guy (US Male)"},
    {"id": "en-US-JennyNeural",   "label": "Jenny (US Female)"},
    {"id": "en-GB-SoniaNeural",   "label": "Sonia (UK Female)"},
    {"id": "en-GB-RyanNeural",    "label": "Ryan (UK Male)"},
    {"id": "en-AU-NatashaNeural", "label": "Natasha (AU Female)"},
    {"id": "en-IN-NeerjaNeural",  "label": "Neerja (IN Female)"},
    {"id": "en-AU-WilliamMultilingualNeural", "label": "William (AU Male)"},
]
 
def split_chunks(text, max_chars=220):
    """Split text into sentence-aware chunks."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 <= max_chars:
            cur = (cur + " " + s).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks or [text]
 
async def tts_chunk(text, voice, rate, pitch):
    import edge_tts
    communicate = edge_tts.Communicate(
        text, voice,
        rate  = f"{rate:+d}%",
        pitch = f"{pitch:+d}Hz",
    )
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf.read()
 
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Edge TTS Reader</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg:      #0e0e11;
    --surface: #17171c;
    --border:  #2a2a35;
    --accent:  #c8f060;
    --accent2: #60e0f0;
    --muted:   #6b6b80;
    --text:    #e8e8f0;
    --danger:  #f06060;
    --r:       14px;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg); color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100dvh; display: flex; flex-direction: column;
    align-items: center; padding: 24px 16px 56px;
  }
  header {
    width: 100%; max-width: 720px;
    display: flex; align-items: baseline; gap: 12px; margin-bottom: 32px;
  }
  header h1 { font-size: clamp(1.7rem,5vw,2.5rem); font-weight: 800; letter-spacing: -.03em; }
  header h1 span { color: var(--accent); }
  .badge {
    margin-left: auto; font-family: 'DM Mono', monospace; font-size: .68rem;
    color: var(--muted); border: 1px solid var(--border);
    padding: 3px 9px; border-radius: 999px; white-space: nowrap;
  }
  .card {
    width: 100%; max-width: 720px; background: var(--surface);
    border: 1px solid var(--border); border-radius: var(--r);
    padding: 20px; margin-bottom: 14px;
  }
  .lbl {
    font-family: 'DM Mono', monospace; font-size: .67rem;
    text-transform: uppercase; letter-spacing: .12em;
    color: var(--muted); margin-bottom: 10px;
  }
  textarea {
    width: 100%; min-height: 190px; resize: vertical;
    background: var(--bg); color: var(--text);
    border: 1px solid var(--border); border-radius: 10px;
    padding: 14px; font-family: 'DM Mono', monospace;
    font-size: .9rem; line-height: 1.65; outline: none; transition: border-color .2s;
  }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--muted); }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media (max-width: 480px) { .grid { grid-template-columns: 1fr; } }
  select {
    width: 100%; background: var(--bg); color: var(--text);
    border: 1px solid var(--border); border-radius: 10px;
    padding: 11px 14px; font-family: 'Syne', sans-serif; font-size: .88rem;
    outline: none; cursor: pointer; appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' fill='none'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236b6b80' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 14px center; transition: border-color .2s;
  }
  select:focus { border-color: var(--accent2); }
  .sw { display: flex; flex-direction: column; gap: 6px; }
  .sr { display: flex; justify-content: space-between; align-items: center; }
  .sv { font-family: 'DM Mono', monospace; font-size: .78rem; color: var(--accent); min-width: 54px; text-align: right; }
  input[type=range] { width: 100%; accent-color: var(--accent); cursor: pointer; }
  .btn {
    width: 100%; max-width: 720px; padding: 16px; margin-bottom: 14px;
    background: var(--accent); color: #0e0e11;
    font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700;
    letter-spacing: .04em; border: none; border-radius: var(--r);
    cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px;
    transition: opacity .2s, transform .1s;
  }
  .btn:active { transform: scale(.98); }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn-stop {
    width: 100%; max-width: 720px; padding: 12px; margin-bottom: 14px;
    background: transparent; color: var(--danger);
    font-family: 'Syne', sans-serif; font-size: .9rem; font-weight: 600;
    border: 1px solid var(--danger); border-radius: var(--r);
    cursor: pointer; display: none; align-items: center; justify-content: center; gap: 8px;
    transition: background .2s;
  }
  .btn-stop.on { display: flex; }
  .btn-stop:hover { background: #f0606015; }
  #progress-wrap { width: 100%; max-width: 720px; margin-bottom: 14px; display: none; }
  #progress-wrap.on { display: block; }
  .prog-top { display: flex; justify-content: space-between; margin-bottom: 6px; }
  .prog-label { font-family: 'DM Mono', monospace; font-size: .72rem; color: var(--muted); }
  .prog-count { font-family: 'DM Mono', monospace; font-size: .72rem; color: var(--accent); }
  .prog-bar-bg { width: 100%; height: 4px; background: var(--border); border-radius: 99px; overflow: hidden; }
  .prog-bar { height: 100%; background: var(--accent); border-radius: 99px; width: 0%; transition: width .4s ease; }
  #status {
    width: 100%; max-width: 720px; text-align: center;
    font-family: 'DM Mono', monospace; font-size: .75rem;
    color: var(--muted); min-height: 18px; margin-bottom: 6px;
  }
  #status.err { color: var(--danger); }
  #player-card { display: none; }
  #player-card.on { display: block; }
  audio { width: 100%; border-radius: 8px; outline: none; }
  .pb-row { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
  .pb-lbl { font-family: 'DM Mono', monospace; font-size: .73rem; color: var(--muted); white-space: nowrap; }
  .pb-val { font-family: 'DM Mono', monospace; font-size: .76rem; color: var(--accent2); min-width: 36px; }
  #pb-speed { flex: 1; accent-color: var(--accent2); }
  .dl-row { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
  .btn-dl {
    flex: 1; padding: 11px 16px;
    background: transparent; color: var(--accent2);
    font-family: 'Syne', sans-serif; font-size: .88rem; font-weight: 600;
    border: 1px solid var(--accent2); border-radius: 10px;
    cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
    transition: background .2s, opacity .2s;
  }
  .btn-dl:hover { background: #60e0f015; }
  .btn-dl:disabled { opacity: .35; cursor: not-allowed; }
  .dl-hint { font-family: 'DM Mono', monospace; font-size: .68rem; color: var(--muted); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .pulsing { animation: pulse 1.2s ease-in-out infinite; }
</style>
</head>
<body>
 
<header>
  <h1>Edge <span>TTS</span> Reader</h1>
  <span class="badge">localhost · streaming</span>
</header>
 
<div class="card">
  <div class="lbl">Paste your text</div>
  <textarea id="text" placeholder="Paste or type anything here — long articles work great now!"></textarea>
</div>
 
<div class="card">
  <div class="lbl">Voice &amp; Controls</div>
  <div class="grid">
    <div>
      <div class="lbl" style="margin-bottom:8px">Voice</div>
      <select id="voice"></select>
    </div>
    <div class="sw">
      <div class="lbl">Generation Rate</div>
      <div class="sr">
        <span style="font-size:.72rem;color:var(--muted)">Slower</span>
        <span class="sv" id="rate-val">+0%</span>
        <span style="font-size:.72rem;color:var(--muted)">Faster</span>
      </div>
      <input type="range" id="rate" min="-50" max="100" value="0" step="5"/>
    </div>
    <div class="sw" style="grid-column:1/-1">
      <div class="lbl">Pitch</div>
      <div class="sr">
        <span style="font-size:.72rem;color:var(--muted)">Lower</span>
        <span class="sv" id="pitch-val">+0 Hz</span>
        <span style="font-size:.72rem;color:var(--muted)">Higher</span>
      </div>
      <input type="range" id="pitch" min="-50" max="50" value="0" step="5"/>
    </div>
  </div>
</div>
 
<div id="status"></div>
 
<div id="progress-wrap">
  <div class="prog-top">
    <span class="prog-label pulsing" id="prog-label">Generating…</span>
    <span class="prog-count" id="prog-count"></span>
  </div>
  <div class="prog-bar-bg"><div class="prog-bar" id="prog-bar"></div></div>
</div>
 
<button class="btn" id="speak-btn" onclick="speak()">
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="5 3 19 12 5 21 5 3"/>
  </svg>
  Speak
</button>
 
<button class="btn-stop" id="stop-btn" onclick="stopAll()">&#9632; Stop</button>
 
<div class="card" id="player-card">
  <div class="lbl">Now Playing</div>
  <audio id="audio" controls></audio>
  <div class="pb-row">
    <span class="pb-lbl">Playback speed</span>
    <input type="range" id="pb-speed" min="0.5" max="3" value="1" step="0.25"/>
    <span class="pb-val" id="pb-val">1×</span>
  </div>
  <div class="dl-row">
    <button class="btn-dl" id="dl-btn" onclick="downloadAudio()" disabled>
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Download MP3
    </button>
    <span class="dl-hint" id="dl-hint">Available when all chunks are ready</span>
  </div>
</div>
 
<script>
  fetch("/voices").then(r=>r.json()).then(vs=>{
    const sel=document.getElementById("voice");
    vs.forEach(v=>{ const o=document.createElement("option"); o.value=v.id; o.textContent=v.label; sel.appendChild(o); });
  });
 
  document.getElementById("rate").addEventListener("input",e=>{
    const v=+e.target.value; document.getElementById("rate-val").textContent=(v>=0?"+":"")+v+"%";
  });
  document.getElementById("pitch").addEventListener("input",e=>{
    const v=+e.target.value; document.getElementById("pitch-val").textContent=(v>=0?"+":"")+v+" Hz";
  });
 
  const audio=document.getElementById("audio");
  document.getElementById("pb-speed").addEventListener("input",e=>{
    const v=parseFloat(e.target.value);
    audio.playbackRate=v;
    document.getElementById("pb-val").textContent=v.toFixed(2).replace(/\.?0+$/,"")+"×";
  });
 
  let queue=[], playing=false, stopped=false, currentURL=null;
  // allBlobs collects every chunk blob so we can merge them for download
  let allBlobs=[], generationDone=false;
 
  function setStatus(msg,err=false){ const el=document.getElementById("status"); el.textContent=msg; el.className=err?"err":""; }
  function setProgress(cur,total){
    document.getElementById("progress-wrap").classList.add("on");
    document.getElementById("prog-count").textContent=`${cur}/${total}`;
    document.getElementById("prog-bar").style.width=`${Math.round(cur/total*100)}%`;
  }
  function clearProgress(){ document.getElementById("progress-wrap").classList.remove("on"); document.getElementById("prog-bar").style.width="0%"; }
  function setBusy(busy){
    document.getElementById("speak-btn").disabled=busy;
    document.getElementById("stop-btn").classList.toggle("on",busy);
    document.getElementById("speak-btn").innerHTML=busy
      ?`<span class="pulsing">Generating…</span>`
      :`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg> Speak`;
  }
 
  function updateDownloadBtn(){
    const btn=document.getElementById("dl-btn");
    const hint=document.getElementById("dl-hint");
    if(generationDone && allBlobs.length>0){
      btn.disabled=false;
      hint.textContent=`${allBlobs.length} chunk${allBlobs.length>1?"s":""} ready · click to save`;
    } else {
      btn.disabled=true;
      hint.textContent="Available when all chunks are ready";
    }
  }
 
  function stopAll(){
    stopped=true; playing=false; queue=[];
    audio.pause(); audio.src="";
    setBusy(false); clearProgress();
    setStatus("Stopped.");
    document.getElementById("player-card").classList.remove("on");
    generationDone=false; allBlobs=[];
    updateDownloadBtn();
  }
 
  function playNext(){
    if(stopped||queue.length===0){ playing=false; return; }
    playing=true;
    const blob=queue.shift();
    if(currentURL) URL.revokeObjectURL(currentURL);
    currentURL=URL.createObjectURL(blob);
    audio.src=currentURL;
    audio.playbackRate=parseFloat(document.getElementById("pb-speed").value);
    audio.play();
    document.getElementById("player-card").classList.add("on");
    audio.onended=()=>{ if(!stopped) playNext(); };
  }
 
  async function downloadAudio(){
    if(!allBlobs.length) return;
    const btn=document.getElementById("dl-btn");
    btn.disabled=true;
    btn.innerHTML=`<span class="pulsing">Merging…</span>`;
    try {
      // Send all chunk blobs to /merge endpoint as multipart form data
      const form=new FormData();
      allBlobs.forEach((b,i)=>form.append("chunk",b,`chunk_${i}.mp3`));
      const res=await fetch("/merge",{ method:"POST", body:form });
      if(!res.ok) throw new Error("Merge failed");
      const merged=await res.blob();
      const url=URL.createObjectURL(merged);
      const a=document.createElement("a");
      a.href=url; a.download="tts_audio.mp3"; a.click();
      setTimeout(()=>URL.revokeObjectURL(url),5000);
    } catch(err){
      setStatus("Download error: "+err.message, true);
    }
    btn.disabled=false;
    btn.innerHTML=`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Download MP3`;
    updateDownloadBtn();
  }
 
  async function speak(){
    const text=document.getElementById("text").value.trim();
    const voice=document.getElementById("voice").value;
    const rate=+document.getElementById("rate").value;
    const pitch=+document.getElementById("pitch").value;
    if(!text){ setStatus("Please paste some text first.",true); return; }
 
    stopped=false; queue=[]; allBlobs=[]; generationDone=false;
    audio.pause(); audio.src="";
    updateDownloadBtn();
    setBusy(true);
    setStatus("Splitting into chunks…");
 
    const splitRes=await fetch("/split",{ method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({text}) });
    const {chunks,total}=await splitRes.json();
 
    setProgress(0,total);
    document.getElementById("prog-label").textContent="Generating…";
 
    let firstPlayed=false;
 
    for(let i=0;i<chunks.length;i++){
      if(stopped) break;
      setStatus(`Generating chunk ${i+1} of ${total}…`);
      try {
        const res=await fetch("/speak_chunk",{ method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({text:chunks[i],voice,rate,pitch}) });
        if(!res.ok) throw new Error("Server error on chunk "+(i+1));
        const blob=await res.blob();
        if(stopped) break;
        allBlobs.push(blob);          // keep a copy for download
        queue.push(blob);
        if(!playing&&!firstPlayed){ firstPlayed=true; setStatus("▶ Playing…"); playNext(); }
      } catch(err){ setStatus("Error: "+err.message,true); break; }
      setProgress(i+1,total);
    }
 
    if(!stopped){
      generationDone=true;
      updateDownloadBtn();
      document.getElementById("prog-label").textContent="Done ✓";
      document.getElementById("prog-label").classList.remove("pulsing");
      setStatus(playing||queue.length?"▶ Playing…":"✓ Done");
      setBusy(false);
    }
  }
</script>
</body>
</html>"""
 
# ── routes ────────────────────────────────────────────────────────────────────
 
@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")
 
@app.route("/voices")
def voices():
    return jsonify(VOICES)
 
@app.route("/split", methods=["POST"])
def split():
    data   = request.get_json()
    text   = data.get("text","").strip()
    chunks = split_chunks(text, max_chars=220)
    return jsonify({"chunks": chunks, "total": len(chunks)})
 
@app.route("/speak_chunk", methods=["POST"])
def speak_chunk():
    data  = request.get_json()
    text  = data.get("text","").strip()
    voice = data.get("voice","en-US-AriaNeural")
    rate  = data.get("rate", 0)
    pitch = data.get("pitch",0)
    if not text:
        return jsonify({"error":"empty chunk"}), 400
    audio_bytes = asyncio.run(tts_chunk(text, voice, rate, pitch))
    return Response(audio_bytes, mimetype="audio/mpeg",
                    headers={"Content-Disposition":"inline; filename=chunk.mp3"})
 
@app.route("/merge", methods=["POST"])
def merge():
    """Concatenate all uploaded MP3 chunk blobs and return a single MP3."""
    files = request.files.getlist("chunk")
    if not files:
        return jsonify({"error": "no chunks provided"}), 400
    buf = io.BytesIO()
    for f in files:
        buf.write(f.read())
    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="tts_audio.mp3"'}
    )
 
# ── main ──────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    print("\n╔══════════════════════════════════════╗")
    print("║   Edge TTS Reader  (chunk streaming)  ║")
    print("╠══════════════════════════════════════╣")
    print("║  Local : http://localhost:5050        ║")
    print("║  Phone : http://192.168.1.34:5050     ║")
    print("║  (phone must be on same Wi-Fi)        ║")
    print("╚══════════════════════════════════════╝\n")
    app.run(host="0.0.0.0", port=10000, debug=False, threaded=True)
