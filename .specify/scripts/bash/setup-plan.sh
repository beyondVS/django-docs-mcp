#!/usr/bin/env bash

set -e

# 명령줄 인수 파싱
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "사용법: $0 [--json]"
            echo "  --json    결과를 JSON 형식으로 출력"
            echo "  --help    이 도움말 메시지 표시"
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# 스크립트 디렉토리 가져오기 및 공통 함수 로드
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 공통 함수로부터 모든 경로와 변수 가져오기
eval $(get_feature_paths)

# 적절한 기능 브랜치인지 확인 (Git 저장소인 경우에만)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# 기능 디렉토리 생성
mkdir -p "$FEATURE_DIR"

# 계획 템플릿이 존재하는 경우 복사
TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"
if [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$IMPL_PLAN"
    echo "계획 템플릿을 $IMPL_PLAN 으로 복사했습니다."
else
    echo "경고: $TEMPLATE 에서 계획 템플릿을 찾을 수 없습니다."
    # 템플릿이 없는 경우 기본 계획 파일 생성
    touch "$IMPL_PLAN"
fi

# 결과 출력
if $JSON_MODE; then
    printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
        "$FEATURE_SPEC" "$IMPL_PLAN" "$FEATURE_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi
