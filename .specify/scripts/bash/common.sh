#!/usr/bin/env bash
# 모든 스크립트에서 공통으로 사용하는 함수 및 변수

# 저장소 루트 디렉토리를 가져옵니다. (Git이 없는 경우 대비)
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Git 저장소가 아닌 경우 스크립트 위치를 기준으로 찾습니다.
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

# 현재 브랜치를 가져옵니다. (Git이 없는 경우 대비)
get_current_branch() {
    # 먼저 SPECIFY_FEATURE 환경 변수가 설정되어 있는지 확인합니다.
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # Git을 사용할 수 있는지 확인합니다.
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    # Git 저장소가 아닌 경우, 가장 최신의 기능(feature) 디렉토리를 찾습니다.
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/specs"

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done

        if [[ -n "$latest_feature" ]]; then
            echo "$latest_feature"
            return
        fi
    fi

    echo "main"  # 최종 기본값
}

# Git 사용 가능 여부를 확인합니다.
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

# 기능 브랜치 명명 규칙을 확인합니다.
check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    # Git 저장소가 아닌 경우 브랜치 이름을 강제할 수 없으므로 경고만 출력합니다.
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] 경고: Git 저장소를 감지하지 못했습니다. 브랜치 검증을 건너뜁니다." >&2
        return 0
    fi

    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "에러: 기능 브랜치가 아닙니다. 현재 브랜치: $branch" >&2
        echo "기능 브랜치 이름은 다음과 같아야 합니다: 001-기능-이름" >&2
        return 1
    fi

    return 0
}

get_feature_dir() { echo "$1/specs/$2"; }

# 정확한 브랜치 일치 대신 숫자 접두사로 기능 디렉토리를 찾습니다.
# 이를 통해 여러 브랜치에서 동일한 명세(spec)로 작업할 수 있습니다. (예: 004-버그-수정, 004-기능-추가)
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local specs_dir="$repo_root/specs"

    # 브랜치에서 숫자 접두사를 추출합니다. (예: "004-무언가"에서 "004")
    if [[ ! "$branch_name" =~ ^([0-9]{3})- ]]; then
        # 브랜치에 숫자 접두사가 없는 경우 정확한 일치로 돌아갑니다.
        echo "$specs_dir/$branch_name"
        return
    fi

    local prefix="${BASH_REMATCH[1]}"

    # specs/ 디렉토리에서 이 접두사로 시작하는 디렉토리를 찾습니다.
    local matches=()
    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/"$prefix"-*; do
            if [[ -d "$dir" ]]; then
                matches+=("$(basename "$dir")")
            fi
        done
    fi

    # 결과 처리
    if [[ ${#matches[@]} -eq 0 ]]; then
        # 일치하는 항목 없음 - 브랜치 이름 경로를 반환합니다. (나중에 명확한 에러와 함께 실패할 것입니다.)
        echo "$specs_dir/$branch_name"
    elif [[ ${#matches[@]} -eq 1 ]]; then
        # 정확히 하나의 일치 항목 발견 - 완벽합니다!
        echo "$specs_dir/${matches[0]}"
    else
        # 여러 개의 일치 항목 발견 - 명명 규칙을 잘 따랐다면 발생하지 않아야 합니다.
        echo "에러: 접두사 '$prefix'로 시작하는 명세 디렉토리가 여러 개 발견되었습니다: ${matches[*]}" >&2
        echo "숫자 접두사당 하나의 명세 디렉토리만 존재해야 합니다." >&2
        echo "$specs_dir/$branch_name"  # 스크립트 중단을 피하기 위해 무언가 반환합니다.
    fi
}

# 기능 관련 경로 정보를 가져옵니다.
get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    # 한 명세에 대해 여러 브랜치를 지원하기 위해 접두사 기반 조회를 사용합니다.
    local feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch")

    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
FEATURE_DIR='$feature_dir'
FEATURE_SPEC='$feature_dir/spec.md'
IMPL_PLAN='$feature_dir/plan.md'
TASKS='$feature_dir/tasks.md'
RESEARCH='$feature_dir/research.md'
DATA_MODEL='$feature_dir/data-model.md'
QUICKSTART='$feature_dir/quickstart.md'
CONTRACTS_DIR='$feature_dir/contracts'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
