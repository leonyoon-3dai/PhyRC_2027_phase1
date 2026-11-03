// Deliberately small grammar: one bounded, human-requested action per command.
const actions = [
  [/^(전진|앞으로|forward|앞)$/, ['I','UP']],
  [/^(후진|뒤로|backward|back|뒤)$/, ['K','DOWN']],
  [/^(오른쪽|오른쪽으로|right)$/, ['L','RIGHT']],
  [/^(왼쪽|왼쪽으로|left)$/, ['J','LEFT']],
  [/^(리프트올려|리프트올리기|리프트올림|liftup)$/, ['W','NUMPAD_8']],
  [/^(리프트내려|리프트내리기|리프트내림|liftdown)$/, ['S','NUMPAD_2']],
  [/^(팔늘려|팔늘리기|팔늘림|extendarm)$/, ['D','NUMPAD_6']],
  [/^(팔줄여|팔줄이기|팔줄임|retractarm)$/, ['A','NUMPAD_4']],
  [/^(집게토글|그리퍼토글|togglegripper)$/, ['SPACE','NUMPAD_0']],
];
export function parseCommand(input) {
  if (typeof input !== 'string' || input.length > 120) throw Error('명령은 120자 이내로 입력하세요.');
  let s=input.trim().toLowerCase().replace(/\s+/g,'');
  if (/^(정지|멈춰|stop)$/.test(s)) return {kind:'stop'};
  if (/^(초기화|reset)$/.test(s)) return {kind:'reset',key:'P',durationMs:150};
  let durationMs=300;
  const duration=s.match(/(\d+(?:\.\d+)?)(초|s|sec|seconds)$/);
  if (duration) {
    durationMs=Number(duration[1])*1000;
    if (durationMs < 100 || durationMs > 800) throw Error('시간은 0.1~0.8초만 가능합니다.');
    s=s.slice(0,duration.index);
  }
  const robot=s.match(/^(?:로봇|robot)(0|1)/);
  if (!robot) throw Error('로봇 0 또는 로봇 1을 명시하세요.');
  const id=Number(robot[1]); s=s.slice(robot[0].length).replace(/^(을|를|이|가)/,'');
  const match=actions.find(([pattern])=>pattern.test(s));
  if (!match) throw Error('알 수 없는 명령입니다. 예: 로봇 0 전진 0.3초');
  if (['SPACE','NUMPAD_0'].includes(match[1][id]) && duration) throw Error('집게 토글에는 시간을 지정하지 않습니다.');
  return {kind:'action',robot:id,key:match[1][id],durationMs};
}
