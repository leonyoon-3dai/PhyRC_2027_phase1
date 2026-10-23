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
let transport = '대기', latency = null, notice = '화면을 클릭한 뒤 조작하세요.';
const panel = document.createElement('section');
panel.setAttribute('aria-label', 'PhyRC 실시간 조작 안내');
panel.style.cssText = 'position:fixed;bottom:12px;right:12px;z-index:99999;width:340px;max-width:calc(100vw - 24px);max-height:calc(100vh - 24px);overflow:auto;box-sizing:border-box;background:rgba(15,28,43,.94);color:#eef5ff;padding:10px 12px;border:1px solid #64748b;border-radius:10px;font:13px/1.4 system-ui,sans-serif;box-shadow:0 4px 24px #0006';
panel.innerHTML = `
 <div style="display:flex;justify-content:space-between;gap:12px"><strong>조작 키 안내</strong><button type="button" data-help style="cursor:pointer;font:inherit">키 안내 접기</button></div>
 <div data-connection role="status"></div>
 <div>누른 키: <strong data-keys>없음</strong></div>
 <div data-notice></div>

 <div data-help-body style="margin-top:6px">
 <table style="border-collapse:collapse;width:100%;text-align:left"><thead><tr><th>동작 (+ / −)</th><th>로봇 0</th><th>로봇 1 · Mac</th></tr></thead><tbody>
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
const connection = panel.querySelector('[data-connection]');
const keysLabel = panel.querySelector('[data-keys]');
const noticeLabel = panel.querySelector('[data-notice]');
const helpButton = panel.querySelector('[data-help]');
helpButton.addEventListener('click', () => {
 const help = panel.querySelector('[data-help-body]');
 help.hidden = !help.hidden;
 helpButton.textContent = help.hidden ? '키 안내 펼치기' : '키 안내 접기';
 helpButton.blur();
});
const label = key => key.replace('NUMPAD_', '숫자 ').replace('SPACE', 'Space').replace('ESCAPE', 'ESC');
function render() {
 const focused = document.hasFocus() && !document.hidden;
 const stale = lastAckAt > 0 && performance.now() - lastAckAt > 1500;
 const pending = latestSent > lastAck;
 connection.textContent = `${stale ? '응답 지연' : transport}${latency === null ? '' : ` · ${latency} ms`} · ${focused ? '조작 중' : '포커스 없음'}${pending ? ' · 대기' : ''}`;
 connection.style.color = transport === '오류' || stale ? '#ff9a9a' : '#8fe0b0';
 keysLabel.textContent = [...held].map(label).join(' + ') || '없음';
 noticeLabel.textContent = notice;
}
async function send() {
 const requestSeq = seq++;
 latestSent = requestSeq;
 const started = performance.now();
 render();
 try {
  const response = await fetch(endpoint, {method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({session,seq:requestSeq,keys:[...held]}),keepalive:true,signal:AbortSignal.timeout(2000)});
  if (!response.ok) throw Error(response.status);
  if (requestSeq > lastAck) {
   lastAck = requestSeq; lastAckAt = performance.now(); latency = Math.round(lastAckAt - started); transport = '서버 수신 정상';
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
 if (!held.has(key)) {
  held.add(key);
  notice = key === 'ESCAPE' ? 'ESC · 종료 후 READY 확인 대기' :
   key === 'P' ? '초기화 키 전송 요청' : ['SPACE','NUMPAD_0','NUMPAD_ENTER'].includes(key) ? '그리퍼 토글 요청' : '이동 입력 중';
  send();
 }
}, true);
window.addEventListener('keyup', e => {
 const key = mapping[e.code]; if (!key) return;
 e.preventDefault(); e.stopImmediatePropagation(); held.delete(key); send();
}, true);
function release() {
 held.clear(); notice = '창 이탈 · 키 해제'; send();
}
window.addEventListener('blur', release);
window.addEventListener('pagehide', release);
document.addEventListener('visibilitychange', () => {if (document.hidden) release();});
setInterval(() => {if (!document.hidden && document.hasFocus()) send(); else render();}, 150);
render();
