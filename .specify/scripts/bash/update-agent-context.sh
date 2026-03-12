#!/usr/bin/env bash

# plan.md의 정보를 바탕으로 에이전트 컨텍스트 파일 업데이트
#
# 이 스크립트는 기능 명세를 파싱하여 프로젝트 정보로 에이전트별 설정 파일을
# 업데이트함으로써 AI 에이전트의 컨텍스트 파일을 유지 관리합니다.
#
# 주요 기능:
# 1. 환경 검증
#    - Git 저장소 구조 및 브랜치 정보 확인
#    - 필수 plan.md 파일 및 템플릿 존재 여부 확인
#    - 파일 권한 및 액세스 가능성 검증
#
# 2. 계획 데이터 추출
#    - plan.md 파일을 파싱하여 프로젝트 메타데이터 추출
#    - 언어/버전, 프레임워크, 데이터베이스 및 프로젝트 유형 식별
#    - 누락되거나 불완전한 명세 데이터를 유연하게 처리
#
# 3. 에이전트 파일 관리
#    - 필요한 경우 템플릿으로부터 새로운 에이전트 컨텍스트 파일 생성
#    - 기존 에이전트 파일을 새로운 프로젝트 정보로 업데이트
#    - 수동으로 추가된 내용 및 커스텀 설정 보존
#    - 여러 AI 에이전트 형식 및 디렉토리 구조 지원
#
# 4. 콘텐츠 생성
#    - 언어별 빌드/테스트 명령어 생성
#    - 적절한 프로젝트 디렉토리 구조 생성
#    - 기술 스택 및 최근 변경 사항 섹션 업데이트
#    - 일관된 포맷팅 및 타임스탬프 유지
#
# 5. 다중 에이전트 지원
#    - 에이전트별 파일 경로 및 명명 규칙 처리
#    - 지원 에이전트: Claude, Gemini, Copilot, Cursor, Qwen, opencode, Codex, Windsurf, Kilo Code, Auggie CLI, Roo Code, CodeBuddy CLI, Qoder CLI, Amp, SHAI, Tabnine CLI, Kiro CLI, Mistral Vibe, Kimi Code, Antigravity 또는 일반 에이전트
#    - 단일 에이전트 또는 모든 기존 에이전트 파일 업데이트 가능
#    - 에이전트 파일이 없는 경우 기본 Claude 파일 생성
#
# 사용법: ./update-agent-context.sh [에이전트_유형]
# 에이전트 유형: claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|roo|codebuddy|amp|shai|tabnine|kiro-cli|agy|bob|vibe|qodercli|kimi|generic
# 모든 기존 에이전트 파일을 업데이트하려면 비워두십시오.

set -e

# 엄격한 에러 처리 활성화
set -u
set -o pipefail

#==============================================================================
# 설정 및 전역 변수
#==============================================================================

# 스크립트 디렉토리 가져오기 및 공통 함수 로드
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 공통 함수로부터 모든 경로와 변수 가져오기
eval $(get_feature_paths)

NEW_PLAN="$IMPL_PLAN"  # 기존 코드와의 호환성을 위한 별칭
AGENT_TYPE="${1:-}"

# 에이전트별 파일 경로
CLAUDE_FILE="$REPO_ROOT/CLAUDE.md"
GEMINI_FILE="$REPO_ROOT/GEMINI.md"
COPILOT_FILE="$REPO_ROOT/.github/agents/copilot-instructions.md"
CURSOR_FILE="$REPO_ROOT/.cursor/rules/specify-rules.mdc"
QWEN_FILE="$REPO_ROOT/QWEN.md"
AGENTS_FILE="$REPO_ROOT/AGENTS.md"
WINDSURF_FILE="$REPO_ROOT/.windsurf/rules/specify-rules.md"
KILOCODE_FILE="$REPO_ROOT/.kilocode/rules/specify-rules.md"
AUGGIE_FILE="$REPO_ROOT/.augment/rules/specify-rules.md"
ROO_FILE="$REPO_ROOT/.roo/rules/specify-rules.md"
CODEBUDDY_FILE="$REPO_ROOT/CODEBUDDY.md"
QODER_FILE="$REPO_ROOT/QODER.md"
AMP_FILE="$REPO_ROOT/AGENTS.md"
SHAI_FILE="$REPO_ROOT/SHAI.md"
TABNINE_FILE="$REPO_ROOT/TABNINE.md"
KIRO_FILE="$REPO_ROOT/AGENTS.md"
AGY_FILE="$REPO_ROOT/.agent/rules/specify-rules.md"
BOB_FILE="$REPO_ROOT/AGENTS.md"
VIBE_FILE="$REPO_ROOT/.vibe/agents/specify-agents.md"
KIMI_FILE="$REPO_ROOT/KIMI.md"

# 템플릿 파일
TEMPLATE_FILE="$REPO_ROOT/.specify/templates/agent-file-template.md"

# 파싱된 계획 데이터를 위한 전역 변수
NEW_LANG=""
NEW_FRAMEWORK=""
NEW_DB=""
NEW_PROJECT_TYPE=""

#==============================================================================
# 유틸리티 함수
#==============================================================================

log_info() {
    echo "정보: $1"
}

log_success() {
    echo "✓ $1"
}

log_error() {
    echo "에러: $1" >&2
}

log_warning() {
    echo "경고: $1" >&2
}

# 임시 파일 정리를 위한 함수
cleanup() {
    local exit_code=$?
    rm -f /tmp/agent_update_*_$$
    rm -f /tmp/manual_additions_$$
    exit $exit_code
}

# 정리 트랩 설정
trap cleanup EXIT INT TERM

#==============================================================================
# 검증 함수
#==============================================================================

validate_environment() {
    # 현재 브랜치/기능 확인 (Git 유무 상관없이)
    if [[ -z "$CURRENT_BRANCH" ]]; then
        log_error "현재 기능을 확인할 수 없습니다."
        if [[ "$HAS_GIT" == "true" ]]; then
            log_info "기능 브랜치에 있는지 확인하십시오."
        else
            log_info "SPECIFY_FEATURE 환경 변수를 설정하거나 기능을 먼저 생성하십시오."
        fi
        exit 1
    fi

    # plan.md 존재 여부 확인
    if [[ ! -f "$NEW_PLAN" ]]; then
        log_error "$NEW_PLAN 에서 plan.md를 찾을 수 없습니다."
        log_info "해당하는 명세 디렉토리가 있는 기능에서 작업 중인지 확인하십시오."
        if [[ "$HAS_GIT" != "true" ]]; then
            log_info "사용법: export SPECIFY_FEATURE=기능-이름 또는 새 기능을 먼저 생성하십시오."
        fi
        exit 1
    fi

    # 템플릿 존재 여부 확인 (새 파일 생성 시 필요)
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log_warning "$TEMPLATE_FILE 에서 템플릿 파일을 찾을 수 없습니다."
        log_warning "새로운 에이전트 파일 생성이 실패할 수 있습니다."
    fi
}

#==============================================================================
# 계획서 파싱 함수
#==============================================================================

extract_plan_field() {
    local field_pattern="$1"
    local plan_file="$2"

    grep "^\*\*${field_pattern}\*\*: " "$plan_file" 2>/dev/null | \
        head -1 | \
        sed "s|^\*\*${field_pattern}\*\*: ||" | \
        sed 's/^[ \t]*//;s/[ \t]*$//' | \
        grep -v "확인 필요" | \
        grep -v "^N/A$" || echo ""
}

parse_plan_data() {
    local plan_file="$1"

    if [[ ! -f "$plan_file" ]]; then
        log_error "계획 파일을 찾을 수 없습니다: $plan_file"
        return 1
    fi

    if [[ ! -r "$plan_file" ]]; then
        log_error "계획 파일을 읽을 수 없습니다: $plan_file"
        return 1
    fi

    log_info "$plan_file 에서 계획 데이터를 파싱하는 중..."

    NEW_LANG=$(extract_plan_field "Language/Version" "$plan_file")
    NEW_FRAMEWORK=$(extract_plan_field "Primary Dependencies" "$plan_file")
    NEW_DB=$(extract_plan_field "Storage" "$plan_file")
    NEW_PROJECT_TYPE=$(extract_plan_field "Project Type" "$plan_file")

    # 발견된 내용 로깅
    if [[ -n "$NEW_LANG" ]]; then
        log_info "언어 확인됨: $NEW_LANG"
    else
        log_warning "계획서에서 언어 정보를 찾을 수 없습니다."
    fi

    if [[ -n "$NEW_FRAMEWORK" ]]; then
        log_info "프레임워크 확인됨: $NEW_FRAMEWORK"
    fi

    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]]; then
        log_info "데이터베이스 확인됨: $NEW_DB"
    fi

    if [[ -n "$NEW_PROJECT_TYPE" ]]; then
        log_info "프로젝트 유형 확인됨: $NEW_PROJECT_TYPE"
    fi
}

format_technology_stack() {
    local lang="$1"
    local framework="$2"
    local parts=()

    # 비어 있지 않은 부분 추가
    [[ -n "$lang" && "$lang" != "확인 필요" ]] && parts+=("$lang")
    [[ -n "$framework" && "$framework" != "확인 필요" && "$framework" != "N/A" ]] && parts+=("$framework")

    # 적절한 형식으로 결합
    if [[ ${#parts[@]} -eq 0 ]]; then
        echo ""
    elif [[ ${#parts[@]} -eq 1 ]]; then
        echo "${parts[0]}"
    else
        # 여러 부분을 " + "로 결합
        local result="${parts[0]}"
        for ((i=1; i<${#parts[@]}; i++)); do
            result="$result + ${parts[i]}"
        done
        echo "$result"
    fi
}

#==============================================================================
# 템플릿 및 콘텐츠 생성 함수
#==============================================================================

get_project_structure() {
    local project_type="$1"

    if [[ "$project_type" == *"web"* ]]; then
        echo "backend/\\nfrontend/\\ntests/"
    else
        echo "src/\\ntests/"
    fi
}

get_commands_for_language() {
    local lang="$1"

    case "$lang" in
        *"Python"*)
            echo "cd src && pytest && ruff check ."
            ;;
        *"Rust"*)
            echo "cargo test && cargo clippy"
            ;;
        *"JavaScript"*|*"TypeScript"*)
            echo "npm test \\&\\& npm run lint"
            ;;
        *)
            echo "# $lang 에 대한 명령어를 추가하십시오."
            ;;
    esac
}

get_language_conventions() {
    local lang="$1"
    echo "$lang: 표준 컨벤션을 따르십시오."
}

create_new_agent_file() {
    local target_file="$1"
    local temp_file="$2"
    local project_name="$3"
    local current_date="$4"

    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log_error "$TEMPLATE_FILE 에서 템플릿을 찾을 수 없습니다."
        return 1
    fi

    if [[ ! -r "$TEMPLATE_FILE" ]]; then
        log_error "템플릿 파일을 읽을 수 없습니다: $TEMPLATE_FILE"
        return 1
    fi

    log_info "템플릿으로부터 새로운 에이전트 컨텍스트 파일을 생성하는 중..."

    if ! cp "$TEMPLATE_FILE" "$temp_file"; then
        log_error "템플릿 파일 복사에 실패했습니다."
        return 1
    fi

    # 템플릿 플레이스홀더 교체
    local project_structure
    project_structure=$(get_project_structure "$NEW_PROJECT_TYPE")

    local commands
    commands=$(get_commands_for_language "$NEW_LANG")

    local language_conventions
    language_conventions=$(get_language_conventions "$NEW_LANG")

    # 안전한 접근 방식으로 에러 체킹과 함께 치환 수행
    local escaped_lang=$(printf '%s\n' "$NEW_LANG" | sed 's/[\[\.*^$()+{}|]/\\&/g')
    local escaped_framework=$(printf '%s\n' "$NEW_FRAMEWORK" | sed 's/[\[\.*^$()+{}|]/\\&/g')
    local escaped_branch=$(printf '%s\n' "$CURRENT_BRANCH" | sed 's/[\[\.*^$()+{}|]/\\&/g')

    # 기술 스택 및 최근 변경 사항 문자열 조건부 빌드
    local tech_stack
    if [[ -n "$escaped_lang" && -n "$escaped_framework" ]]; then
        tech_stack="- $escaped_lang + $escaped_framework ($escaped_branch)"
    elif [[ -n "$escaped_lang" ]]; then
        tech_stack="- $escaped_lang ($escaped_branch)"
    elif [[ -n "$escaped_framework" ]]; then
        tech_stack="- $escaped_framework ($escaped_branch)"
    else
        tech_stack="- ($escaped_branch)"
    fi

    local recent_change
    if [[ -n "$escaped_lang" && -n "$escaped_framework" ]]; then
        recent_change="- $escaped_branch: $escaped_lang + $escaped_framework 추가"
    elif [[ -n "$escaped_lang" ]]; then
        recent_change="- $escaped_branch: $escaped_lang 추가"
    elif [[ -n "$escaped_framework" ]]; then
        recent_change="- $escaped_branch: $escaped_framework 추가"
    else
        recent_change="- $escaped_branch: 추가"
    fi

    local substitutions=(
        "s|\[PROJECT NAME\]|$project_name|"
        "s|\[DATE\]|$current_date|"
        "s|\[EXTRACTED FROM ALL PLAN.MD FILES\]|$tech_stack|"
        "s|\[ACTUAL STRUCTURE FROM PLANS\]|$project_structure|g"
        "s|\[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES\]|$commands|"
        "s|\[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE\]|$language_conventions|"
        "s|\[LAST 3 FEATURES AND WHAT THEY ADDED\]|$recent_change|"
    )

    for substitution in "${substitutions[@]}"; do
        if ! sed -i.bak -e "$substitution" "$temp_file"; then
            log_error "치환 실패: $substitution"
            rm -f "$temp_file" "$temp_file.bak"
            return 1
        fi
    done

    # \n 시퀀스를 실제 줄바꿈으로 변환
    newline=$(printf '\n')
    sed -i.bak2 "s/\\\\n/${newline}/g" "$temp_file"

    # 백업 파일 정리
    rm -f "$temp_file.bak" "$temp_file.bak2"

    # .mdc 파일의 경우 규칙이 자동 포함되도록 Cursor 프런트매터 추가
    if [[ "$target_file" == *.mdc ]]; then
        local frontmatter_file
        frontmatter_file=$(mktemp) || return 1
        printf '%s\n' "---" "description: Project Development Guidelines" "globs: [\"**/*\"]" "alwaysApply: true" "---" "" > "$frontmatter_file"
        cat "$temp_file" >> "$frontmatter_file"
        mv "$frontmatter_file" "$temp_file"
    fi

    return 0
}

update_existing_agent_file() {
    local target_file="$1"
    local current_date="$2"

    log_info "기존 에이전트 컨텍스트 파일을 업데이트하는 중..."

    # 원자적 업데이트를 위해 단일 임시 파일 사용
    local temp_file
    temp_file=$(mktemp) || {
        log_error "임시 파일 생성에 실패했습니다."
        return 1
    }

    # 파일 프로세싱
    local tech_stack=$(format_technology_stack "$NEW_LANG" "$NEW_FRAMEWORK")
    local new_tech_entries=()
    local new_change_entry=""

    # 새로운 기술 항목 준비
    if [[ -n "$tech_stack" ]] && ! grep -q "$tech_stack" "$target_file"; then
        new_tech_entries+=("- $tech_stack ($CURRENT_BRANCH)")
    fi

    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]] && [[ "$NEW_DB" != "확인 필요" ]] && ! grep -q "$NEW_DB" "$target_file"; then
        new_tech_entries+=("- $NEW_DB ($CURRENT_BRANCH)")
    fi

    # 새로운 변경 항목 준비
    if [[ -n "$tech_stack" ]]; then
        new_change_entry="- $CURRENT_BRANCH: $tech_stack 추가"
    elif [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]] && [[ "$NEW_DB" != "확인 필요" ]]; then
        new_change_entry="- $CURRENT_BRANCH: $NEW_DB 추가"
    fi

    # 섹션 존재 여부 확인
    local has_active_technologies=0
    local has_recent_changes=0

    if grep -q "^## Active Technologies" "$target_file" 2>/dev/null; then
        has_active_technologies=1
    fi

    if grep -q "^## Recent Changes" "$target_file" 2>/dev/null; then
        has_recent_changes=1
    fi

    # 파일 한 줄씩 처리
    local in_tech_section=false
    local in_changes_section=false
    local tech_entries_added=false
    local changes_entries_added=false
    local existing_changes_count=0

    while IFS= read -r line || [[ -n "$line" ]]; do
        # 활성 기술 섹션 처리
        if [[ "$line" == "## Active Technologies" ]]; then
            echo "$line" >> "$temp_file"
            in_tech_section=true
            continue
        elif [[ $in_tech_section == true ]] && [[ "$line" =~ ^##[[:space:]] ]]; then
            # 섹션 닫기 전에 새 기술 항목 추가
            if [[ $tech_entries_added == false ]] && [[ ${#new_tech_entries[@]} -gt 0 ]]; then
                printf '%s\n' "${new_tech_entries[@]}" >> "$temp_file"
                tech_entries_added=true
            fi
            echo "$line" >> "$temp_file"
            in_tech_section=false
            continue
        elif [[ $in_tech_section == true ]] && [[ -z "$line" ]]; then
            # 기술 섹션의 빈 줄 앞에 새 기술 항목 추가
            if [[ $tech_entries_added == false ]] && [[ ${#new_tech_entries[@]} -gt 0 ]]; then
                printf '%s\n' "${new_tech_entries[@]}" >> "$temp_file"
                tech_entries_added=true
            fi
            echo "$line" >> "$temp_file"
            continue
        fi

        # 최근 변경 사항 섹션 처리
        if [[ "$line" == "## Recent Changes" ]]; then
            echo "$line" >> "$temp_file"
            # 제목 바로 뒤에 새 변경 항목 추가
            if [[ -n "$new_change_entry" ]]; then
                echo "$new_change_entry" >> "$temp_file"
            fi
            in_changes_section=true
            changes_entries_added=true
            continue
        elif [[ $in_changes_section == true ]] && [[ "$line" =~ ^##[[:space:]] ]]; then
            echo "$line" >> "$temp_file"
            in_changes_section=false
            continue
        elif [[ $in_changes_section == true ]] && [[ "$line" == "- "* ]]; then
            # 기존 변경 사항은 2개까지만 유지
            if [[ $existing_changes_count -lt 2 ]]; then
                echo "$line" >> "$temp_file"
                ((existing_changes_count++))
            fi
            continue
        fi

        # 타임스탬프 업데이트
        if [[ "$line" =~ \*\*최종\ 업데이트\*\*:.*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] ]] || [[ "$line" =~ \*\*Last\ updated\*\*:.*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] ]]; then
            echo "$line" | sed "s/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/$current_date/" >> "$temp_file"
        else
            echo "$line" >> "$temp_file"
        fi
    done < "$target_file"

    # 루프 종료 후 체크: 활성 기술 섹션에 있고 아직 추가 안 된 경우
    if [[ $in_tech_section == true ]] && [[ $tech_entries_added == false ]] && [[ ${#new_tech_entries[@]} -gt 0 ]]; then
        printf '%s\n' "${new_tech_entries[@]}" >> "$temp_file"
        tech_entries_added=true
    fi

    # 섹션이 없는 경우 파일 끝에 추가
    if [[ $has_active_technologies -eq 0 ]] && [[ ${#new_tech_entries[@]} -gt 0 ]]; then
        echo "" >> "$temp_file"
        echo "## Active Technologies" >> "$temp_file"
        printf '%s\n' "${new_tech_entries[@]}" >> "$temp_file"
        tech_entries_added=true
    fi

    if [[ $has_recent_changes -eq 0 ]] && [[ -n "$new_change_entry" ]]; then
        echo "" >> "$temp_file"
        echo "## Recent Changes" >> "$temp_file"
        echo "$new_change_entry" >> "$temp_file"
        changes_entries_added=true
    fi

    # Cursor .mdc 파일에 프런트매터 확인
    if [[ "$target_file" == *.mdc ]]; then
        if ! head -1 "$temp_file" | grep -q '^---'; then
            local frontmatter_file
            frontmatter_file=$(mktemp) || { rm -f "$temp_file"; return 1; }
            printf '%s\n' "---" "description: Project Development Guidelines" "globs: [\"**/*\"]" "alwaysApply: true" "---" "" > "$frontmatter_file"
            cat "$temp_file" >> "$frontmatter_file"
            mv "$frontmatter_file" "$temp_file"
        fi
    fi

    # 임시 파일을 대상 파일로 이동
    if ! mv "$temp_file" "$target_file"; then
        log_error "대상 파일 업데이트에 실패했습니다."
        rm -f "$temp_file"
        return 1
    fi

    return 0
}

#==============================================================================
# 메인 에이전트 파일 업데이트 함수
#==============================================================================

update_agent_file() {
    local target_file="$1"
    local agent_name="$2"

    if [[ -z "$target_file" ]] || [[ -z "$agent_name" ]]; then
        log_error "update_agent_file 함수에 target_file과 agent_name 매개변수가 필요합니다."
        return 1
    fi

    log_info "$agent_name 컨텍스트 파일 업데이트 중: $target_file"

    local project_name
    project_name=$(basename "$REPO_ROOT")
    local current_date
    current_date=$(date +%Y-%m-%d)

    # 디렉토리가 없으면 생성
    local target_dir
    target_dir=$(dirname "$target_file")
    if [[ ! -d "$target_dir" ]]; then
        if ! mkdir -p "$target_dir"; then
            log_error "디렉토리 생성 실패: $target_dir"
            return 1
        fi
    fi

    if [[ ! -f "$target_file" ]]; then
        # 템플릿으로부터 새 파일 생성
        local temp_file
        temp_file=$(mktemp) || {
            log_error "임시 파일 생성 실패"
            return 1
        }

        if create_new_agent_file "$target_file" "$temp_file" "$project_name" "$current_date"; then
            if mv "$temp_file" "$target_file"; then
                log_success "새로운 $agent_name 컨텍스트 파일을 생성했습니다."
            else
                log_error "임시 파일을 $target_file 로 이동하지 못했습니다."
                rm -f "$temp_file"
                return 1
            fi
        else
            log_error "새로운 에이전트 파일 생성 실패"
            rm -f "$temp_file"
            return 1
        fi
    else
        # 기존 파일 업데이트
        if [[ ! -r "$target_file" ]]; then
            log_error "기존 파일을 읽을 수 없습니다: $target_file"
            return 1
        fi

        if [[ ! -w "$target_file" ]]; then
            log_error "기존 파일에 쓸 수 없습니다: $target_file"
            return 1
        fi

        if update_existing_agent_file "$target_file" "$current_date"; then
            log_success "기존 $agent_name 컨텍스트 파일을 업데이트했습니다."
        else
            log_error "기존 에이전트 파일 업데이트 실패"
            return 1
        fi
    fi

    return 0
}

#==============================================================================
# 에이전트 선택 및 프로세싱
#==============================================================================

update_specific_agent() {
    local agent_type="$1"

    case "$agent_type" in
        claude)
            update_agent_file "$CLAUDE_FILE" "Claude Code"
            ;;
        gemini)
            update_agent_file "$GEMINI_FILE" "Gemini CLI"
            ;;
        copilot)
            update_agent_file "$COPILOT_FILE" "GitHub Copilot"
            ;;
        cursor-agent)
            update_agent_file "$CURSOR_FILE" "Cursor IDE"
            ;;
        qwen)
            update_agent_file "$QWEN_FILE" "Qwen Code"
            ;;
        opencode)
            update_agent_file "$AGENTS_FILE" "opencode"
            ;;
        codex)
            update_agent_file "$AGENTS_FILE" "Codex CLI"
            ;;
        windsurf)
            update_agent_file "$WINDSURF_FILE" "Windsurf"
            ;;
        kilocode)
            update_agent_file "$KILOCODE_FILE" "Kilo Code"
            ;;
        auggie)
            update_agent_file "$AUGGIE_FILE" "Auggie CLI"
            ;;
        roo)
            update_agent_file "$ROO_FILE" "Roo Code"
            ;;
        codebuddy)
            update_agent_file "$CODEBUDDY_FILE" "CodeBuddy CLI"
            ;;
        qodercli)
            update_agent_file "$QODER_FILE" "Qoder CLI"
            ;;
        amp)
            update_agent_file "$AMP_FILE" "Amp"
            ;;
        shai)
            update_agent_file "$SHAI_FILE" "SHAI"
            ;;
        tabnine)
            update_agent_file "$TABNINE_FILE" "Tabnine CLI"
            ;;
        kiro-cli)
            update_agent_file "$KIRO_FILE" "Kiro CLI"
            ;;
        agy)
            update_agent_file "$AGY_FILE" "Antigravity"
            ;;
        bob)
            update_agent_file "$BOB_FILE" "IBM Bob"
            ;;
        vibe)
            update_agent_file "$VIBE_FILE" "Mistral Vibe"
            ;;
        kimi)
            update_agent_file "$KIMI_FILE" "Kimi Code"
            ;;
        generic)
            log_info "일반 에이전트: 미리 정의된 컨텍스트 파일이 없습니다."
            ;;
        *)
            log_error "알 수 없는 에이전트 유형 '$agent_type'"
            log_error "기대 유형: claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|roo|codebuddy|amp|shai|tabnine|kiro-cli|agy|bob|vibe|qodercli|kimi|generic"
            exit 1
            ;;
    esac
}

update_all_existing_agents() {
    local found_agent=false

    # 가능한 모든 에이전트 파일 확인 및 존재하는 경우 업데이트
    if [[ -f "$CLAUDE_FILE" ]]; then
        update_agent_file "$CLAUDE_FILE" "Claude Code"
        found_agent=true
    fi

    if [[ -f "$GEMINI_FILE" ]]; then
        update_agent_file "$GEMINI_FILE" "Gemini CLI"
        found_agent=true
    fi

    if [[ -f "$COPILOT_FILE" ]]; then
        update_agent_file "$COPILOT_FILE" "GitHub Copilot"
        found_agent=true
    fi

    if [[ -f "$CURSOR_FILE" ]]; then
        update_agent_file "$CURSOR_FILE" "Cursor IDE"
        found_agent=true
    fi

    if [[ -f "$QWEN_FILE" ]]; then
        update_agent_file "$QWEN_FILE" "Qwen Code"
        found_agent=true
    fi

    if [[ -f "$AGENTS_FILE" ]]; then
        update_agent_file "$AGENTS_FILE" "Codex/opencode"
        found_agent=true
    fi

    if [[ -f "$WINDSURF_FILE" ]]; then
        update_agent_file "$WINDSURF_FILE" "Windsurf"
        found_agent=true
    fi

    if [[ -f "$KILOCODE_FILE" ]]; then
        update_agent_file "$KILOCODE_FILE" "Kilo Code"
        found_agent=true
    fi

    if [[ -f "$AUGGIE_FILE" ]]; then
        update_agent_file "$AUGGIE_FILE" "Auggie CLI"
        found_agent=true
    fi

    if [[ -f "$ROO_FILE" ]]; then
        update_agent_file "$ROO_FILE" "Roo Code"
        found_agent=true
    fi

    if [[ -f "$CODEBUDDY_FILE" ]]; then
        update_agent_file "$CODEBUDDY_FILE" "CodeBuddy CLI"
        found_agent=true
    fi

    if [[ -f "$SHAI_FILE" ]]; then
        update_agent_file "$SHAI_FILE" "SHAI"
        found_agent=true
    fi

    if [[ -f "$TABNINE_FILE" ]]; then
        update_agent_file "$TABNINE_FILE" "Tabnine CLI"
        found_agent=true
    fi

    if [[ -f "$QODER_FILE" ]]; then
        update_agent_file "$QODER_FILE" "Qoder CLI"
        found_agent=true
    fi

    if [[ -f "$KIRO_FILE" ]]; then
        update_agent_file "$KIRO_FILE" "Kiro CLI"
        found_agent=true
    fi

    if [[ -f "$AGY_FILE" ]]; then
        update_agent_file "$AGY_FILE" "Antigravity"
        found_agent=true
    fi
    if [[ -f "$BOB_FILE" ]]; then
        update_agent_file "$BOB_FILE" "IBM Bob"
        found_agent=true
    fi

    if [[ -f "$VIBE_FILE" ]]; then
        update_agent_file "$VIBE_FILE" "Mistral Vibe"
        found_agent=true
    fi

    if [[ -f "$KIMI_FILE" ]]; then
        update_agent_file "$KIMI_FILE" "Kimi Code"
        found_agent=true
    fi

    # 에이전트 파일이 하나도 없으면 기본 Claude 파일 생성
    if [[ "$found_agent" == false ]]; then
        log_info "기존 에이전트 파일을 찾을 수 없습니다. 기본 Claude 파일을 생성합니다..."
        update_agent_file "$CLAUDE_FILE" "Claude Code"
    fi
}

print_summary() {
    echo
    log_info "변경 사항 요약:"

    if [[ -n "$NEW_LANG" ]]; then
        echo "  - 언어 추가: $NEW_LANG"
    fi

    if [[ -n "$NEW_FRAMEWORK" ]]; then
        echo "  - 프레임워크 추가: $NEW_FRAMEWORK"
    fi

    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]]; then
        echo "  - 데이터베이스 추가: $NEW_DB"
    fi

    echo
    log_info "사용법: $0 [claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|roo|codebuddy|amp|shai|tabnine|kiro-cli|agy|bob|vibe|qodercli|kimi|generic]"
}

#==============================================================================
# 메인 실행
#==============================================================================

main() {
    # 실행 전 환경 검증
    validate_environment

    log_info "=== 기능 $CURRENT_BRANCH 에 대한 에이전트 컨텍스트 파일 업데이트 중 ==="

    # 계획 파일을 파싱하여 프로젝트 정보 추출
    if ! parse_plan_data "$NEW_PLAN"; then
        log_error "계획 데이터 파싱 실패"
        exit 1
    fi

    # 에이전트 유형 인수에 따라 처리
    local success=true

    if [[ -z "$AGENT_TYPE" ]]; then
        # 특정 에이전트가 지정되지 않은 경우 - 모든 기존 에이전트 파일 업데이트
        log_info "에이전트가 지정되지 않았습니다. 모든 기존 에이전트 파일을 업데이트합니다..."
        if ! update_all_existing_agents; then
            success=false
        fi
    else
        # 특정 에이전트가 지정된 경우 - 해당 에이전트만 업데이트
        log_info "특정 에이전트 업데이트: $AGENT_TYPE"
        if ! update_specific_agent "$AGENT_TYPE"; then
            success=false
        fi
    fi

    # 요약 출력
    print_summary

    if [[ "$success" == true ]]; then
        log_success "에이전트 컨텍스트 업데이트가 성공적으로 완료되었습니다."
        exit 0
    else
        log_error "에이전트 컨텍스트 업데이트가 에러와 함께 완료되었습니다."
        exit 1
    fi
}

# 스크립트가 직접 실행되는 경우 메인 함수 호출
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
