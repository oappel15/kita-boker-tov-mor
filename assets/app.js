/* בוקר טוב עולמי · app.js – persistent nav, TTS (he-IL), archive search */
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
/* archive search */
var q=$("#q");
if(q){q.addEventListener("input",function(){var v=q.value.trim().toLowerCase(),any=false;
 $$(".arch").forEach(function(sec){var vis=0;$$("li",sec).forEach(function(li){var m=!v||li.getAttribute("data-q").indexOf(v)>-1;li.hidden=!m;if(m)vis++;});sec.hidden=!vis;if(vis)any=true;});
 $("#q-none").hidden=any;});}
})();
