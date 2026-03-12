#!/usr/bin/env pwsh

# 통합 선행 조건 확인 스크립트 (PowerShell)
#
# 이 스크립트는 명세 기반 개발(Spec-Driven Development) 워크플로우를 위한 통합된 선행 조건 확인을 제공합니다.
# 이전에 여러 스크립트에 흩어져 있던 기능을 대체합니다.
#
# 사용법: .\check-prerequisites.ps1 [옵션]
#
# 옵션:
#   -Json               JSON 형식으로 출력
#   -RequireTasks       tasks.md 파일 존재 필수 (구현 단계용)
#   -IncludeTasks       AVAILABLE_DOCS 목록에 tasks.md 포함
#   -PathsOnly          경로 변수만 출력 (검증 안 함)
#   -Help, -h          도움말 메시지 표시

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# 도움말 요청 시 표시
if ($Help) {
    Write-Output @"
사용법: .\check-prerequisites.ps1 [옵션]

명세 기반 개발 워크플로우를 위한 통합 선행 조건 확인 스크립트입니다.

옵션:
  -Json               JSON 형식으로 출력
  -RequireTasks       tasks.md 파일 존재 필수 (구현 단계용)
  -IncludeTasks       AVAILABLE_DOCS 목록에 tasks.md 포함
  -PathsOnly          경로 변수만 출력 (선행 조건 검증 안 함)
  -Help, -h          이 도움말 메시지 표시

예시:
  # 작업 선행 조건 확인 (plan.md 필요)
  .\check-prerequisites.ps1 -Json

  # 구현 선행 조건 확인 (plan.md + tasks.md 필요)
  .\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks

  # 기능 경로만 가져오기 (검증 안 함)
  .\check-prerequisites.ps1 -PathsOnly

"@
    exit 0
}

# 공통 함수 로드
. "$PSScriptRoot/common.ps1"

# 기능 경로 가져오기 및 브랜치 검증
$paths = Get-FeaturePathsEnv

if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) {
    exit 1
}

# 경로 전용 모드인 경우 경로 출력 후 종료 (JSON과 경로 전용 조합 지원)
if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT    = $paths.REPO_ROOT
            BRANCH       = $paths.CURRENT_BRANCH
            FEATURE_DIR  = $paths.FEATURE_DIR
            FEATURE_SPEC = $paths.FEATURE_SPEC
            IMPL_PLAN    = $paths.IMPL_PLAN
            TASKS        = $paths.TASKS
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
        Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
        Write-Output "TASKS: $($paths.TASKS)"
    }
    exit 0
}

# 필수 디렉토리 및 파일 검증
if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Write-Output "에러: 기능 디렉토리를 찾을 수 없습니다: $($paths.FEATURE_DIR)"
    Write-Output "/speckit.specify를 먼저 실행하여 기능 구조를 생성하십시오."
    exit 1
}

if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
    Write-Output "에러: $($paths.FEATURE_DIR)에서 plan.md를 찾을 수 없습니다."
    Write-Output "/speckit.plan을 먼저 실행하여 구현 계획을 생성하십시오."
    exit 1
}

# 필요한 경우 tasks.md 확인
if ($RequireTasks -and -not (Test-Path $paths.TASKS -PathType Leaf)) {
    Write-Output "에러: $($paths.FEATURE_DIR)에서 tasks.md를 찾을 수 없습니다."
    Write-Output "/speckit.tasks를 먼저 실행하여 작업 목록을 생성하십시오."
    exit 1
}

# 사용 가능한 문서 목록 빌드
$docs = @()

# 선택적 문서들 확인
if (Test-Path $paths.RESEARCH) { $docs += 'research.md' }
if (Test-Path $paths.DATA_MODEL) { $docs += 'data-model.md' }

# contracts 디렉토리 확인 (존재하고 파일이 있는 경우에만)
if ((Test-Path $paths.CONTRACTS_DIR) -and (Get-ChildItem -Path $paths.CONTRACTS_DIR -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    $docs += 'contracts/'
}

if (Test-Path $paths.QUICKSTART) { $docs += 'quickstart.md' }

# 요청된 경우 tasks.md 포함
if ($IncludeTasks -and (Test-Path $paths.TASKS)) {
    $docs += 'tasks.md'
}

# 결과 출력
if ($Json) {
    # JSON 출력
    [PSCustomObject]@{
        FEATURE_DIR = $paths.FEATURE_DIR
        AVAILABLE_DOCS = $docs
    } | ConvertTo-Json -Compress
} else {
    # 텍스트 출력
    Write-Output "FEATURE_DIR:$($paths.FEATURE_DIR)"
    Write-Output "AVAILABLE_DOCS:"

    # 각 잠재적 문서의 상태 표시
    Test-FileExists -Path $paths.RESEARCH -Description 'research.md' | Out-Null
    Test-FileExists -Path $paths.DATA_MODEL -Description 'data-model.md' | Out-Null
    Test-DirHasFiles -Path $paths.CONTRACTS_DIR -Description 'contracts/' | Out-Null
    Test-FileExists -Path $paths.QUICKSTART -Description 'quickstart.md' | Out-Null

    if ($IncludeTasks) {
        Test-FileExists -Path $paths.TASKS -Description 'tasks.md' | Out-Null
    }
}
