# Docktor

Docktor는 Dockerfile 정적 분석과 실제 이미지 빌드 결과를 함께 확인해 컨테이너 이미지의 품질을 점검하는 프로젝트입니다.  
배포 전에 Docker 이미지의 성능, 운영성, 보안 측면에서 확인이 필요한 요소를 진단하고, 더 나은 방향으로 개선할 수 있도록 돕는 것을 목표로 합니다.

## 기술 스택

- Python 3.12
- Typer
- Rich
- Docker CLI
- Trivy

## 프로젝트 실행 방법

### 1. 공통 권장 사항

- macOS와 Windows 모두 Python 3.12 사용을 권장합니다.
- 저장소 루트에서 가상환경을 만든 뒤 활성화합니다.
- 의존성은 가상환경 안에만 설치합니다.
- `--build` 또는 `--trivy` 옵션을 쓸 경우 각 OS에 Docker와 Trivy가 별도로 설치되어 있어야 합니다.

### 2. macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
python -m main analyze --file test/Dockerfile
```

설치 후에는 아래처럼 실행해도 됩니다.

```bash
docktor analyze --file test/Dockerfile
```

### 3. Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m main analyze --file test/Dockerfile
```

설치 후에는 아래 방식 중 하나로 실행합니다.

```powershell
python -m main analyze --file test/Dockerfile
docktor analyze --file test/Dockerfile
docktor.bat analyze --file test/Dockerfile
```

### 4. 왜 Windows에서 `docktor`가 바로 안 될 수 있는가

저장소의 [`docktor`](./docktor)는 shebang 기반 실행 파일이라 macOS/Linux에서는 자연스럽지만 Windows에서는 그대로 실행 파일로 인식되지 않을 수 있습니다.  
Windows에서는 아래 둘 중 하나로 실행하는 것을 권장합니다.

- `pip install -e .` 후 생성되는 `docktor` 엔트리포인트 사용
- `python -m main ...` 또는 `docktor.bat ...` 사용

### 5. 옵션별 요구 사항

- `analyze --file ...`: Python 의존성만 맞으면 실행 가능
- `--build`: Docker CLI 및 Docker Engine 필요
- `--trivy`: Trivy 설치 필요

### 6. 팀 공통 실행 규칙

- 둘 다 같은 Python 메이저/마이너 버전을 사용합니다.
- 둘 다 가상환경을 활성화한 상태에서 실행합니다.
- 둘 다 `pip install -e .` 또는 `pip install -r requirements.txt` 중 하나로 의존성을 맞춥니다.
- 가능하면 명령은 `python -m main ...` 형태로 통일합니다.
- Git 줄바꿈 차이를 줄이기 위해 저장소의 `.gitattributes` 설정을 유지합니다.

## 프로젝트 구조


## 프로젝트 작업 순서

본 프로젝트는 `main` 브랜치와 `develop` 브랜치를 분리하여 운영합니다.

- `main`: 최종 배포 및 제출 기준 브랜치
- `develop`: 기능 개발 내용을 통합하는 브랜치

작업은 아래 순서대로 진행합니다.

### 1. 이슈 발행

작업을 시작하기 전에 GitHub Issue를 먼저 생성합니다.

- 이슈 제목과 내용을 작성합니다.
- 하나의 이슈에는 하나의 작업만 담습니다.

### 2. 브랜치 분기

이슈를 만든 뒤에는 `develop` 브랜치에서 작업용 브랜치를 생성합니다.
브랜치 이름 규칙은 아래 컨벤션을 따릅니다.

```bash
cd Docktor
git checkout develop
git pull origin develop
git checkout -b feat/#1/changeLogin
```

### 3. 작업 진행

생성한 브랜치에서 실제 기능 개발 또는 수정을 진행합니다.

- 작업 중간중간 의미 있는 단위로 커밋합니다.
- 커밋 메시지는 아래 컨벤션을 따릅니다.
- 다른 사람의 작업 내용과 충돌하지 않도록 수시로 `git pull origin develop`을 실행하여 `develop` 브랜치의 변경 사항을 본인 브랜치에 반영합니다.

예시
```bash
git status
git add .
git commit -m "feat: 로그인 API 추가"
git pull origin develop
git push origin feat/#1/changeLogin
```

### 4. PR 발행

작업이 끝나면 본인 브랜치에서 `develop` 브랜치로 Pull Request를 생성합니다.

- PR 제목은 작업 내용을 한눈에 알 수 있게 작성합니다.
- PR 본문에는 어떤 작업을 했는지, 왜 수정했는지, 확인이 필요한 부분이 있는지 적습니다.
- 관련 이슈가 있다면 PR 본문에 함께 연결합니다.

### 5. 최소 1명의 팀원에게 코드 리뷰 받기

PR을 올린 뒤에는 최소 1명 이상의 팀원에게 코드 리뷰를 받아야 합니다.

- 리뷰어는 코드의 동작, 구조, 오타, 누락 사항 등을 확인합니다.
- 리뷰 의견이 달리면 작성자는 내용을 반영해 수정합니다.
- 수정 후 다시 커밋하고 PR에 반영합니다.

```bash
git add .
git commit -m "fix: 리뷰 반영하여 로그인 예외 처리 수정"
git push origin feat/#1/changeLogin
```

### 6. `develop` 브랜치에 머지

리뷰가 완료되면 PR을 `develop` 브랜치에 머지합니다.

- 리뷰 없이 바로 머지하지 않습니다.
- 충돌이 있다면 먼저 해결한 뒤 머지합니다.
- 모든 개발 작업은 우선 `develop` 브랜치에 반영됩니다.

### 7. 브랜치 삭제

머지가 완료되면 사용한 작업 브랜치는 삭제합니다.

```bash
git checkout develop
git pull origin develop
git branch -d feat/#1/changeLogin
git push origin --delete feat/#1/changeLogin
```

### 8. 이슈 닫기

작업이 정상적으로 머지되면 마지막으로 해당 이슈를 닫습니다.

- PR과 연결된 이슈가 있다면 함께 닫습니다.
- 작업이 끝난 이슈는 바로 정리합니다.

즉, 전체 작업 흐름은 아래와 같습니다.

```markdown
이슈 발행
→ 브랜치 분기
→ 작업 진행
→ PR 발행
→ 최소 1명 코드 리뷰
→ develop 브랜치 머지
→ 브랜치 삭제
→ 이슈 닫기
```

## 6. 컨벤션

### 커밋 메시지 형식

```markdown
<type>: <subject>
```

### Type 종류

| Type | 설명 | 예시 |
| --- | --- | --- |
| `feat` | 새로운 기능 추가 | `feat: 회원가입 API 추가` |
| `fix` | 버그 수정 | `fix: 토큰 만료 처리 수정` |
| `refactor` | 리팩토링 | `refactor: 서비스 로직 분리` |
| `docs` | 문서 수정 | `docs: README 업데이트` |
| `style` | 코드 포맷팅 | `style: 코드 포맷 정리` |
| `test` | 테스트 코드 | `test: 회원가입 테스트 추가` |
| `chore` | 빌드, 설정 변경 | `chore: requirements.txt 업데이트` |

### 커밋 메시지 규칙

- `subject`는 50자 이내로 작성합니다.
- 커밋 메시지는 한글로 작성합니다.
- 문장 끝에 마침표를 사용하지 않습니다.
- 명령문 형태로 작성합니다.
- 예시는 `추가`, `수정`, `삭제`처럼 동작이 드러나는 표현을 사용합니다.

### 커밋 메시지 예시

```bash
# 기능 추가
git commit -m "feat: 상품 검색 API 추가"

# 버그 수정
git commit -m "fix: 위시리스트 중복 등록 버그 수정"

# 리팩토링
git commit -m "refactor: 페이지네이션 로직 개선"
```

### 브랜치 전략

#### 브랜치 종류

| 브랜치 | 용도 | 네이밍 예시 |
| --- | --- | --- |
| `main` | 배포 브랜치 | - |
| `develop` | 개발 통합 브랜치 | - |
| `feat/*` | 기능 개발 | `feat/#1/changeLogin` |
| `fix/*` | 버그 수정 | `fix/login-error` |
| `hotfix/*` | 긴급 수정 | `hotfix/critical-bug` |

#### 브랜치 네이밍 규칙

브랜치는 아래 형식으로 작성합니다.

```markdown
feat/#이슈번호/간단한기능설명
```

예시

```markdown
feat/#1/changeLogin
fix/#3/loginError
hotfix/#7/criticalBug
```

브랜치명 작성 시 아래 규칙을 지킵니다.

- 작업 성격이 드러나는 prefix를 사용합니다.
- 이슈 번호를 포함합니다.
- 기능 설명은 영어로 짧게 작성합니다.
- 기능 설명은 가능하면 두 단어 이하로 작성합니다.

### 코드 컨벤션
- Python 코드는 [PEP 8](https://peps.python.org/pep-0008/)을 준수합니다.
- 변수명, 함수명은 소문자와 snake_case를 사용합니다.
- 클래스명은 PascalCase를 사용합니다.
- 들여쓰기는 공백 4칸을 사용합니다.
