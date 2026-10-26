// Human teleop only. Disable native stream keyboard at the Python subscription;
// this channel supplies full key state and monotonically ordered heartbeats.
const mapping = {
  KeyI:'I',KeyK:'K',KeyL:'L',KeyJ:'J',KeyU:'U',KeyO:'O',KeyW:'W',KeyS:'S',
  KeyD:'D',KeyA:'A',KeyE:'E',KeyQ:'Q',KeyV:'V',KeyR:'R',KeyC:'C',KeyZ:'Z',
  ArrowUp:'UP',ArrowDown:'DOWN',ArrowLeft:'LEFT',ArrowRight:'RIGHT',
  Digit8:'NUMPAD_8',Digit2:'NUMPAD_2',Digit6:'NUMPAD_6',Digit4:'NUMPAD_4',
  Digit9:'NUMPAD_9',Digit7:'NUMPAD_7',Digit3:'NUMPAD_3',Digit1:'NUMPAD_1',
  Minus:'NUMPAD_SUBTRACT',Equal:'NUMPAD_ADD',BracketLeft:'NUMPAD_DIVIDE',BracketRight:'NUMPAD_MULTIPLY',
  Space:'SPACE',Digit0:'NUMPAD_0',Enter:'NUMPAD_ENTER',KeyP:'P',Escape:'ESCAPE',
  Numpad8:'NUMPAD_8',Numpad2:'NUMPAD_2',Numpad6:'NUMPAD_6',Numpad4:'NUMPAD_4',
  Numpad9:'NUMPAD_9',Numpad7:'NUMPAD_7',Numpad3:'NUMPAD_3',Numpad1:'NUMPAD_1',
  NumpadAdd:'NUMPAD_ADD',NumpadSubtract:'NUMPAD_SUBTRACT',NumpadDivide:'NUMPAD_DIVIDE',
  NumpadMultiply:'NUMPAD_MULTIPLY',Numpad0:'NUMPAD_0',NumpadEnter:'NUMPAD_ENTER'
};
const held = new Set();
const session = globalThis.crypto?.randomUUID?.() ?? String(Math.random());
const endpoint = `http://${location.hostname}:8211/keys`;
let seq = 0, lastAck = -1, lastAckAt = 0, latestSent = -1;
let guidance = null, guidanceAt = 0, serverKeys = new Set(), arrowsVisible = true, preciseMode = false, appliedKeys = new Set();
const directionOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
directionOverlay.setAttribute('aria-label', '로봇 방향별 조작 키 · 현재 카메라와 로봇 회전 반영');
directionOverlay.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:99990;overflow:hidden';
document.body.append(directionOverlay);
const displayKey = key => ({UP:'↑',DOWN:'↓',LEFT:'←',RIGHT:'→'}[key] || key);
function drawDirections() {
 const video = document.querySelector('video');
 if (!arrowsVisible || !guidance?.robots?.length || !video || performance.now()-guidanceAt>1500) {directionOverlay.innerHTML='';return;}
 const rect=video.getBoundingClientRect();
 const [sw,sh]=guidance.stream_size;
 const scale=Math.min(rect.width/sw,rect.height/sh);
 const ox=rect.left+(rect.width-sw*scale)/2, oy=rect.top+(rect.height-sh*scale)/2;
 const point=p=>p && p.length===2 && p.every(Number.isFinite) ? [ox+p[0]*scale,oy+p[1]*scale] : null;
 const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
 let markup='<defs><marker id="phyrc-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="context-stroke"/></marker><clipPath id="phyrc-video-clip"><rect x="'+ox+'" y="'+oy+'" width="'+sw*scale+'" height="'+sh*scale+'"/></clipPath></defs><g clip-path="url(#phyrc-video-clip)">';
 for (const robot of guidance.robots) {
  const color=robot.id===0?'#50e2f0':'#ffc766';
  const center=point(robot.center);
  if (center) markup+=`<g data-robot="${robot.id}"><rect x="${center[0]-44}" y="${center[1]-35}" width="88" height="25" rx="12" fill="#102236e8" stroke="${color}"/><text x="${center[0]}" y="${center[1]-18}" text-anchor="middle" fill="${color}" font-family="system-ui,sans-serif" font-size="12" font-weight="700">ROBOT ${robot.id}</text></g>`;
  for (const arrow of robot.arrows) {
   const a=point(arrow.start),b=point(arrow.end);if(!a||!b)continue;
   const active=held.has(arrow.key), received=serverKeys.has(arrow.key);
   const stroke=active?'#a3ff4f':color;
   const text=esc(`${arrow.label} ${displayKey(arrow.key)}${appliedKeys.has(arrow.key)?' ●':active&&received?' ✓':''}`);
   const w=Math.max(72,text.length*10+14);
   markup+=`<g data-direction-key="${esc(arrow.key)}" data-active="${active}" role="button" aria-label="${esc(arrow.label)} ${esc(displayKey(arrow.key))}" style="pointer-events:all;cursor:pointer;filter:drop-shadow(0 1px 3px #000)"><path d="M${a[0]} ${a[1]}L${b[0]} ${b[1]}" stroke="${stroke}" stroke-width="${active?6:3}" fill="none" marker-end="url(#phyrc-arrow)"/><rect x="${b[0]-w/2}" y="${b[1]-28}" width="${w}" height="23" rx="7" fill="${active?'#213a08f0':'#102236e8'}" stroke="${stroke}"/><text x="${b[0]}" y="${b[1]-12}" fill="${stroke}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" font-weight="700">${text}</text></g>`;
  }
 }
 directionOverlay.innerHTML=markup+'</g>';
}
window.addEventListener('resize',drawDirections);
let transport = '대기', latency = null, notice = '화면을 클릭한 뒤 조작하세요.';
const panel = document.createElement('section');
panel.setAttribute('aria-label', 'PhyRC 실시간 조작 안내');
panel.style.cssText = 'position:fixed;bottom:12px;right:12px;z-index:99999;width:340px;max-width:calc(100vw - 24px);max-height:calc(100vh - 24px);overflow:auto;box-sizing:border-box;background:rgba(15,28,43,.94);color:#eef5ff;padding:10px 12px;border:1px solid #64748b;border-radius:10px;font:13px/1.4 system-ui,sans-serif;box-shadow:0 4px 24px #0006';
panel.innerHTML = `
 <div style="display:flex;justify-content:space-between;gap:12px"><strong>조작 키 안내</strong><button type="button" data-help style="cursor:pointer;font:inherit">키 안내 펼치기</button></div>
 <div data-connection role="status"></div>
 <div>누른 키: <strong data-keys>없음</strong></div>
 <div data-notice></div>
 <div data-applied style="font-size:12px;color:#a3ff4f"></div>
 <button type="button" data-arrows style="font:inherit;margin-top:5px;cursor:pointer">로봇 방향 화살표 숨기기</button>
 <div style="font-size:11px;color:#b8c9dd">화살표: 로봇 기준 방향 · 초록: 누른 키 · ✓ 수신 · ● 제어 입력 반영</div>

 <div data-help-body hidden style="margin-top:6px">
 <table style="border-collapse:collapse;width:100%;text-align:left;color:#eef5ff"><thead><tr><th>동작 (+ / −)</th><th>로봇 0</th><th>로봇 1 · Mac</th></tr></thead><tbody>
 <tr><td>전진 / 후진</td><td>I / K</td><td>↑ / ↓</td></tr>
 <tr><td>옆 이동</td><td>L / J</td><td>→ / ←</td></tr>
 <tr><td>베이스 회전</td><td>U / O</td><td>[ / ]</td></tr>
 <tr><td>리프트</td><td>W / S</td><td>8 / 2</td></tr>
 <tr><td>팔 늘리기 / 줄이기</td><td>D / A</td><td>6 / 4</td></tr>
 <tr><td>손목 yaw</td><td>E / Q</td><td>9 / 7</td></tr>
 <tr><td>손목 pitch</td><td>V / R</td><td>= (+) / −</td></tr>
 <tr><td>손목 roll</td><td>C / Z</td><td>3 / 1</td></tr>
 <tr><td>그리퍼 토글</td><td>Space</td><td>0 또는 Enter</td></tr>
 </tbody></table>
 <div style="margin-top:6px">P: 초기화 · ESC: 종료·저장<br><span style="font-size:11px;color:#b8c9dd">창 이탈 시 키 해제 · 저장 완료는 READY 확인<br>응답은 입력 수신 확인이며 동작 상태는 영상 확인</span></div>
 </div>`;
document.body.append(panel);
const controls=document.createElement('section');
controls.style.cssText='position:fixed;top:12px;left:12px;z-index:99999;width:240px;border:1px solid #64748b;border-radius:12px;background:#0f1c2bf0;padding:10px;color:#eef5ff;font:13px/1.4 system-ui,sans-serif;box-shadow:0 4px 24px #0005';
controls.innerHTML=`<div style="display:flex;gap:6px"><button data-robot-select="0">로봇 0</button><button data-robot-select="1">로봇 1</button><button data-controls-collapse style="margin-left:auto">접기</button></div><div data-controls-body><button data-precision style="width:100%;margin:8px 0">연속 이동 · 짧게 눌러 미세 이동</button><div data-control-buttons style="display:grid;grid-template-columns:1fr 1fr;gap:5px"></div><div style="font-size:11px;color:#b8c9dd;margin-top:7px">화살표·버튼을 누르거나 키보드로 조작<br>정밀 모드: 키마다 짧은 입력 한 번</div></div>`;
document.body.append(controls);
let selectedRobot=0;
const buttonSets=[[['U','회전 + U'],['O','회전 − O'],['W','리프트 ↑ W'],['S','리프트 ↓ S'],['D','팔 늘림 D'],['A','팔 줄임 A'],['SPACE','집게 열기·닫기 Space']],
 [['NUMPAD_DIVIDE','회전 + ['],['NUMPAD_MULTIPLY','회전 − ]'],['NUMPAD_8','리프트 ↑ 8'],['NUMPAD_2','리프트 ↓ 2'],['NUMPAD_6','팔 늘림 6'],['NUMPAD_4','팔 줄임 4'],['NUMPAD_0','집게 열기·닫기 0']]];
function paintControls(){
 controls.querySelector('[data-control-buttons]').innerHTML=buttonSets[selectedRobot].map(([key,title])=>`<button data-control-key="${key}" style="padding:8px 2px;font:inherit;cursor:pointer;border:1px solid #5e7489;border-radius:6px;background:#233b50;color:#eef5ff;${key==='SPACE'||key==='NUMPAD_0'?'grid-column:1/3;':''}">${title}</button>`).join('');
 controls.querySelectorAll('[data-robot-select]').forEach(b=>{b.style.cssText=`font:inherit;cursor:pointer;border-radius:5px;border:1px solid #64748b;padding:4px 8px;background:${+b.dataset.robotSelect===selectedRobot?'#205e74':'#233b50'};color:white`;});
}
paintControls();
controls.querySelectorAll('[data-robot-select]').forEach(button=>button.addEventListener('click',()=>{selectedRobot=+button.dataset.robotSelect;paintControls();button.blur();}));
controls.querySelector('[data-controls-collapse]').addEventListener('click',e=>{const body=controls.querySelector('[data-controls-body]');body.hidden=!body.hidden;e.target.textContent=body.hidden?'펼치기':'접기';e.target.blur();});
controls.querySelector('[data-precision]').addEventListener('click',e=>{preciseMode=!preciseMode;e.target.textContent=preciseMode?'정밀 모드 · 한 번에 짧게 이동':'연속 이동 · 짧게 눌러 미세 이동';e.target.style.background=preciseMode?'#b7f077':'';e.target.blur();});
function pressControl(key){if(held.has(key))return;held.add(key);notice='화면 조작 입력';send();if(preciseMode)setTimeout(()=>{held.delete(key);send();},100);}
function releaseControl(key){held.delete(key);send();}
for(const surface of [directionOverlay,controls]){
 surface.addEventListener('pointerdown',e=>{const target=e.target.closest('[data-direction-key],[data-control-key]');if(!target)return;e.preventDefault();e.stopPropagation();const key=target.dataset.directionKey||target.dataset.controlKey;surface.dataset.pointerKey=key;surface.setPointerCapture(e.pointerId);pressControl(key);});
 const end=e=>{const key=surface.dataset.pointerKey;if(!key)return;e.preventDefault();delete surface.dataset.pointerKey;releaseControl(key);};
 surface.addEventListener('pointerup',end);surface.addEventListener('pointercancel',end);
}
const connection = panel.querySelector('[data-connection]');
const keysLabel = panel.querySelector('[data-keys]');
const noticeLabel = panel.querySelector('[data-notice]');
const arrowButton=panel.querySelector('[data-arrows]');
arrowButton.addEventListener('click',()=>{arrowsVisible=!arrowsVisible;arrowButton.textContent=arrowsVisible?'로봇 방향 화살표 숨기기':'로봇 방향 화살표 보이기';arrowButton.blur();drawDirections();});
const helpButton = panel.querySelector('[data-help]');
helpButton.addEventListener('click', () => {
 const help = panel.querySelector('[data-help-body]');
 help.hidden = !help.hidden;
 helpButton.textContent = help.hidden ? '키 안내 펼치기' : '키 안내 접기';
 helpButton.blur();
});
const label = key => key.replace('NUMPAD_', '숫자 ').replace('SPACE', 'Space').replace('ESCAPE', 'ESC');
function render() {
 drawDirections();
 panel.querySelector('[data-applied]').textContent=appliedKeys.size?`제어 입력 반영: ${[...appliedKeys].map(displayKey).join(" + ")}`:"제어 입력: 중립";
 const focused = document.hasFocus() && !document.hidden;
 const stale = lastAckAt > 0 && performance.now() - lastAckAt > 1500;
 const pending = latestSent > lastAck;
 connection.textContent = `${stale ? '응답 지연' : transport}${latency === null ? '' : ` · ${latency} ms`} · ${focused ? '조작 중' : '포커스 없음'}${pending ? ' · 대기' : ''}`;
 connection.style.color = transport === '오류' || stale ? '#ff9a9a' : '#8fe0b0';
 keysLabel.textContent = [...held].map(label).join(' + ') || '없음';
 noticeLabel.textContent = notice;
}
async function send(forceRelease=false) {
 const requestSeq = seq++;
 latestSent = requestSeq;
 const started = performance.now();
 render();
 try {
  const response = await fetch(endpoint, {method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({session,seq:requestSeq,keys:[...held],force_release:forceRelease}),keepalive:true,signal:AbortSignal.timeout(2000)});
  if (!response.ok) throw Error(response.status);
  const payload=await response.json();
  if (requestSeq > lastAck) {
   lastAck = requestSeq; lastAckAt = performance.now(); latency = Math.round(lastAckAt - started); transport = '서버 수신 정상';
   if(payload.guidance){guidance=payload.guidance;guidanceAt=performance.now();}
   serverKeys=new Set(payload.server_keys||[]);
   appliedKeys=new Set(payload.applied_keys||[]);
  }
 } catch (_) {
  if (requestSeq > lastAck) {
   held.clear(); transport = '오류'; notice = '입력 연결 오류: 로컬 키를 해제했습니다. 서버 watchdog 해제와 영상을 확인하세요.';
  }
 }
 render();
}
window.addEventListener('keydown', e => {
 const key = mapping[e.code];
 if (!key || e.metaKey || e.ctrlKey || e.altKey) return;
 e.preventDefault(); e.stopImmediatePropagation();
 if (e.repeat && preciseMode) return;
 if (!held.has(key)) {
  held.add(key);
  notice = key === 'ESCAPE' ? 'ESC · 종료 후 READY 확인 대기' :
   key === 'P' ? '초기화 키 전송 요청' : ['SPACE','NUMPAD_0','NUMPAD_ENTER'].includes(key) ? '그리퍼 토글 요청' : '이동 입력 중';
  send();
  if(preciseMode)setTimeout(()=>{held.delete(key);send();},100);
 }
}, true);
window.addEventListener('keyup', e => {
 const key = mapping[e.code]; if (!key) return;
 e.preventDefault(); e.stopImmediatePropagation(); held.delete(key); send();
}, true);
function release() {
 held.clear(); notice = '창 이탈 · 키 해제'; send(true);
}
window.addEventListener('blur', release);
window.addEventListener('pagehide', release);
document.addEventListener('visibilitychange', () => {if (document.hidden) release();});
setInterval(() => {if (!document.hidden && document.hasFocus()) send(); else render();}, 150);
render();
