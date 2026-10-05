"""Self-contained, editable SVG network for Streamlit's HTML iframe."""

import json
import math


def vector_network_html(nodes, edges, title, *, label_mode='hidden'):
    """Render positioned nodes and associations as draggable, exportable SVG.

    Each node has id, label, x, y, color, radius and optional detail/category.
    Each edge has source, target and optional color/width. Supplied positions are
    preserved proportionally; dragging changes presentation only, not data.
    """
    nodes = [dict(node) for node in nodes]
    ids = {str(node['id']) for node in nodes}
    edges = [dict(edge) for edge in edges
             if str(edge['source']) in ids and str(edge['target']) in ids]
    for edge in edges:
        edge['source'], edge['target'] = str(edge['source']), str(edge['target'])
    finite_x = [float(node['x']) for node in nodes if math.isfinite(float(node['x']))]
    finite_y = [float(node['y']) for node in nodes if math.isfinite(float(node['y']))]
    xmin, xmax = (min(finite_x), max(finite_x)) if finite_x else (0.0, 1.0)
    ymin, ymax = (min(finite_y), max(finite_y)) if finite_y else (0.0, 1.0)
    scale = min(1090 / (xmax - xmin) if xmax != xmin else math.inf,
                610 / (ymax - ymin) if ymax != ymin else math.inf)
    if not math.isfinite(scale):
        scale = 1
    for node in nodes:
        x, y = float(node['x']), float(node['y'])
        node['x'] = round(600 + (x - (xmin + xmax) / 2) * scale, 2) if math.isfinite(x) else 600
        node['y'] = round(360 + (y - (ymin + ymax) / 2) * scale, 2) if math.isfinite(y) else 360
        node['id'] = str(node['id'])
        node['label'] = str(node.get('label', node['id']))
        node['radius'] = max(7, min(30, float(node.get('radius', 13))))
    payload = json.dumps({'nodes': nodes, 'edges': edges, 'title': title,
                          'labelMode': label_mode}, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c')
    return r'''<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f8f2;color:#14221a;font:14px Arial,sans-serif}
.bar{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:10px 13px;background:#064c2c;color:#fff}
.bar strong{margin-right:auto;font-size:15px}.bar label{font-weight:700}
button,select{padding:7px 10px;border:1px solid #a9c1ae;border-radius:7px;background:#fff;color:#102c1a;font-weight:650;cursor:pointer}
.hint{padding:7px 13px;font-size:12px;color:#33443a;background:#e7f1e8}
.stage{overflow:auto;background:#fff;border-bottom:1px solid #d4e1d6}
svg{display:block;width:100%;height:690px;min-width:700px;touch-action:none}
.node{cursor:grab}.node:active{cursor:grabbing}.node text{pointer-events:none}
.node:hover circle{stroke:#b91c1c;stroke-width:3}.edge{pointer-events:none}
.detail{min-height:62px;padding:10px 14px;background:#fff;line-height:1.45}
.detail strong{color:#064c2c}.detail span{display:inline-block;margin-right:16px}
.legend{padding:8px 14px;background:#fff;font-size:12px}.legend span{display:inline-flex;gap:5px;align-items:center;margin:4px 12px 4px 0}.legend i{width:11px;height:11px;border:1px solid #777;border-radius:50%;display:inline-block}
</style></head><body>
<div class="bar"><strong id="heading"></strong><label for="names">Node names</label>
<select id="names"><option value="hidden">Hidden</option><option value="outside">Outside nodes</option><option value="center">Centered in nodes</option></select>
<button id="zoomIn" aria-label="Zoom in">＋</button><button id="zoomOut" aria-label="Zoom out">−</button><button id="fit">Fit view</button>
<button id="reset">Reset positions</button><button id="export">Download SVG</button></div>
<div class="hint">Drag nodes to rearrange them; drag the background to pan and scroll to zoom. Click a node to inspect its annotation. Export SVG to keep the current arrangement.</div>
<div class="stage"><svg id="network" viewBox="0 0 1200 720" role="img" aria-label="Editable vector network"><rect x="0" y="0" width="1200" height="720" fill="#ffffff"/><g id="edgeLayer"></g><g id="nodeLayer"></g></svg></div>
<div class="detail" id="detail" aria-live="polite">Select a node to inspect its annotation.</div>
<details class="legend"><summary>Color legend</summary><div id="legend"></div></details>
<script>
const data=__PAYLOAD__;
const svg=document.getElementById('network'), edgeLayer=document.getElementById('edgeLayer'),nodeLayer=document.getElementById('nodeLayer');
const byId=new Map(data.nodes.map(n=>[n.id,n]));
const original=new Map(data.nodes.map(n=>[n.id,{x:n.x,y:n.y}]));
const incident=new Map(data.nodes.map(n=>[n.id,[]]));
const nodeGroups=new Map();
document.getElementById('heading').textContent=data.title;
const names=document.getElementById('names');names.value=data.labelMode;
function element(tag,attrs){const item=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attrs))item.setAttribute(key,String(value));return item}
function point(event,matrix=svg.getScreenCTM().inverse()){const p=svg.createSVGPoint();p.x=event.clientX;p.y=event.clientY;return p.matrixTransform(matrix)}
let view={x:0,y:0,w:1200,h:720};
function applyView(){svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.w} ${view.h}`)}
function zoom(factor,anchor={x:view.x+view.w/2,y:view.y+view.h/2}){const width=Math.max(120,Math.min(4800,view.w*factor)),ratio=width/view.w;view={x:anchor.x-(anchor.x-view.x)*ratio,y:anchor.y-(anchor.y-view.y)*ratio,w:width,h:view.h*ratio};applyView()}
document.getElementById('zoomIn').onclick=()=>zoom(.8);document.getElementById('zoomOut').onclick=()=>zoom(1.25);
document.getElementById('fit').onclick=()=>{view={x:0,y:0,w:1200,h:720};applyView()};
svg.addEventListener('wheel',event=>{event.preventDefault();zoom(event.deltaY>0?1.12:.89,point(event))},{passive:false});
let pan=null;
svg.addEventListener('pointerdown',event=>{if(event.target.closest('.node'))return;pan={point:point(event),view:{...view},matrix:svg.getScreenCTM().inverse()};svg.setPointerCapture(event.pointerId)});
svg.addEventListener('pointermove',event=>{if(!pan)return;const p=point(event,pan.matrix);view.x=pan.view.x+pan.point.x-p.x;view.y=pan.view.y+pan.point.y-p.y;applyView()});
svg.addEventListener('pointerup',()=>pan=null);svg.addEventListener('pointercancel',()=>pan=null);
function updateEdge(record){const a=byId.get(record.data.source),b=byId.get(record.data.target);record.line.setAttribute('x1',a.x);record.line.setAttribute('y1',a.y);record.line.setAttribute('x2',b.x);record.line.setAttribute('y2',b.y)}
function updateLabels(){for(const n of data.nodes){const group=nodeGroups.get(n.id),label=group.querySelector('text');const mode=names.value;label.style.display=mode==='hidden'?'none':'';
  label.setAttribute('y',mode==='center'?0:n.radius+14);label.setAttribute('font-size',mode==='center'?12:11);
  label.setAttribute('font-weight',mode==='center'?'700':'600');label.setAttribute('fill',mode==='center'?'#10251a':'#172b20');
}}
for(const edge of data.edges){const line=element('line',{class:'edge',stroke:edge.color||'#b5c8bd','stroke-width':edge.width||1.2,'stroke-opacity':.75});edgeLayer.appendChild(line);
  const record={data:edge,line};incident.get(String(edge.source)).push(record);incident.get(String(edge.target)).push(record);updateEdge(record)}
for(const n of data.nodes){const group=element('g',{class:'node',transform:`translate(${n.x},${n.y})`});
  const circle=element('circle',{r:n.radius,fill:n.color||'#08743f',stroke:'#ffffff','stroke-width':1.5});group.appendChild(circle);
  const label=element('text',{'text-anchor':'middle','dominant-baseline':'middle','paint-order':'stroke',stroke:'#ffffff','stroke-width':2,'stroke-linejoin':'round'});label.textContent=n.label;group.appendChild(label);
  const tip=element('title',{});tip.textContent=n.label+' · '+(n.category||'')+' · '+n.id;group.appendChild(tip);
  let drag=null,moved=false;
  group.addEventListener('pointerdown',event=>{const p=point(event);drag={x:p.x,y:p.y,dx:p.x-n.x,dy:p.y-n.y};moved=false;group.setPointerCapture(event.pointerId);event.preventDefault();event.stopPropagation()});
  group.addEventListener('pointermove',event=>{if(!drag)return;const p=point(event);if(Math.abs(p.x-drag.x)>2||Math.abs(p.y-drag.y)>2)moved=true;n.x=Math.max(20,Math.min(1180,p.x-drag.dx));n.y=Math.max(20,Math.min(700,p.y-drag.dy));group.setAttribute('transform',`translate(${n.x},${n.y})`);for(const edge of incident.get(n.id))updateEdge(edge)});
  group.addEventListener('pointerup',()=>{drag=null});group.addEventListener('pointercancel',()=>{drag=null});
  group.addEventListener('click',()=>{if(moved){moved=false;return}const detail=document.getElementById('detail');detail.replaceChildren();const heading=document.createElement('strong');heading.textContent=n.label+' · '+n.id;detail.appendChild(heading);
    const fields=n.detail||{};for(const [key,value] of Object.entries(fields)){const item=document.createElement('span');item.textContent=key+': '+value;detail.appendChild(item)}});
  nodeLayer.appendChild(group);nodeGroups.set(n.id,group)}
names.addEventListener('change',updateLabels);updateLabels();
const legend=document.getElementById('legend'),categories=new Map();
for(const node of data.nodes)if(node.category)categories.set(node.category,node.color);
for(const edge of data.edges)if(edge.category)categories.set('Edge: '+edge.category,edge.color);
for(const [category,color] of categories){const chip=document.createElement('span'),swatch=document.createElement('i');swatch.style.backgroundColor=color||'#08743f';chip.appendChild(swatch);chip.appendChild(document.createTextNode(category));legend.appendChild(chip)}
document.getElementById('reset').onclick=()=>{for(const n of data.nodes){Object.assign(n,original.get(n.id));nodeGroups.get(n.id).setAttribute('transform',`translate(${n.x},${n.y})`)}for(const records of incident.values())for(const record of records)updateEdge(record)};
document.getElementById('export').onclick=()=>{const clone=svg.cloneNode(true);clone.setAttribute('xmlns','http://www.w3.org/2000/svg');const blob=new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='schistosome_network.svg';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000)};
</script></body></html>'''.replace('__PAYLOAD__', payload)
