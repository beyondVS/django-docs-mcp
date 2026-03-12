#!/usr/bin/env pwsh
# 기능을 위한 구현 계획 설정

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# 도움말 요청 시 표시
if ($Help) {
    Write-Output "사용법: ./setup-plan.ps1 [-Json] [-Help]"
    Write-Output "  -Json     결과를 JSON 형식으로 출력"
    Write-Output "  -Help     이 도움말 메시지 표시"
    exit 0
}

# 공통 함수 로드
. "$PSScriptRoot/common.ps1"

# 공통 함수로부터 모든 경로와 변수 가져오기
$paths = Get-FeaturePathsEnv

# 적절한 기능 브랜치인지 확인 (Git 저장소인 경우에만)
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit $paths.HAS_GIT)) {
    exit 1
}

# 기능 디렉토리 생성
New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null

# 계획 템플릿이 존재하는 경우 복사, 그렇지 않으면 빈 파일 생성
$template = Join-Path $paths.REPO_ROOT '.specify/templates/plan-template.md'
if (Test-Path $template) {
    Copy-Item $template $paths.IMPL_PLAN -Force
    Write-Output "계획 템플릿을 $($paths.IMPL_PLAN) 으로 복사했습니다."
} else {
    Write-Warning "$template 에서 계획 템플릿을 찾을 수 없습니다."
    # 템플릿이 없는 경우 기본 계획 파일 생성
    New-Item -ItemType File -Path $paths.IMPL_PLAN -Force | Out-Null
}

# 결과 출력
if ($Json) {
    $result = [PSCustomObject]@{
        FEATURE_SPEC = $paths.FEATURE_SPEC
        IMPL_PLAN = $paths.IMPL_PLAN
        SPECS_DIR = $paths.FEATURE_DIR
        BRANCH = $paths.CURRENT_BRANCH
        HAS_GIT = $paths.HAS_GIT
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
