#!/usr/bin/env bash

set -e

JSON_MODE=false
SHORT_NAME=""
BRANCH_NUMBER=""
ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --short-name)
            if [ $((i + 1)) -gt $# ]; then
                echo '에러: --short-name 옵션에 값이 필요합니다.' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
            # 다음 인수가 다른 옵션인지 확인
            if [[ "$next_arg" == --* ]]; then
                echo '에러: --short-name 옵션에 값이 필요합니다.' >&2
                exit 1
            fi
            SHORT_NAME="$next_arg"
            ;;
        --number)
            if [ $((i + 1)) -gt $# ]; then
                echo '에러: --number 옵션에 값이 필요합니다.' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
            if [[ "$next_arg" == --* ]]; then
                echo '에러: --number 옵션에 값이 필요합니다.' >&2
                exit 1
            fi
            BRANCH_NUMBER="$next_arg"
            ;;
        --help|-h)
            echo "사용법: $0 [--json] [--short-name <이름>] [--number N] <기능_설명>"
            echo ""
            echo "옵션:"
            echo "  --json              JSON 형식으로 출력"
            echo "  --short-name <이름> 브랜치에 사용할 커스텀 짧은 이름(2-4단어) 제공"
            echo "  --number N          브랜치 번호 수동 지정 (자동 감지보다 우선함)"
            echo "  --help, -h          이 도움말 메시지 표시"
            echo ""
            echo "예시:"
            echo "  $0 '사용자 인증 시스템 추가' --short-name 'user-auth'"
            echo "  $0 'API를 위한 OAuth2 연동 구현' --number 5"
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
    i=$((i + 1))
done

FEATURE_DESCRIPTION="${ARGS[*]}"
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "사용법: $0 [--json] [--short-name <이름>] [--number N] <기능_설명>" >&2
    exit 1
fi

# 공백 제거 및 설명이 비어 있지 않은지 확인
FEATURE_DESCRIPTION=$(echo "$FEATURE_DESCRIPTION" | xargs)
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "에러: 기능 설명은 비어 있거나 공백만 포함할 수 없습니다." >&2
    exit 1
fi

# 프로젝트 마커를 찾아 저장소 루트를 찾는 함수
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# specs 디렉토리에서 가장 높은 번호를 가져오는 함수
get_highest_from_specs() {
    local specs_dir="$1"
    local highest=0

    if [ -d "$specs_dir" ]; then
        for dir in "$specs_dir"/*; do
            [ -d "$dir" ] || continue
            dirname=$(basename "$dir")
            number=$(echo "$dirname" | grep -o '^[0-9]\+' || echo "0")
            number=$((10#$number))
            if [ "$number" -gt "$highest" ]; then
                highest=$number
            fi
        done
    fi

    echo "$highest"
}

# Git 브랜치에서 가장 높은 번호를 가져오는 함수
get_highest_from_branches() {
    local highest=0

    # 모든 브랜치(로컬 및 리모트) 가져오기
    branches=$(git branch -a 2>/dev/null || echo "")

    if [ -n "$branches" ]; then
        while IFS= read -r branch; do
            # 브랜치 이름 정리: 마커 및 리모트 접두사 제거
            clean_branch=$(echo "$branch" | sed 's/^[* ]*//; s|^remotes/[^/]*/||')

            # 브랜치가 ###-* 패턴과 일치하는 경우 번호 추출
            if echo "$clean_branch" | grep -q '^[0-9]\{3\}-'; then
                number=$(echo "$clean_branch" | grep -o '^[0-9]\{3\}' || echo "0")
                number=$((10#$number))
                if [ "$number" -gt "$highest" ]; then
                    highest=$number
                fi
            fi
        done <<< "$branches"
    fi

    echo "$highest"
}

# 기존 브랜치를 확인하고 다음 가용 번호를 반환하는 함수
check_existing_branches() {
    local specs_dir="$1"

    # 최신 브랜치 정보를 위해 fetch 수행 (리모트가 없는 경우 에러 무시)
    git fetch --all --prune 2>/dev/null || true

    # 모든 브랜치에서 가장 높은 번호 확인
    local highest_branch=$(get_highest_from_branches)

    # 모든 명세(specs)에서 가장 높은 번호 확인
    local highest_spec=$(get_highest_from_specs "$specs_dir")

    # 둘 중 최댓값 선택
    local max_num=$highest_branch
    if [ "$highest_spec" -gt "$max_num" ]; then
        max_num=$highest_spec
    fi

    # 다음 번호 반환
    echo $((max_num + 1))
}

# 브랜치 이름을 정리하고 포맷팅하는 함수
clean_branch_name() {
    local name="$1"
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# 저장소 루트 해결. Git 정보 우선 사용, 없으면 프로젝트 마커 검색
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "에러: 저장소 루트를 결정할 수 없습니다. 저장소 내에서 이 스크립트를 실행하십시오." >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# 불용어(stop word) 필터링 및 길이 필터링을 포함한 브랜치 이름 생성 함수
generate_branch_name() {
    local description="$1"

    # 필터링할 일반적인 불용어
    local stop_words="^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$"

    # 소문자 변환 및 단어 분리
    local clean_name=$(echo "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/ /g')

    # 단어 필터링: 불용어 및 3자 미만 단어 제거 (원문에서 대문자 약어인 경우는 예외)
    local meaningful_words=()
    for word in $clean_name; do
        [ -z "$word" ] && continue

        # 불용어가 아니고 (길이가 3자 이상이거나 원문에서 대문자 약어인 경우) 유지
        if ! echo "$word" | grep -qiE "$stop_words"; then
            if [ ${#word} -ge 3 ]; then
                meaningful_words+=("$word")
            elif echo "$description" | grep -q "\b${word^^}\b"; then
                meaningful_words+=("$word")
            fi
        fi
    done

    # 유의미한 단어가 있는 경우 처음 3-4개 사용
    if [ ${#meaningful_words[@]} -gt 0 ]; then
        local max_words=3
        if [ ${#meaningful_words[@]} -eq 4 ]; then max_words=4; fi

        local result=""
        local count=0
        for word in "${meaningful_words[@]}"; do
            if [ $count -ge $max_words ]; then break; fi
            if [ -n "$result" ]; then result="$result-"; fi
            result="$result$word"
            count=$((count + 1))
        done
        echo "$result"
    else
        # 유의미한 단어를 찾지 못한 경우 기존 로직으로 회귀
        local cleaned=$(clean_branch_name "$description")
        echo "$cleaned" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//'
    fi
}

# 브랜치 이름 생성
if [ -n "$SHORT_NAME" ]; then
    # 제공된 짧은 이름 사용 및 정리
    BRANCH_SUFFIX=$(clean_branch_name "$SHORT_NAME")
else
    # 설명을 바탕으로 스마트 필터링을 거쳐 생성
    BRANCH_SUFFIX=$(generate_branch_name "$FEATURE_DESCRIPTION")
fi

# 브랜치 번호 결정
if [ -z "$BRANCH_NUMBER" ]; then
    if [ "$HAS_GIT" = true ]; then
        # 리모트의 기존 브랜치 확인
        BRANCH_NUMBER=$(check_existing_branches "$SPECS_DIR")
    else
        # 로컬 디렉토리 확인으로 회귀
        HIGHEST=$(get_highest_from_specs "$SPECS_DIR")
        BRANCH_NUMBER=$((HIGHEST + 1))
    fi
fi

# 8진수 변환 방지를 위해 10진수 해석 강제 (예: 010 → 8이 아닌 10으로 해석)
FEATURE_NUM=$(printf "%03d" "$((10#$BRANCH_NUMBER))")
BRANCH_NAME="${FEATURE_NUM}-${BRANCH_SUFFIX}"

# GitHub의 244바이트 브랜치 이름 제한 준수 및 필요시 절삭
MAX_BRANCH_LENGTH=244
if [ ${#BRANCH_NAME} -gt $MAX_BRANCH_LENGTH ]; then
    MAX_SUFFIX_LENGTH=$((MAX_BRANCH_LENGTH - 4))

    # 단어 경계에서 절삭 시도
    TRUNCATED_SUFFIX=$(echo "$BRANCH_SUFFIX" | cut -c1-$MAX_SUFFIX_LENGTH)
    TRUNCATED_SUFFIX=$(echo "$TRUNCATED_SUFFIX" | sed 's/-$//')

    ORIGINAL_BRANCH_NAME="$BRANCH_NAME"
    BRANCH_NAME="${FEATURE_NUM}-${TRUNCATED_SUFFIX}"

    >&2 echo "[specify] 경고: 브랜치 이름이 GitHub의 244바이트 제한을 초과했습니다."
    >&2 echo "[specify] 원본: $ORIGINAL_BRANCH_NAME (${#ORIGINAL_BRANCH_NAME} 바이트)"
    >&2 echo "[specify] 절삭됨: $BRANCH_NAME (${#BRANCH_NAME} 바이트)"
fi

if [ "$HAS_GIT" = true ]; then
    if ! git checkout -b "$BRANCH_NAME" 2>/dev/null; then
        # 브랜치 이미 존재 여부 확인
        if git branch --list "$BRANCH_NAME" | grep -q .; then
            >&2 echo "에러: 브랜치 '$BRANCH_NAME'이 이미 존재합니다. 다른 이름을 사용하거나 --number로 번호를 지정하십시오."
            exit 1
        else
            >&2 echo "에러: Git 브랜치 '$BRANCH_NAME' 생성에 실패했습니다. Git 설정을 확인하십시오."
            exit 1
        fi
    fi
else
    >&2 echo "[specify] 경고: Git 저장소를 감지하지 못했습니다. $BRANCH_NAME 에 대한 브랜치 생성을 건너뜁니다."
fi

FEATURE_DIR="$SPECS_DIR/$BRANCH_NAME"
mkdir -p "$FEATURE_DIR"

TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
SPEC_FILE="$FEATURE_DIR/spec.md"
if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

# 현재 세션에 대해 SPECIFY_FEATURE 환경 변수 설정
export SPECIFY_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE 환경 변수가 $BRANCH_NAME 으로 설정되었습니다."
fi
