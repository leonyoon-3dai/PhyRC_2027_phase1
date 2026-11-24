# Codex 설치 명령

Ubuntu 서버의 Bash 터미널에서 아래 명령을 실행합니다. 설치가 끝나면 작업할 저장소 디렉터리에서 `codex`를 실행합니다.

```bash
set -euo pipefail

echo "1/4 Ensuring Node.js and npm are installed"
if ! command -v node >/dev/null 2>&1 || ! node --version | grep -Eq '^v20\.'; then
  sudo apt-get update
  sudo apt-get install -y curl ca-certificates
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

echo "2/4 Installing Codex CLI with npm"
sudo npm install -g @openai/codex

echo "3/4 Verifying installation"
codex --version

echo "4/4 Starting Codex"
echo "Run this in any repository directory:"
echo "  codex"
```

PhyRC 시연에서 로봇 행동을 생성하는 격리 actor는 새 서버 준비 문서의 고정 CLI 버전을 사용합니다. [모델과 영상 경로 확인](active/start.md#2-모델과-영상-경로-확인)

[메인 README](../README.md)
