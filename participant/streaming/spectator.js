// Read-only spectator UI. No keyboard, robot command, or simulator mutation API.
const style = document.createElement('style');
style.textContent = `
 #phyrc-progress{width:390px;max-width:38vw;flex:none;height:100vh;overflow:auto;padding:18px;background:#101b28;color:#e7eef7;border-left:1px solid #344456;font:13px/1.55 system-ui,sans-serif}
 #phyrc-progress h1{font-size:18px;margin:0 0 4px}#phyrc-progress h2{font-size:14px;color:#b7d9ed;margin:20px 0 8px}
 #phyrc-progress p{font:inherit;color:inherit;margin:5px 0}#phyrc-progress pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#162536;padding:10px;border-radius:6px;font:12px/1.5 ui-monospace,monospace;margin:7px 0}
 #phyrc-progress dl{display:grid;grid-template-columns:105px 1fr;gap:5px 10px;margin:8px 0}#phyrc-progress dt{color:#98aec3}#phyrc-progress dd{margin:0;overflow-wrap:anywhere}
 #phyrc-progress details{border-top:1px solid #344456;margin-top:9px;padding-top:9px}#phyrc-progress summary{cursor:pointer;color:#c1dfef}
 #phyrc-progress .muted{color:#99acbf;font-size:12px}#phyrc-progress .score{font-size:24px;font-weight:700;color:#9ce2c1}#phyrc-progress .warning{color:#ffd38a}
 #phyrc-progress ul{padding-left:17px}#phyrc-progress li{margin:4px 0;overflow-wrap:anywhere}
 @media(max-width:850px){#app{flex-direction:column!important}#stream-container{height:55vh;flex:none}#phyrc-progress{height:45vh;width:100%;max-width:none;border-left:0;border-top:1px solid #344456;padding:12px}}
`;
document.head.append(style);
const panel = document.createElement('aside');
panel.id = 'phyrc-progress';
panel.setAttribute('aria-label', '자동 수집 진행 상황 · 관찰 전용');
document.getElementById('app').append(panel);
const element = (tag, content, className) => {
  const node = document.createElement(tag);
  if (content !== undefined) node.textContent = String(content);
  if (className) node.className = className;
  return node;
};
const value = v => v === null || v === undefined ? '미측정' : typeof v === 'boolean' ? (v ? '예' : '아니오') : String(v);
const seconds = v => typeof v === 'number' ? `${v.toFixed(2)}초` : '미측정';
const statusNames = {starting:'환경 준비',collecting:'수집 진행',replaying_prefix:'기록한 행동 재실행',completed:'실행 종료',review_ready:'점수 기준 도달 · 검토 준비',failed:'실행 오류',interrupted:'중단'};
const stageNames = {preparation:'준비',approach:'접근',grasp:'파지',lift:'들기',transport:'운반',first_sleeve:'첫 소매',shoulder:'어깨',second_sleeve:'두 번째 소매',neck:'목',orientation:'방향',recovery:'복구',final_check:'최종 확인'};
const activityNames = {initializing:'환경 초기화',replay_prefix:'기록한 행동 재실행',model_request:'모델 응답 대기',executing_action:'행동 적용·기록',closed:'실행 종료'};
let sdkConnected = false;
let lastData = null;
let lastReceived = 0;
let lastFrames = null;
let frameIncrease = false;
let lastFrameCheck = 0;
let transportError = false;
window.addEventListener('phyrc-stream-state', event => {
  sdkConnected = event.detail?.sdk_connected === true;
  render();
});

function details(title, body, open=false) {
  const node = element('details');
  node.open = open;
  node.append(element('summary', title), element('pre', body));
  return node;
}
function facts(items) {
  const list = element('dl');
  for (const [name, item] of items) list.append(element('dt', name), element('dd', item));
  return list;
}
function render() {
  const children = [element('h1','PhyRC 라이브 관찰'), element('p','자동 수집 · 로봇 조작 없음','muted')];
  const video = document.getElementById('remote-video');
  const receiving = frameIncrease && performance.now()-lastFrameCheck < 5000;
  children.push(element('p', `영상 연결: ${sdkConnected ? 'SDK 연결됨' : '대기/끊김'} · 프레임: ${receiving ? '증가 확인' : '증가 미확인'}`));
  children.push(element('p', `브라우저 보고 ${video?.videoWidth || 0}×${video?.videoHeight || 0} · 총 프레임 ${value(lastFrames)}`, 'muted'));
  if (transportError) children.push(element('p', '진행 정보 연결 대기 · 마지막 확인 기록을 표시합니다.', 'warning'));
  if (!lastData?.available) {
    children.push(element('p','수집 기록을 기다리고 있습니다.'));
    panel.replaceChildren(...children);
    return;
  }
  const a=lastData.attempt, score=lastData.evaluation || {}, recent=lastData.recent_decisions || [];
  const latest=recent.at(-1), response=latest?.response || {};
  children.push(element('h2','최근 모델 수집 기록'));
  children.push(element('p','현재 영상과 아래 모델 수집 기록이 같은 실행인지 확인되지 않았습니다.','warning'));
  children.push(facts([
    ['run ID',lastData.run_id],['상태',statusNames[a.status] || value(a.status)],
    ['현재 처리',activityNames[a.activity] || '최근 기록 참고'],
    ['기록 시작 UTC',value(a.started_at_utc)],['기록 종료 UTC',value(a.ended_at_utc)],
    ['최근 의도 단계',stageNames[response.stage] || value(response.stage)],
    ['기록 전이',value(a.simulation_steps)],['모델 호출',value(a.actor_calls_attempted)],
    ['원본 재실행',value(a.replay_steps_completed)],
    ['실제 경과',seconds(lastData.elapsed_wall_s)+(lastData.elapsed_wall_is_live_estimate?' · 진행 추정':'')],
    ['시뮬레이션',seconds(a.simulation_steps/20)],['Actor 합계',seconds(a.actor_call_wall_s)],
    ['환경 요청 합계',seconds(a.environment_dispatch_wall_s)],
  ]));
  children.push(element('p',`진행 정보 확인 ${new Date(lastReceived).toLocaleTimeString()} · 물리 진행과 실제 대기 시간은 다릅니다.`,'muted'));
  children.push(element('h2','공식 평가'));
  children.push(element('p',`${value(score.raw_points)} / 50점`,'score'));
  children.push(facts([['착의 success',value(score.success)],['rate 상태',value(score.score_status)],['최종 rate',score.final_score == null?'미측정':`${score.final_score} points/s`],['평가 출처',score.source==='final_official_report'?'최종 공식 결과':score.source==='live_official_score_sample'?'실행 중 공식 표본':'아직 없음']]));
  children.push(element('p',`모델 시각 판단: ${value(response.visual_assessment)} · 공식 점수와 별도입니다.`,'warning'));
  if (response.reason) {
    children.push(element('h2','최근 모델 응답·행동 기록'));
    children.push(element('p',response.reason));
    children.push(element('p',`결정 ${latest.decision_index} · ${value(response.tool)} · 요청 ${value(response.steps)} step · 모델 입력 ${seconds(latest.observation_simulation_time_s)} · 실행 직전 ${seconds(latest.latest_observation_simulation_time_s)}`,'muted'));
    children.push(details('최종 행동 JSON',JSON.stringify(response,null,2)));
  }
  children.push(details('사용한 기본 프롬프트',lastData.prompt ?? '공개 검토가 필요한 내용이 있어 표시하지 않습니다.'));
  children.push(element('p','기본 요청문과 최종 행동 응답만 표시합니다. 단계는 모델 의도이며 실행 성공 라벨이 아닙니다.','muted'));
  children.push(element('h2','최근 결정 기록'));
  const history=element('ul');
  for (const item of [...recent].reverse()) history.append(element('li',`#${item.decision_index} ${stageNames[item.response.stage] || item.response.stage} · ${item.response.tool} · ${item.execution ? `${item.execution.actual_steps} step 기록`:'실행 응답 대기'}`));
  children.push(history,element('h2','기록 파일'));
  const files=element('ul');
  for (const file of lastData.files || []) files.append(element('li',`${file.path} · ${(file.bytes/1024).toFixed(1)} KiB`));
  children.push(files,element('p',`파일 완료: ${value(a.capture_complete)} · 학습 승인: 별도 검수 필요`,'muted'));
  const opened=new Set([...panel.querySelectorAll('details[open]')].map(n=>n.querySelector('summary').textContent));
  panel.replaceChildren(...children);
  for (const item of panel.querySelectorAll('details')) item.open=opened.has(item.querySelector('summary').textContent);
}

async function tick() {
  try {
    const response=await fetch('/api/progress',{cache:'no-store',signal:AbortSignal.timeout(3000)});
    if (!response.ok) throw Error('progress unavailable');
    lastData=await response.json();lastReceived=Date.now();transportError=false;
  } catch (_) { transportError=true; }
  const video=document.getElementById('remote-video');
  const frames=video?.getVideoPlaybackQuality?.().totalVideoFrames ?? null;
  frameIncrease=typeof frames==='number' && typeof lastFrames==='number' && frames>lastFrames;
  lastFrames=frames;lastFrameCheck=performance.now();
  render();
  if (lastData?.run_id) {
    try {
      await fetch('/api/viewer-metrics',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({run_id:lastData.run_id,sdk_connected:sdkConnected,total_video_frames:frames,
          video_width:video?.videoWidth || 0,video_height:video?.videoHeight || 0,page_visible:!document.hidden}),
        signal:AbortSignal.timeout(2000)});
    } catch (_) { /* Metrics never drive the simulator or hide the last status. */ }
  }
  setTimeout(tick,1000);
}
render();
void tick();
