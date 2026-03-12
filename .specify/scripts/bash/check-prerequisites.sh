#!/usr/bin/env bash

# 통합 선행 조건 확인 스크립트
#
# 이 스크립트는 명세 기반 개발(Spec-Driven Development) 워크플로우를 위한 통합된 선행 조건 확인을 제공합니다.
# 이전에 여러 스크립트에 흩어져 있던 기능을 대체합니다.
#
# 사용법: ./check-prerequisites.sh [옵션]
#
# 옵션:
#   --json              JSON 형식으로 출력
#   --require-tasks     tasks.md 파일 존재 필수 (구현 단계용)
#   --include-tasks     AVAILABLE_DOCS 목록에 tasks.md 포함
#   --paths-only        경로 변수만 출력 (검증 안 함)
#   --help, -h          도움말 메시지 표시
#
# 출력:
#   JSON 모드: {"FEATURE_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   텍스트 모드: FEATURE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   경로 전용: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... 등

set -e

# 명령줄 인수 파싱
JSON_MODE=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            ;;
        --include-tasks)
            INCLUDE_TASKS=true
            ;;
        --paths-only)
            PATHS_ONLY=true
            ;;
        --help|-h)
            cat << 'EOF'
사용법: check-prerequisites.sh [옵션]

명세 기반 개발 워크플로우를 위한 통합 선행 조건 확인 스크립트입니다.

옵션:
  --json              JSON 형식으로 출력
  --require-tasks     tasks.md 파일 존재 필수 (구현 단계용)
  --include-tasks     AVAILABLE_DOCS 목록에 tasks.md 포함
  --paths-only        경로 변수만 출력 (선행 조건 검증 안 함)
  --help, -h          이 도움말 메시지 표시

예시:
  # 작업 선행 조건 확인 (plan.md 필요)
  ./check-prerequisites.sh --json

  # 구현 선행 조건 확인 (plan.md + tasks.md 필요)
  ./check-prerequisites.sh --json --require-tasks --include-tasks

  # 기능 경로만 가져오기 (검증 안 함)
  ./check-prerequisites.sh --paths-only

EOF
            exit 0
            ;;
        *)
            echo "에러: 알 수 없는 옵션 '$arg'. --help를 사용하여 사용법을 확인하십시오." >&2
            exit 1
            ;;
    esac
done

# 공통 함수 로드
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 기능 경로 가져오기 및 브랜치 검증
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# 경로 전용 모드인 경우 경로 출력 후 종료 (JSON과 경로 전용 조합 지원)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # 최소한의 JSON 경로 데이터 (검증 수행 안 함)
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","FEATURE_DIR":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$FEATURE_DIR" "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "FEATURE_DIR: $FEATURE_DIR"
        echo "FEATURE_SPEC: $FEATURE_SPEC"
        echo "IMPL_PLAN: $IMPL_PLAN"
        echo "TASKS: $TASKS"
    fi
    exit 0
fi

# 필수 디렉토리 및 파일 검증
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "에러: 기능 디렉토리를 찾을 수 없습니다: $FEATURE_DIR" >&2
    echo "/speckit.specify를 먼저 실행하여 기능 구조를 생성하십시오." >&2
    exit 1
fi

if [[ ! -f "$IMPL_PLAN" ]]; then
    echo "에러: $FEATURE_DIR에서 plan.md를 찾을 수 없습니다." >&2
    echo "/speckit.plan을 먼저 실행하여 구현 계획을 생성하십시오." >&2
    exit 1
fi

# 필요한 경우 tasks.md 확인
if $REQUIRE_TASKS && [[ ! -f "$TASKS" ]]; then
    echo "에러: $FEATURE_DIR에서 tasks.md를 찾을 수 없습니다." >&2
    echo "/speckit.tasks를 먼저 실행하여 작업 목록을 생성하십시오." >&2
    exit 1
fi

# 사용 가능한 문서 목록 빌드
docs=()

# 선택적 문서들 확인
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")

# contracts 디렉토리 확인 (존재하고 파일이 있는 경우에만)
if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi

[[ -f "$QUICKSTART" ]] && docs+=("quickstart.md")

# 요청된 경우 tasks.md 포함
if $INCLUDE_TASKS && [[ -f "$TASKS" ]]; then
    docs+=("tasks.md")
fi

# 결과 출력
if $JSON_MODE; then
    # 문서의 JSON 배열 생성
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi

    printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$FEATURE_DIR" "$json_docs"
else
    # 텍스트 출력
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "AVAILABLE_DOCS:"

    # 각 잠재적 문서의 상태 표시
    check_file "$RESEARCH" "research.md"
    check_file "$DATA_MODEL" "data-model.md"
    check_dir "$CONTRACTS_DIR" "contracts/"
    check_file "$QUICKSTART" "quickstart.md"

    if $INCLUDE_TASKS; then
        check_file "$TASKS" "tasks.md"
    fi
fi
