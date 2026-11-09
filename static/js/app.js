const $ = (id) => document.getElementById(id);
let pendingAction = null;
let currentLanguage = "te-IN";

function toast(message) {
  const el = $("toast"); el.textContent = message; el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 3000);
}
function addBubble(text, who="bot", label="Dukaan Dost") {
  const log=$("chatLog"), div=document.createElement("div");
  div.className=`bubble ${who}`;
  const b=document.createElement("b"); b.textContent=who==="user"?"You":label;
  const p=document.createElement("p"); p.textContent=text;
  div.append(b,p); log.append(div); log.scrollTop=log.scrollHeight;
}
async function speak(text) {
  try {
    const res=await fetch("/api/speak",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,language:currentLanguage})});
    const data=await res.json();
    if(data.success){$("audioPlayer").src=data.audio_url;$("audioPlayer").hidden=false;await $("audioPlayer").play().catch(()=>{});}
  } catch(e) { console.warn("Timbre unavailable",e); }
}
async function sendCommand(text, confirmed=false) {
  addBubble(text,"user");
  const res=await fetch("/api/command",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,confirmed})});
  const data=await res.json();
  if(data.requires_confirmation){
    pendingAction={text,confirmed:true};
    const yes=window.confirm(data.reply+"\n\nProceed?");
    if(yes){return sendCommand(text,true);}
    addBubble("Okay, I haven't changed your inventory.","bot");
    return;
  }
  pendingAction=null;
  addBubble(data.reply||data.error||"Something went wrong.");
  if(data.success){speak(data.reply);refreshDashboard();}
  else toast(data.reply||data.error||"Request failed");
}
async function refreshDashboard(){
  const res=await fetch("/api/dashboard"), data=await res.json();
  $("revenue").textContent="₹"+Number(data.stats.revenue).toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2});
  $("unitsSold").textContent=data.stats.units_sold;
  $("productCount").textContent=data.products.length;
  $("lowCount").textContent=data.stats.low_stock;
  $("inventoryRows").innerHTML=data.products.map(p=>`<tr><td>${escapeHtml(p.name)}</td><td>${p.quantity} ${escapeHtml(p.unit)}</td><td>₹${Number(p.price).toFixed(2)}</td><td><span class="pill ${p.quantity<=p.low_stock_threshold?"low":"ok"}">${p.quantity<=p.low_stock_threshold?"Low stock":"In stock"}</span></td></tr>`).join("");
  $("lowList").textContent=data.low_stock_items.length? "Needs restocking: "+data.low_stock_items.map(p=>p.name).join(", "):"All products are above their alert levels.";
  $("recentSales").innerHTML=data.recent_sales.length?data.recent_sales.map(s=>`<div class="sale-row"><div><b>${escapeHtml(s.name)}</b><small>${s.quantity} ${escapeHtml(s.unit)} · ${new Date(s.created_at+"Z").toLocaleString()}</small></div><strong>₹${Number(s.total).toFixed(2)}</strong></div>`).join(""):'<p class="muted">No sales recorded yet. Try “Sell 2 soap”.</p>';
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
$("commandForm").addEventListener("submit",async e=>{e.preventDefault();const input=$("commandInput"),text=input.value.trim();if(!text)return;input.value="";await sendCommand(text);});
document.querySelectorAll("[data-command]").forEach(b=>b.addEventListener("click",()=>sendCommand(b.dataset.command)));
$("refreshBtn").addEventListener("click",refreshDashboard);
$("productForm").addEventListener("submit",async e=>{
  e.preventDefault();const form=new FormData(e.currentTarget),body=Object.fromEntries(form.entries());
  for(const k of ["quantity","price","low_stock_threshold"])body[k]=Number(body[k]);
  const res=await fetch("/api/products",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const data=await res.json();
  if(data.success){toast(data.message);e.currentTarget.reset();refreshDashboard();}
  else toast(data.error||"Could not add product");
});
$("audioFile").addEventListener("change",async e=>{
  const file=e.target.files[0];if(!file)return;
  addBubble("Voice note: "+file.name,"user");
  const fd=new FormData();fd.append("audio",file);
  toast("Sending audio to Gnani Prisma…");
  try{
    const res=await fetch("/api/voice",{method:"POST",body:fd}),data=await res.json();
    if(!data.success)throw new Error(data.error||"Transcription failed");
    currentLanguage=(data.detected_language||"te-IN").startsWith("en")?"en-IN":"te-IN";
    addBubble("Prisma heard: "+data.transcript,"bot","Gnani Prisma");
    await sendCommand(data.transcript);
  }catch(err){addBubble(err.message);toast(err.message);}
  e.target.value="";
});
fetch("/health").then(r=>r.json()).then(d=>{$("apiStatus").textContent=d.gnani_configured?"Gnani API connected (key configured)":"Demo mode · Add Gnani API key";$("apiStatus").previousElementSibling.style.background=d.gnani_configured?"#16845b":"#d99b26";}).catch(()=>{$("apiStatus").textContent="Server status unavailable";});
refreshDashboard();
