import assert from 'node:assert/strict';
import {parseCommand} from '../participant/streaming/text_commands.mjs';
assert.deepEqual(parseCommand('로봇 0 전진 0.3초'),{kind:'action',robot:0,key:'I',durationMs:300});
assert.deepEqual(parseCommand('robot 1 lift up'),{kind:'action',robot:1,key:'NUMPAD_8',durationMs:300});
assert.equal(parseCommand('로봇 1 집게 토글').key,'NUMPAD_0');
assert.equal(parseCommand('초기화').key,'P');
assert.equal(parseCommand('정지').kind,'stop');
for (const input of ['전진','로봇 2 전진','로봇 0 전진 5초','로봇 0 전진 후진','로봇 0 집게 열어','로봇 0 전진 0초']) assert.throws(()=>parseCommand(input));
console.log('text command grammar passed');
