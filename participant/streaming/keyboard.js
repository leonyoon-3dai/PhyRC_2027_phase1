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
const held=new Set(); let seq=0; const session=crypto.randomUUID?.() ?? String(Math.random());
const endpoint=`http://${location.hostname}:8211/keys`;
const status=document.createElement('div');
status.textContent='PhyRC human teleop: SPACE robot 0 grip; 0 robot 1 grip; P reset; ESC save/exit. Mac robot 1: arrows + 8/2,6/4,9/7,+/−,3/1,[/]. Click page to control.';
status.style.cssText='position:fixed;top:0;left:0;right:0;z-index:99999;background:#152635;color:white;padding:8px;font:14px sans-serif';
document.body.append(status);
function send(){
 fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({session,seq:seq++,keys:[...held]}),keepalive:true})
 .then(r=>{if(!r.ok)throw Error(r.status);status.style.background='#152635';})
 .catch(()=>{held.clear();status.style.background='#9b2323';});
}
window.addEventListener('keydown',e=>{
 const key=mapping[e.code]; if(!key||e.metaKey||e.ctrlKey||e.altKey)return;
 e.preventDefault();e.stopImmediatePropagation();if(!held.has(key)){held.add(key);send();}
},true);
window.addEventListener('keyup',e=>{
 const key=mapping[e.code];if(!key)return;e.preventDefault();e.stopImmediatePropagation();held.delete(key);send();
},true);
function release(){held.clear();send();}
window.addEventListener('blur',release);
window.addEventListener('pagehide',release);
document.addEventListener('visibilitychange',()=>{if(document.hidden)release();});
setInterval(()=>{if(!document.hidden&&document.hasFocus())send();},150);
