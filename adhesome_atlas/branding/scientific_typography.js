/* Presentation only: preserve React nodes, raw table data, values and identifiers. */
(()=>{
 const pattern=__ATLAS_SPECIES_PATTERN__,owned=__ATLAS_TYPOGRAPHY_MODE__==='owned';
 if(window.__atlasTypography){window.__atlasTypography.setPattern(pattern);return}
 let species=new RegExp(pattern,'gi');
 const hasSpecies=s=>{species.lastIndex=0;return species.test(s)};
 function runs(text){
  const result=[];let end=0;
  const append=(s,bold,italic=false)=>{species.lastIndex=0;let at=0;for(const m of s.matchAll(species)){if(m.index>at)result.push({text:s.slice(at,m.index),bold,italic});result.push({text:m[0],bold,italic:true});at=m.index+m[0].length}if(at<s.length)result.push({text:s.slice(at),bold,italic})};
  for(const m of text.matchAll(/\*\*\*(?=\S)([^*]+?)\*\*\*|\*\*(?=\S)([^*]+?)\*\*|(?<!\*)\*(?=\S)([^*\n]+?)\*(?!\*)/g)){append(text.slice(end,m.index),false);append(m[1]||m[2]||m[3],!!(m[1]||m[2]),!!(m[1]||m[3]));end=m.index+m[0].length}append(text.slice(end),false);return result;
 }
 function font(base,run){
  const size=base.match(/\d+(?:\.\d+)?(?:px|pt|em|rem)\b[\s\S]*/);if(!size)return base;
  const weight=run.bold?'700':(base.match(/\b(?:[1-9]00|bold|bolder)\b/)||[''])[0];
  return ((run.italic||/\b(?:italic|oblique)\b/.test(base))?'italic ':'')+(weight?weight+' ':'')+size[0];
 }
 if(window.CanvasRenderingContext2D){for(const method of ['fillText','strokeText']){
  const original=CanvasRenderingContext2D.prototype[method];
  CanvasRenderingContext2D.prototype[method]=function(text,x,y,maxWidth){
   if(typeof text!=='string'||(Number.isFinite(maxWidth)&&maxWidth<=0)||(!hasSpecies(text)&&!(/\*\*\S[\s\S]*?\*\*/.test(text))))return original.apply(this,arguments);
   const parts=runs(text);if(!parts.some(r=>r.bold||r.italic))return original.apply(this,arguments);
   const base=this.font,widths=parts.map(r=>{this.font=font(base,r);return this.measureText(r.text).width});this.font=base;
   const total=widths.reduce((a,b)=>a+b,0),scale=Number.isFinite(maxWidth)&&total>maxWidth?maxWidth/total:1;
   const align=this.textAlign,right=align==='right'||(align==='end'&&this.direction!=='rtl')||(align==='start'&&this.direction==='rtl');
   const start=x-(align==='center'?total*scale/2:right?total*scale:0);
   this.save();this.translate(start,y);this.scale(scale,1);this.textAlign='left';let offset=0;
   parts.forEach((r,i)=>{this.font=font(base,r);original.call(this,r.text,offset,0);offset+=widths[i]});this.restore();
  };
 }}
 const skip='script,style,pre,code,textarea,title,[data-atlas-typeset]';
 function controls(){
  document.querySelectorAll('select,option,[role="option"],[data-baseweb="tag"],input[role="combobox"]').forEach(el=>{
   const text=el instanceof HTMLSelectElement?el.selectedOptions[0]?.textContent:el instanceof HTMLInputElement?el.value:el.textContent;
   if(text&&hasSpecies(text)){el.style.setProperty('font-style','italic','important');el.dataset.atlasSpeciesControl='1'}
   else if(el.dataset.atlasSpeciesControl){el.style.removeProperty('font-style');delete el.dataset.atlasSpeciesControl}
  });
  if(document.body){const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);while(walk.nextNode()){
   const node=walk.currentNode,p=node.parentElement;if(!p||p.closest('script,style,pre,code,textarea'))continue;
   const value=node.data.trim();species.lastIndex=0;const match=species.exec(value);
   if(match&&match.index===0&&match[0].length===value.length&&p.textContent.trim()===value)p.style.fontStyle='italic';
  }}
 }
 function decorate(){
  controls();if(!owned||!document.body)return;
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),nodes=[];
  while(walker.nextNode()){const node=walker.currentNode,p=node.parentElement;if(!p||p.closest(skip)||p.closest('option,select,input'))continue;if(node.data.includes('**')||hasSpecies(node.data))nodes.push(node)}
  for(const node of nodes){
   const p=node.parentElement;if(!p||!node.isConnected)continue;
   const existingItalic=!!p.closest('em,i'),parts=runs(node.data);
   if(!parts.some(r=>r.bold||r.italic&&!existingItalic))continue;
   const svg=p.namespaceURI==='http://www.w3.org/2000/svg',fragment=document.createDocumentFragment();
   for(const r of parts){
    if(!r.bold&&(!r.italic||existingItalic)){fragment.appendChild(document.createTextNode(r.text));continue}
    const span=svg?document.createElementNS('http://www.w3.org/2000/svg','tspan'):document.createElement(r.bold?'strong':'em');
    span.setAttribute('data-atlas-typeset','1');span.textContent=r.text;
    if(r.italic){span.style.fontStyle='italic';if(svg)span.setAttribute('font-style','italic')}
    if(r.bold){span.style.fontWeight='700';if(svg)span.setAttribute('font-weight','700')}
    fragment.appendChild(span);
   }
   node.replaceWith(fragment);
  }
 }
 let queued=false;
 const schedule=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;decorate()})};
 window.__atlasTypography={runs,setPattern(value){species=new RegExp(value,'gi');schedule()}};
 const start=()=>{decorate();new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true,characterData:true});window.addEventListener('resize',schedule);document.addEventListener('change',schedule,true)};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
