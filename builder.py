import json
import re
from urllib.parse import quote

INTERNAL = "https://internal.geoedge.com"
MAX_THUMBS = 20

TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CCR Gallery</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:#111;color:#eee;padding:10px}
h1{font-size:16px;margin-bottom:6px}
.stats{font-size:11px;color:#888;margin-bottom:10px}
.controls{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;align-items:center;position:sticky;top:0;background:#111;z-index:100;padding:6px 0;border-bottom:1px solid #2a2a2a}
#search{flex:1;min-width:180px;padding:5px 8px;background:#222;border:1px solid #444;color:#eee;border-radius:4px;font-size:13px}
#tld-filter{padding:5px 8px;background:#222;border:1px solid #444;color:#eee;border-radius:4px;font-size:12px;max-width:180px}
.fb{padding:4px 9px;background:#2a2a2a;border:1px solid #444;color:#ccc;border-radius:4px;cursor:pointer;font-size:11px}
.fb.on{background:#0047cc;border-color:#0047cc;color:#fff}
#cd{font-size:11px;color:#888;white-space:nowrap}
.db{border:1px solid #2a2a2a;border-radius:5px;margin-bottom:8px;padding:8px;background:#181818}
.db:hover{border-color:#444}
.db.hi{display:none}
.dh{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin-bottom:5px}
.dt{font-size:13px;font-weight:700;color:#6af;word-break:break-all}
.bg{display:flex;flex-wrap:wrap;gap:3px;align-items:center}
.vc{padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700}
.vc.cf{background:#c8600022;color:#f90;border:1px solid #f904}
.vc.tm{background:#006bc822;color:#6bf;border:1px solid #6bf4}
.bl{padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700;background:#c8000022;color:#f55;border:1px solid #f554}
.mal{padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700;background:#8b000022;color:#f77;border:1px solid #f774}
.qt{font-size:9px;color:#555;font-style:italic}
.cnt{font-size:10px;color:#777}
.more{font-size:9px;color:#f83;margin-left:3px}
.meta{font-size:9px;color:#666;margin-bottom:5px;display:flex;flex-wrap:wrap;gap:8px}
.meta span{color:#888}
.meta b{color:#aaa}
.thumbs{display:flex;flex-wrap:wrap;gap:5px}
.tc{width:108px;background:#202020;border-radius:4px;overflow:hidden;border:1px solid #2a2a2a}
.tc img{width:108px;height:72px;object-fit:cover;display:block;cursor:zoom-in}
.tm{padding:2px 3px;font-size:8px}
.th{display:block;color:#9cf;word-break:break-all;font-weight:600;margin-bottom:1px;overflow:hidden;max-height:2em}
.ti{display:block;color:#777;font-size:7px;margin-bottom:1px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.inc{display:block;color:#f44;font-size:8px;font-weight:700;margin-bottom:1px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.tl{display:flex;gap:3px;margin-top:1px}
.tl a{color:#7af;font-size:8px;text-decoration:none}
.ns{font-size:10px;color:#444;padding:4px 0}
.btn-research{padding:2px 8px;background:#1a3a1a;border:1px solid #3a6a3a;color:#6d6;border-radius:3px;cursor:pointer;font-size:10px;text-decoration:none;display:inline-block;margin-left:4px}
.btn-research:hover{background:#2a4a2a;color:#8f8}

/* Lightbox */
#lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,.88);z-index:9999;align-items:center;justify-content:center;flex-direction:column;gap:10px}
#lb.open{display:flex}
#lb img{max-width:90vw;max-height:82vh;border-radius:4px;box-shadow:0 0 40px #000}
#lb-meta{color:#aaa;font-size:11px;text-align:center;max-width:80vw}
#lb-close{position:fixed;top:14px;right:20px;font-size:28px;color:#aaa;cursor:pointer;line-height:1;background:none;border:none}
#lb-close:hover{color:#fff}
</style>
</head>
<body>
<h1>CCR Gallery</h1>
<div class="stats" id="stats"></div>
<div class="controls">
  <input id="search" type="text" placeholder="Search domain..." autofocus>
  <select id="tld-filter"><option value="">All TLDs</option></select>
  <button class="fb on" data-f="all">All</button>
  <button class="fb" data-f="bl">BL</button>
  <button class="fb" data-f="cf">Confiant</button>
  <button class="fb" data-f="tm">TMT</button>
  <button class="fb" data-f="mal">Malicious</button>
  <button class="fb" data-f="yd">Has data</button>
  <button class="fb" data-f="nd">No data</button>
  <span id="cd"></span>
</div>
<div id="gallery"></div>

<!-- Lightbox -->
<div id="lb">
  <button id="lb-close" onclick="closeLb()">&#x2715;</button>
  <img id="lb-img" src="" alt="">
  <div id="lb-meta"></div>
</div>

<script>
const ROWS=__DATA__;
const INT='https://internal.geoedge.com';

function thumbUrl(h){return`https://geoedge-analytics.s3.amazonaws.com/screenshots/${h.slice(0,2)}/${h.slice(2,4)}/landingthumb_${h}.jpg`}
function fullUrl(h){return`https://geoedge-analytics.s3.amazonaws.com/screenshots/${h.slice(0,2)}/${h.slice(2,4)}/landing_${h}.jpg`}
function jobUrl(id){return id?`${INT}/admin_geinternalpage/analytics/snapshots_job/${id}`:'#'}
function adsUrl(id){return id?`${INT}/admin_geinternalpage/analytics/snapshots_ads?req_rpt_period=all&search_type=ji&search_str=${id}`:'#'}
function researchUrl(display,query){
  const isHost=display!==query;
  const stype=isHost?'host':'tld';
  const sq=isHost?display:query;
  return`${INT}/admin_geinternalpage/analytics/snapshots_jobs?req_rpt_period=last30days&job_status=all&no_ads=all&scan_type=-1&code_type=-1&is_manual=&location=0&emulation_category=-1&location_via=all&malware_type=0&is_sound=&is_fake=&event_type=-1&is_screenshot=&security_rule=&security_rule_extra_id=0&preview=landing&search_type%5B%5D=${stype}&search_q%5B%5D=${encodeURIComponent(sq)}&group=landing_title&rows_limit=500&rows_order=&output_fields%5B%5D=in&output_fields%5B%5D=lu&output_fields%5B%5D=lh&submit=Search`;
}

// Lightbox
function openLb(src, meta){
  document.getElementById('lb-img').src=src;
  document.getElementById('lb-meta').textContent=meta||'';
  document.getElementById('lb').classList.add('open');
}
function closeLb(){
  document.getElementById('lb').classList.remove('open');
  document.getElementById('lb-img').src='';
}
document.getElementById('lb').addEventListener('click',function(e){if(e.target===this)closeLb();});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeLb();});

const gallery=document.getElementById('gallery');
const blocks=[];

// Populate TLD dropdown
const tldSet=new Set(ROWS.map(r=>r[4]).filter(Boolean));
const tldSel=document.getElementById('tld-filter');
[...tldSet].sort().forEach(t=>{const o=document.createElement('option');o.value=t;o.textContent=t;tldSel.appendChild(o);});

ROWS.forEach(([display,query,vendor,bl,tld,rdap_date,rdap_days,status,track_ads,track_lp,is_mal,thumbs])=>{
  const vc=vendor==='confiant'?'cf':'tm';
  const blBadge=bl?'<span class="bl">BL</span>':'';
  const malBadge=is_mal?'<span class="mal">MALICIOUS</span>':'';
  const extraStr=thumbs.length===20?` <span class="more">+more</span>`:'';
  const cnt=`<span class="cnt">(${thumbs.length} shots${extraStr})</span>`;

  // Meta row: domain age + status info
  const metaParts=[];
  if(rdap_date) metaParts.push(`<span><b>Reg:</b> ${rdap_date}${rdap_days?' ('+rdap_days+' days)':''}</span>`);
  if(status) metaParts.push(`<span><b>Status:</b> ${status}</span>`);
  if(track_ads) metaParts.push(`<span><b>Track ads:</b> ${track_ads}</span>`);
  if(track_lp) metaParts.push(`<span><b>Track LP:</b> ${track_lp}</span>`);
  const metaHtml=metaParts.length?`<div class="meta">${metaParts.join('')}</div>`:'';

  const thumbHtml=thumbs.length?thumbs.map(([h,jid,lp,loc,emul,time,lpUrl,incident])=>{
    const ju=jobUrl(jid),au=adsUrl(jid),src=thumbUrl(h),full=fullUrl(h);
    const metaStr=[loc,emul,time].filter(Boolean).join(' · ');
    const incidentLine=incident?`<span class="inc" title="${incident}">${incident}</span>`:'';
    const lpLine=lpUrl?`<span class="ti" title="${lpUrl}"><a href="${lpUrl}" target="_blank" style="color:#7af;text-decoration:none">${lpUrl.length>30?lpUrl.slice(0,30)+'…':lpUrl}</a></span>`:'';
    return`<div class="tc">
      <img loading="lazy" src="${src}" alt="${lp}" title="${metaStr}" onclick="openLb('${full}','${(metaStr+' | '+lp).replace(/'/g,'&apos;')}')">
      <div class="tm">
        <span class="th" title="${lp}">${lp}</span>
        ${incidentLine}${lpLine}
        <div class="tl"><a href="${ju}" target="_blank">job</a><a href="${au}" target="_blank">ads</a></div>
      </div>
    </div>`;
  }).join(''):'<div class="ns">No screenshots found</div>';

  const researchBtn=`<a class="btn-research" href="${researchUrl(display,query)}" target="_blank">🔍 Further Research</a>`;

  const div=document.createElement('div');
  div.className='db';
  div.dataset.d=display.toLowerCase();
  div.dataset.q=query.toLowerCase();
  div.dataset.v=vendor;
  div.dataset.bl=bl;
  div.dataset.mal=is_mal?'1':'0';
  div.dataset.tld=(tld||query).toLowerCase();
  div.dataset.hd=thumbs.length>0?'1':'0';
  div.innerHTML=`
    <div class="dh">
      <span class="dt">${display}</span>
      <div class="bg">
        <span class="vc ${vc}">${vendor}</span>${blBadge}${malBadge}
        <span class="qt">${query}</span>${cnt}${researchBtn}
      </div>
    </div>
    ${metaHtml}
    <div class="thumbs">${thumbHtml}</div>`;
  gallery.appendChild(div);
  blocks.push(div);
});

const totThumb=ROWS.reduce((s,r)=>s+r[11].length,0);
document.getElementById('stats').textContent=`${ROWS.length} domains • ${totThumb} screenshots shown`;

const searchEl=document.getElementById('search'),cdEl=document.getElementById('cd');
let af='all', tldFilter='';

tldSel.addEventListener('change',()=>{tldFilter=tldSel.value;upd();});

function upd(){
  const q=searchEl.value.trim().toLowerCase();
  let vis=0;
  blocks.forEach(b=>{
    let s=true;
    if(q&&!b.dataset.d.includes(q)&&!b.dataset.q.includes(q))s=false;
    if(tldFilter&&b.dataset.tld!==tldFilter.toLowerCase())s=false;
    if(af==='bl'&&b.dataset.bl!='1')s=false;
    if(af==='cf'&&b.dataset.v!=='confiant')s=false;
    if(af==='tm'&&b.dataset.v!=='TMT')s=false;
    if(af==='mal'&&b.dataset.mal!='1')s=false;
    if(af==='yd'&&b.dataset.hd!='1')s=false;
    if(af==='nd'&&b.dataset.hd!='0')s=false;
    b.classList.toggle('hi',!s);
    if(s)vis++;
  });
  cdEl.textContent=vis+'/'+blocks.length+' shown';
}
searchEl.addEventListener('input',upd);
document.querySelectorAll('.fb').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('.fb').forEach(b=>b.classList.remove('on'));
    btn.classList.add('on');af=btn.dataset.f;upd();
  });
});
upd();
</script>
</body>
</html>'''


def build_gallery(rows, screenshot_data):
    compact = []
    for row in rows:
        display = row["display"]
        query = row["query"]
        vendor = row.get("vendor", "")
        bl = 1 if row.get("should_bl") else 0
        tld = row.get("tld", query)
        rdap_date = row.get("rdap_creation_date", "")
        rdap_days = row.get("rdap_creation_days", "")
        status = row.get("status", "")
        track_ads = row.get("track_ads", "")
        track_lp = row.get("track_lp", "")
        is_mal = 1 if row.get("is_malicious") else 0

        items = screenshot_data.get(display, [])[:MAX_THUMBS]
        thumbs = []
        for it in items:
            m = re.search(r"landingthumb_([0-9a-f]{32})\.jpg", it.get("thumb", ""))
            if not m:
                continue
            h = m.group(1)
            job_id_m = re.search(r"/(\d+)$", it.get("jobHref", ""))
            job_id = job_id_m.group(1) if job_id_m else ""
            thumbs.append([
                h,
                job_id,
                it.get("lpHost", ""),
                it.get("location", ""),
                it.get("emulation", ""),
                it.get("time", ""),
                it.get("lpUrl", ""),
                it.get("incident", ""),
            ])

        compact.append([
            display, query, vendor, bl,
            tld, rdap_date, rdap_days,
            status, track_ads, track_lp, is_mal,
            thumbs,
        ])

    data_json = json.dumps(compact, separators=(",", ":"))
    return TEMPLATE.replace("__DATA__", data_json)
