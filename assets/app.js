/* בוקר טוב עולמי · app.js – persistent nav, TTS (he-IL), archive search, personal topic filter */
(function(){
"use strict";
function $(s,r){return (r||document).querySelector(s);}
function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));}
var LS={get:function(k){try{return localStorage.getItem(k);}catch(e){return null;}},set:function(k,v){try{localStorage.setItem(k,v);}catch(e){}}};
/* nav: open/closed state remembered on this device until the user changes it */
var tog=$("#nav-toggle");
function navSet(o,save){document.body.classList.toggle("nav-open",o);if(tog){tog.setAttribute("aria-expanded",o?"true":"false");tog.textContent=o?"✕ סגירה":"☰ תפריט";tog.setAttribute("aria-label",o?"סגירת התפריט":"פתיחת התפריט");}if(save)LS.set("kitaBoker:nav",o?"1":"0");}
navSet(document.body.classList.contains("nav-open"),false);
if(tog)tog.addEventListener("click",function(){navSet(!document.body.classList.contains("nav-open"),true);});
/* TTS */
var TTS={ok:("speechSynthesis" in window)&&("SpeechSynthesisUtterance" in window),q:[],rate:.95,
 voice:function(){if(!TTS.ok)return null;var v=speechSynthesis.getVoices()||[];for(var i=0;i<v.length;i++){if(/^(he|iw)/i.test(v[i].lang))return v[i];}return null;},
 stop:function(){if(!TTS.ok)return;TTS.q=[];speechSynthesis.cancel();$$(".speaking").forEach(function(x){x.classList.remove("speaking");});},
 speak:function(els,rate){if(!TTS.ok)return false;TTS.stop();TTS.rate=rate||.95;
  els.forEach(function(el){var t=(el.innerText||el.textContent||"").replace(/\s+/g," ").trim();if(!t)return;(t.match(/[^.!?:]+[.!?:״]*/g)||[t]).forEach(function(p){p=p.trim();if(p)TTS.q.push({el:el,t:p});});});
  TTS.next();return true;},
 next:function(){$$(".speaking").forEach(function(x){x.classList.remove("speaking");});var it=TTS.q.shift();if(!it)return;it.el.classList.add("speaking");
  var u=new SpeechSynthesisUtterance(it.t);u.lang="he-IL";u.rate=TTS.rate;var v=TTS.voice();if(v)u.voice=v;u.onend=u.onerror=function(){TTS.next();};speechSynthesis.speak(u);}
};
window.KitaTTS=TTS;
$$("[data-tts]").forEach(function(b){b.addEventListener("click",function(){
 var note=b.parentNode.querySelector(".tts-note");
 if(!TTS.ok){if(note)note.textContent="הדפדפן הזה לא תומך בהקראה. נסו Chrome, Edge או Safari.";return;}
 var sel=b.getAttribute("data-tts"),art=b.closest("article");
 var els=(sel==="@item"&&art)?$$(".tts-src",art):$$(sel);
 TTS.speak(els,b.hasAttribute("data-slow")?.75:.95);
 if(note)note.textContent=TTS.voice()?"מקריאים... אפשר לעצור בכל רגע.":"מקריאים. אם לא שומעים, ייתכן שאין במכשיר קול בעברית: אפשר להוסיף קול עברית בהגדרות, או לנסות Chrome או Edge.";
});});
$$("[data-tts-stop]").forEach(function(b){b.addEventListener("click",function(){TTS.stop();var n=b.parentNode.querySelector(".tts-note");if(n)n.textContent="";});});
window.addEventListener("beforeunload",function(){TTS.stop();});
/* personal topic filter: chosen topics open + first; others collapsed headers that open on tap.
   Saved per browser in localStorage "kitaBoker:topics" (JSON array). Nothing saved = all topics open. */
var tf=$("#tfilter"),TKEY="kitaBoker:topics";
var secs=$$("section.topic[data-topic]");
function secOpen(sec,o){var b=$(".topic-tog",sec),body=$(".topic-body",sec);if(!b||!body)return;
 body.hidden=!o;sec.classList.toggle("collapsed",!o);b.setAttribute("aria-expanded",o?"true":"false");}
secs.forEach(function(sec){var b=$(".topic-tog",sec);if(b)b.addEventListener("click",function(){var o=b.getAttribute("aria-expanded")!=="true";secOpen(sec,o);if(!o)TTS.stop();});});
document.documentElement.classList.add("tf-js");
if(tf&&secs.length){
 var grid=$("#topics-grid"),orig=grid?$$("section.topic",grid):[],boxes=$$(".tf-opts input",tf),panel=$("#tf-panel"),tgl=$("#tf-toggle"),all=$("#tf-all"),status=$("#tf-status");
 var names={};boxes.forEach(function(x){names[x.value]=x.parentNode.textContent.trim();});
 var load=function(){try{var v=JSON.parse(LS.get(TKEY)||"null");return (v&&v.length)?v.filter(function(k){return /^[a-z]+$/.test(k);}):[];}catch(e){return [];}};
 var apply=function(sel){
  var on=sel.length>0;
  secs.forEach(function(sec){secOpen(sec,!on||sel.indexOf(sec.getAttribute("data-topic"))>-1);sec.classList.toggle("mine",on&&sel.indexOf(sec.getAttribute("data-topic"))>-1);});
  if(grid){var mine=orig.filter(function(s){return !on||sel.indexOf(s.getAttribute("data-topic"))>-1;}),rest=orig.filter(function(s){return mine.indexOf(s)<0;});mine.concat(rest).forEach(function(s){grid.appendChild(s);});}
  boxes.forEach(function(x){x.checked=sel.indexOf(x.value)>-1;});
  all.hidden=!on;
  var shown=sel.filter(function(k){return names[k];}).map(function(k){return names[k];});
  status.textContent=!on?"כרגע מוצגים כל הנושאים.":(shown.length?"הנושאים שלכם, תמיד פתוחים: "+shown.join(", ")+". שאר הנושאים סגורים, ואפשר לפתוח כל אחד בלחיצה על הכותרת.":"הנושאים שבחרתם לא מופיעים במהדורה הזו, ולכן כל הנושאים כאן סגורים. אפשר לפתוח כל נושא בלחיצה על הכותרת.");
  var pre=document.getElementById("tf-pre");if(pre)pre.parentNode.removeChild(pre);
 };
 var save=function(sel){if(sel.length)LS.set(TKEY,JSON.stringify(sel));else{try{localStorage.removeItem(TKEY);}catch(e){}}apply(sel);};
 var panelSet=function(o){panel.hidden=!o;tgl.setAttribute("aria-expanded",o?"true":"false");};
 tf.hidden=false;apply(load());
 tgl.addEventListener("click",function(){panelSet(panel.hidden);if(!panel.hidden&&boxes[0])boxes[0].focus();});
 boxes.forEach(function(x){x.addEventListener("change",function(){var keep=load().filter(function(k){return !names[k];});save(keep.concat(boxes.filter(function(b){return b.checked;}).map(function(b){return b.value;})));});});
 $("#tf-done").addEventListener("click",function(){panelSet(false);tgl.focus();});
 var reset=function(){save([]);};
 $("#tf-reset").addEventListener("click",function(){reset();panelSet(false);tgl.focus();});
 all.addEventListener("click",function(){reset();tgl.focus();});
 panel.addEventListener("keydown",function(ev){if(ev.key==="Escape"){panelSet(false);tgl.focus();}});
}
/* a link to a topic or a story inside a collapsed topic (chips, archive, topic pages) opens it */
function openForHash(){var h=location.hash.slice(1);if(!h)return;var el=document.getElementById(h);if(!el)return;var sec=el.closest?el.closest("section.topic[data-topic]"):null;
 if(sec&&sec.classList.contains("collapsed")){secOpen(sec,true);setTimeout(function(){el.scrollIntoView();},0);}}
openForHash();window.addEventListener("hashchange",openForHash);
$$('a[href^="#sec-"]').forEach(function(a){a.addEventListener("click",function(){var sec=document.getElementById(a.getAttribute("href").slice(1));if(sec&&sec.classList.contains("collapsed"))secOpen(sec,true);});});
/* archive search */
var q=$("#q");
if(q){q.addEventListener("input",function(){var v=q.value.trim().toLowerCase(),any=false;
 $$(".arch").forEach(function(sec){var vis=0;$$("li",sec).forEach(function(li){var m=!v||li.getAttribute("data-q").indexOf(v)>-1;li.hidden=!m;if(m)vis++;});sec.hidden=!vis;if(vis)any=true;});
 $("#q-none").hidden=any;});}
})();
