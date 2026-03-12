#!/usr/bin/env pwsh
# 새로운 기능 생성
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

# 도움말 요청 시 표시
if ($Help) {
    Write-Host "사용법: ./create-new-feature.ps1 [-Json] [-ShortName <이름>] [-Number N] <기능 설명>"
    Write-Host ""
    Write-Host "옵션:"
    Write-Host "  -Json               JSON 형식으로 출력"
    Write-Host "  -ShortName <이름>   브랜치에 사용할 커스텀 짧은 이름(2-4단어) 제공"
    Write-Host "  -Number N           브랜치 번호 수동 지정 (자동 감지보다 우선함)"
    Write-Host "  -Help               이 도움말 메시지 표시"
    Write-Host ""
    Write-Host "예시:"
    Write-Host "  ./create-new-feature.ps1 '사용자 인증 시스템 추가' -ShortName 'user-auth'"
    Write-Host "  ./create-new-feature.ps1 'API를 위한 OAuth2 연동 구현'"
    exit 0
}

# 기능 설명 제공 여부 확인
if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "사용법: ./create-new-feature.ps1 [-Json] [-ShortName <이름>] <기능 설명>"
    exit 1
}

$featureDesc = ($FeatureDescription -join ' ').Trim()

# 공백 제거 후 설명이 비어 있지 않은지 확인
if ([string]::IsNullOrWhiteSpace($featureDesc)) {
    Write-Error "에러: 기능 설명은 비어 있거나 공백만 포함할 수 없습니다."
    exit 1
}

# 프로젝트 마커를 찾아 저장소 루트를 찾는 함수
function Find-RepositoryRoot {
    param(
        [string]$StartDir,
        [string[]]$Markers = @('.git', '.specify')
    )
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in $Markers) {
            if (Test-Path (Join-Path $current $marker)) {
                return $current
            }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) {
            # 마커를 찾지 못하고 파일 시스템 루트에 도달
            return $null
        }
        $current = $parent
    }
}

function Get-HighestNumberFromSpecs {
    param([string]$SpecsDir)

    $highest = 0
    if (Test-Path $SpecsDir) {
        Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d+)') {
                $num = [int]$matches[1]
                if ($num -gt $highest) { $highest = $num }
            }
        }
    }
    return $highest
}

function Get-HighestNumberFromBranches {
    param()

    $highest = 0
    try {
        $branches = git branch -a 2>$null
        if ($LASTEXITCODE -eq 0) {
            foreach ($branch in $branches) {
                # 브랜치 이름 정리: 마커 및 리모트 접두사 제거
                $cleanBranch = $branch.Trim() -replace '^\*?\s+', '' -replace '^remotes/[^/]+/', ''

                # 브랜치가 ###-* 패턴과 일치하는 경우 번호 추출
                if ($cleanBranch -match '^(\d+)-') {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) { $highest = $num }
                }
            }
        }
    } catch {
        # Git 명령어 실패 시 0 반환
        Write-Verbose "Git 브랜치 확인 불가: $_"
    }
    return $highest
}

function Get-NextBranchNumber {
    param(
        [string]$SpecsDir
    )

    # 리모트 정보 fetch (에러 무시)
    try {
        git fetch --all --prune 2>$null | Out-Null
    } catch {
        # fetch 에러 무시
    }

    # 모든 브랜치에서 가장 높은 번호 확인
    $highestBranch = Get-HighestNumberFromBranches

    # 모든 명세(specs)에서 가장 높은 번호 확인
    $highestSpec = Get-HighestNumberFromSpecs -SpecsDir $SpecsDir

    # 둘 중 최댓값 선택
    $maxNum = [Math]::Max($highestBranch, $highestSpec)

    # 다음 번호 반환
    return $maxNum + 1
}

function ConvertTo-CleanBranchName {
    param([string]$Name)

    return $Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}

$fallbackRoot = (Find-RepositoryRoot -StartDir $PSScriptRoot)
if (-not $fallbackRoot) {
    Write-Error "에러: 저장소 루트를 결정할 수 없습니다. 저장소 내에서 이 스크립트를 실행하십시오."
    exit 1
}

try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $hasGit = $true
    } else {
        throw "Git 사용 불가"
    }
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

Set-Location $repoRoot

$specsDir = Join-Path $repoRoot 'specs'
New-Item -ItemType Directory -Path $specsDir -Force | Out-Null

# 불용어 필터링 및 길이 필터링을 포함한 브랜치 이름 생성 함수
function Get-BranchName {
    param([string]$Description)

    # 필터링할 일반적인 불용어
    $stopWords = @(
        'i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their',
        'want', 'need', 'add', 'get', 'set'
    )

    # 소문자 변환 및 단어 추출
    $cleanName = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $cleanName -split '\s+' | Where-Object { $_ }

    # 단어 필터링: 불용어 및 3자 미만 단어 제거
    $meaningfulWords = @()
    foreach ($word in $words) {
        if ($stopWords -contains $word) { continue }

        if ($word.Length -ge 3) {
            $meaningfulWords += $word
        } elseif ($Description -match "\b$($word.ToUpper())\b") {
            $meaningfulWords += $word
        }
    }

    # 유의미한 단어가 있는 경우 처음 3-4개 사용
    if ($meaningfulWords.Count -gt 0) {
        $maxWords = if ($meaningfulWords.Count -eq 4) { 4 } else { 3 }
        $result = ($meaningfulWords | Select-Object -First $maxWords) -join '-'
        return $result
    } else {
        # 유의미한 단어를 찾지 못한 경우 기존 로직으로 회귀
        $result = ConvertTo-CleanBranchName -Name $Description
        $fallbackWords = ($result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $fallbackWords)
    }
}

# 브랜치 이름 생성
if ($ShortName) {
    # 제공된 짧은 이름 사용 및 정리
    $branchSuffix = ConvertTo-CleanBranchName -Name $ShortName
} else {
    # 설명을 바탕으로 스마트 필터링을 거쳐 생성
    $branchSuffix = Get-BranchName -Description $featureDesc
}

# 브랜치 번호 결정
if ($Number -eq 0) {
    if ($hasGit) {
        # 리모트의 기존 브랜치 확인
        $Number = Get-NextBranchNumber -SpecsDir $specsDir
    } else {
        # 로컬 디렉토리 확인으로 회귀
        $Number = (Get-HighestNumberFromSpecs -SpecsDir $specsDir) + 1
    }
}

$featureNum = ('{0:000}' -f $Number)
$branchName = "$featureNum-$branchSuffix"

# GitHub의 244바이트 브랜치 이름 제한 준수 및 필요시 절삭
$maxBranchLength = 244
if ($branchName.Length -gt $maxBranchLength) {
    $maxSuffixLength = $maxBranchLength - 4

    # 절삭
    $truncatedSuffix = $branchSuffix.Substring(0, [Math]::Min($branchSuffix.Length, $maxSuffixLength))
    $truncatedSuffix = $truncatedSuffix -replace '-$', ''

    $originalBranchName = $branchName
    $branchName = "$featureNum-$truncatedSuffix"

    Write-Warning "[specify] 브랜치 이름이 GitHub의 244바이트 제한을 초과했습니다."
    Write-Warning "[specify] 원본: $originalBranchName ($($originalBranchName.Length) 바이트)"
    Write-Warning "[specify] 절삭됨: $branchName ($($branchName.Length) 바이트)"
}

if ($hasGit) {
    $branchCreated = $false
    try {
        git checkout -q -b $branchName 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $branchCreated = $true
        }
    } catch {
        # Git 명령어 실행 중 예외 발생
    }

    if (-not $branchCreated) {
        # 브랜치 이미 존재 여부 확인
        $existingBranch = git branch --list $branchName 2>$null
        if ($existingBranch) {
            Write-Error "에러: 브랜치 '$branchName'이 이미 존재합니다. 다른 이름을 사용하거나 -Number로 번호를 지정하십시오."
            exit 1
        } else {
            Write-Error "에러: Git 브랜치 '$branchName' 생성에 실패했습니다. Git 설정을 확인하십시오."
            exit 1
        }
    }
} else {
    Write-Warning "[specify] 경고: Git 저장소를 감지하지 못했습니다. $branchName 에 대한 브랜치 생성을 건너뜁니다."
}

$featureDir = Join-Path $specsDir $branchName
New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

$template = Join-Path $repoRoot '.specify/templates/spec-template.md'
$specFile = Join-Path $featureDir 'spec.md'
if (Test-Path $template) {
    Copy-Item $template $specFile -Force
} else {
    New-Item -ItemType File -Path $specFile | Out-Null
}

# 현재 세션에 대해 SPECIFY_FEATURE 환경 변수 설정
$env:SPECIFY_FEATURE = $branchName

if ($Json) {
    $obj = [PSCustomObject]@{
        BRANCH_NAME = $branchName
        SPEC_FILE = $specFile
        FEATURE_NUM = $featureNum
        HAS_GIT = $hasGit
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "SPEC_FILE: $specFile"
    Write-Output "FEATURE_NUM: $featureNum"
    Write-Output "HAS_GIT: $hasGit"
    Write-Output "SPECIFY_FEATURE 환경 변수가 $branchName 으로 설정되었습니다."
}
