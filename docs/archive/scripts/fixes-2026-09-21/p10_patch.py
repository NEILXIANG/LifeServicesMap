#!/usr/bin/env python3
"""2026-09-22 — analytics gaps found in the tracking audit (safe ones only).

New events, all carrying no free text and no personal data:
  task_src        a card's "official source ↗" link was opened      {id, to:host}
  task_link       any other outbound link inside a card was opened  {id, to:host}
  guide_link      an outbound link in the long-form guide           {to:host}
  feedback_click  the user reached for the email feedback link      {kind:'place'|'general'|'task', id, cat}
  season_shown    the seasonal note was actually displayed          {id}   (once per page load)

Deliberately NOT tracked (left for the maintainer to decide): taps on phone
numbers anywhere, and anything inside the "Help now" sheet — who calls a
crisis line is exactly what this tool promises not to know.
One delegated listener; no existing handler is changed."""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)

LISTENER = r"""// 2026-09-22 tracking audit: outbound links and the feedback mail link were
// invisible in the data — a card's official source, links in the guide text, and
// "Report an issue". One listener, capture phase so it runs before the in-app
// browser mailto handler below can stop anything. Records the destination host
// only. The Help sheet and every tel: link are left out on purpose.
function _linkHost(href){try{return new URL(href,location.href).hostname.replace(/^www\./,'');}catch(e){return '';}}
document.addEventListener('click',e=>{
  try{
    const a=e.target&&e.target.closest?e.target.closest('a[href]'):null;
    if(!a||a.closest('#helpModal'))return;
    const href=a.getAttribute('href')||'';
    if(/^mailto:/i.test(href)){
      if(a.classList.contains('pv-report')){
        const box=a.closest('.leaflet-popup-content'),pv=box&&box.querySelector('[data-pid]');
        trackEvent('feedback_click',{kind:'place',id:pv?pv.dataset.pid:undefined,cat:pv?pv.dataset.pcat:undefined});
      }else if(a.id==='feedbackLink')trackEvent('feedback_click',{kind:'general'});
      else if(a.closest('#guideTasks')&&a.closest('.task-checked'))trackEvent('feedback_click',{kind:'task',id:_taskOpen||undefined});
      return;
    }
    if(!/^https?:/i.test(href))return;
    if(a.closest('#guideTasks')){
      trackEvent(a.closest('.task-src')?'task_src':'task_link',{id:_taskOpen||undefined,to:_linkHost(href)});
    }else if(a.closest('#guideBody')){
      trackEvent('guide_link',{to:_linkHost(href)});
    }
  }catch(err){}
},true);
"""
s = rep(s, "if(IN_APP_BROWSER)document.addEventListener('click',e=>{",
        LISTENER + "if(IN_APP_BROWSER)document.addEventListener('click',e=>{")

s = rep(s, "let _seasonClosedMem={};", "let _seasonClosedMem={},_seasonShown={};")
s = rep(s, """  el.hidden=false;
  document.getElementById('seasonClose').onclick=()=>{""",
"""  el.hidden=false;
  if(!_seasonShown[x.id]){_seasonShown[x.id]=1;trackEvent('season_shown',{id:x.id});}
  document.getElementById('seasonClose').onclick=()=>{""")
open(E, 'w', encoding='utf-8').write(s)
print('p10 applied')
