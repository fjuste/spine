#Requires -Version 5.1
<#
.SYNOPSIS
    Spine - Windows vendor-mode installer (PowerShell, no symlinks).

.DESCRIPTION
    Copies the Spine directory into PROJECT_ROOT\.spine as real files (the
    nested .git is never copied) and materializes the IDE trees (.agents,
    .cursor, .opencode, .claude) as real files so they can be committed.

    PowerShell port of scripts/install-vendor.sh. Both installers share the
    .spine-vendor marker, so a project installed by one can be updated by the
    other. No Bash, Python, symlink privilege, or Developer Mode is required.

.PARAMETER ProjectRoot
    Destination consumer project directory (required; prompted when omitted).

.PARAMETER SpineDir
    Spine source directory. Defaults to the directory containing this script.
    Required with -Update (the source must differ from the vendored .spine).

.PARAMETER Update
    Overwrite vendored trees from -SpineDir and prune deselected skills.

.PARAMETER Uninstall
    Remove .spine-vendor, .spine and materialized IDE trees (keeps docs\ and
    opencode.json).

.PARAMETER Force
    Convert an existing symlink-mode install (removes links before copying).

.PARAMETER DryRun
    Preview without making changes.

.PARAMETER Core
    Install core skills only (alias for -Skills core).

.PARAMETER Skills
    Skill selection: all (default), core, or a comma-separated list.

.PARAMETER Targets
    Comma-separated targets: cursor,opencode,claude,antigravity (default: all).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\tools\spine\install.ps1 -ProjectRoot C:\dev\my-project

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\dev\my-project\.spine\install.ps1 -Update -ProjectRoot C:\dev\my-project -SpineDir C:\tools\spine

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\dev\my-project\.spine\install.ps1 -Uninstall -ProjectRoot C:\dev\my-project
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, HelpMessage = 'Destination project directory (e.g. C:\dev\my-project)')]
    [string]$ProjectRoot,
    [string]$SpineDir = '',
    [switch]$Update,
    [switch]$Uninstall,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Core,
    [string[]]$Skills = @(),
    [string[]]$Targets = @('cursor', 'opencode', 'claude', 'antigravity')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# =============================================================================
# Constants
# =============================================================================

$CORE_SKILLS = @(
    'writing-plans',
    'executing-plans',
    'test-driven-development',
    'systematic-debugging',
    'verification-before-completion'
)

$CORE_RULES = @(
    '01-core-protocol.md',
    '02-memory-bank.md',
    '03-code-quality.md'
)

$VENDOR_GITIGNORE_ENTRIES = @('.spine', '.agents/', '.cursor/', '.claude/', '.opencode/')

$VENDOR_GITIGNORE_NOTE = '# Spine vendor mode: trees are versioned (.spine, .agents, .cursor, .claude, .opencode)'

$DOCS_SEED_PATHS = @(
    'memory/global/project-brief.md',
    'memory/global/product-context.md',
    'memory/global/domain-glossary.md',
    'memory/global/system-patterns.md',
    'memory/global/tech-context.md',
    'memory/global/decision-log.md',
    'memory/ledger/roadmap.md',
    'memory/ledger/progress.md',
    'memory/ledger/learnings.md',
    'memory/active_tasks/_task-template.md',
    'governance/skills-policy.md',
    'governance/memory-tags-policy.md',
    'governance/ice-scoring-guide.md',
    'quality/guardrails.md',
    'workflow/gitflow-operacional.md',
    'workflow/ciclo-de-entrega.md'
)

# Excluded only at the Spine root (templates/docs must still be vendored).
$SPINE_ROOT_EXCLUDE_DIRS = @('.git', '.spine', 'docs', '.cursor', '.claude', '.opencode', '.agents', 'graphify-out')

# Excluded at any depth.
$SPINE_ANY_EXCLUDE_DIRS = @('.git', 'node_modules', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache')

$SPINE_EXCLUDE_FILES = @('.spine-vendor')

$ROBOCOPY_FAILURE_EXIT_CODE = 8

$VALID_TARGETS = @('cursor', 'opencode', 'claude', 'antigravity')

$script:Copied = 0
$script:Skipped = 0
$script:Warnings = 0
$script:Removed = 0

# =============================================================================
# Logging
# =============================================================================

function Write-Mark {
    param([string]$Mark, [ConsoleColor]$Color, [string]$Message)
    Write-Host "  $Mark " -ForegroundColor $Color -NoNewline
    Write-Host $Message
}

function Write-Ok      { param([string]$Message) Write-Mark '+' Green $Message }
function Write-Skip    { param([string]$Message) Write-Mark '=' Blue $Message }
function Write-Warn    { param([string]$Message) Write-Mark '!' Yellow $Message }
function Write-Info    { param([string]$Message) Write-Mark 'i' Cyan $Message }
function Write-DryRun  { param([string]$Message) Write-Host "  [DRY-RUN] $Message" }

function Write-Section {
    param([string]$Title)
    Write-Host ''
    Write-Host $Title
}

function Stop-Install {
    param([string]$Message, [int]$ExitCode = 1)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit $ExitCode
}

# =============================================================================
# Path and filesystem helpers
# =============================================================================

function Split-ListArgument {
    <# Flattens values like 'a,b' passed through `powershell -File` into an array. #>
    param([string[]]$Values)
    $result = @()
    foreach ($value in $Values) {
        foreach ($part in ($value -split ',')) {
            $trimmed = $part.Trim()
            if ($trimmed) { $result += $trimmed }
        }
    }
    return , $result
}

function Join-Native {
    <# Join-Path that accepts '\' or '/' in Relative and emits the native separator. #>
    param([string]$Base, [string]$Relative)
    $separator = [System.IO.Path]::DirectorySeparatorChar
    return (Join-Path $Base ($Relative -replace '[\\/]', $separator))
}

function Resolve-FullPath {
    param([string]$Path)
    return (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\', '/')
}

function Test-SpineRoot {
    param([string]$Dir)
    foreach ($name in @('rules', 'skills', 'commands')) {
        if (-not (Test-Path -LiteralPath (Join-Native $Dir $name) -PathType Container)) { return $false }
    }
    return $true
}

function Test-ReparsePoint {
    <# True for symlinks and junctions, including broken ones. #>
    param([string]$Path)
    try {
        $attributes = [System.IO.File]::GetAttributes($Path)
    } catch {
        return $false
    }
    return (($attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
}

function Test-PathOrLink {
    param([string]$Path)
    return ((Test-Path -LiteralPath $Path) -or (Test-ReparsePoint $Path))
}

function Remove-Link {
    <# Deletes the link itself; never recurses into the link target. #>
    param([string]$Path)
    $attributes = [System.IO.File]::GetAttributes($Path)
    if (($attributes -band [System.IO.FileAttributes]::Directory) -ne 0) {
        [System.IO.Directory]::Delete($Path, $false)
    } else {
        [System.IO.File]::Delete($Path)
    }
}

function Remove-PathSafe {
    param([string]$Path)
    if (Test-ReparsePoint $Path) {
        Remove-Link $Path
    } elseif (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function New-DirectorySafe {
    param([string]$Dir)
    if (Test-Path -LiteralPath $Dir -PathType Container) { return }
    if ($DryRun) {
        Write-DryRun "Would create directory: $Dir"
    } else {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
}

function Get-RelativeToProject {
    param([string]$Path)
    if ($Path.StartsWith($script:ProjectRootFull)) {
        return $Path.Substring($script:ProjectRootFull.Length).TrimStart('\', '/')
    }
    return $Path
}

$script:HasRobocopy = [bool](Get-Command robocopy -ErrorAction SilentlyContinue)

function Test-RobocopyAvailable {
    return $script:HasRobocopy
}

function Invoke-Robocopy {
    param([string]$Source, [string]$Destination, [string[]]$ExtraArgs = @())
    $arguments = @($Source, $Destination, '/MIR', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/NC', '/NS') + $ExtraArgs
    & robocopy @arguments | Out-Null
    if ($LASTEXITCODE -ge $ROBOCOPY_FAILURE_EXIT_CODE) {
        Stop-Install "robocopy failed ($LASTEXITCODE): $Source -> $Destination"
    }
    $global:LASTEXITCODE = 0
}

function Sync-Directory {
    <# Mirrors Source into Destination (Destination becomes an exact copy). #>
    param([string]$Source, [string]$Destination)
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        Write-Warn "Source missing, skip: $Source"
        $script:Warnings++
        return $false
    }
    if ($DryRun) {
        Write-DryRun "Would mirror: $Source -> $Destination"
        $script:Copied++
        return $true
    }
    if (Test-ReparsePoint $Destination) { Remove-Link $Destination }
    if (Test-RobocopyAvailable) {
        Invoke-Robocopy $Source $Destination
    } else {
        Remove-PathSafe $Destination
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
        Get-ChildItem -LiteralPath $Source -Force | Copy-Item -Destination $Destination -Recurse -Force
    }
    $script:Copied++
    return $true
}

function Copy-FileSafe {
    param([string]$Source, [string]$Destination)
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        Write-Warn "File missing, skip: $Source"
        $script:Warnings++
        return $false
    }
    if ($DryRun) {
        Write-DryRun "Would copy file: $(Get-RelativeToProject $Destination)"
        $script:Copied++
        return $true
    }
    if (Test-ReparsePoint $Destination) { Remove-Link $Destination }
    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    $script:Copied++
    return $true
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Get-MarkdownFileNames {
    param([string]$Dir)
    if (-not (Test-Path -LiteralPath $Dir -PathType Container)) { return @() }
    return @(Get-ChildItem -LiteralPath $Dir -Filter '*.md' -File | Sort-Object Name | ForEach-Object { $_.Name })
}

function Get-AvailableSkills {
    param([string]$SourceRoot)
    $skillsDir = Join-Native $SourceRoot 'skills'
    return @(Get-ChildItem -LiteralPath $skillsDir -Directory | Sort-Object Name | ForEach-Object { $_.Name })
}

function Resolve-SkillList {
    param([string]$SourceRoot)
    if ($Core) { return $CORE_SKILLS }
    $selection = Split-ListArgument $Skills
    if ($selection.Count -eq 0 -or ($selection.Count -eq 1 -and $selection[0] -eq 'all')) {
        return Get-AvailableSkills $SourceRoot
    }
    if ($selection.Count -eq 1 -and $selection[0] -eq 'core') { return $CORE_SKILLS }
    return $selection
}

function Test-TargetEnabled {
    param([string]$Name)
    return ($script:TargetList -contains $Name)
}

# =============================================================================
# Symlink-mode detection
# =============================================================================

function Get-IdeLinkCandidates {
    param([string]$Root)
    return @(
        (Join-Native $Root '.agents\skills'),
        (Join-Native $Root '.agents\rules'),
        (Join-Native $Root '.agents\workflows'),
        (Join-Native $Root '.cursor\rules'),
        (Join-Native $Root '.cursor\commands'),
        (Join-Native $Root '.cursor\skills'),
        (Join-Native $Root '.opencode\commands'),
        (Join-Native $Root '.opencode\agents'),
        (Join-Native $Root '.claude\skills')
    )
}

function Get-IdeLinks {
    <# Returns IDE directories that are links, or links found directly inside them. #>
    param([string]$Root)
    $links = @()
    foreach ($dir in (Get-IdeLinkCandidates $Root)) {
        if (Test-ReparsePoint $dir) {
            $links += $dir
            continue
        }
        if (Test-Path -LiteralPath $dir -PathType Container) {
            foreach ($child in (Get-ChildItem -LiteralPath $dir -Force)) {
                if (Test-ReparsePoint $child.FullName) { $links += $child.FullName }
            }
        }
    }
    return , $links
}

function Get-LinkTarget {
    param([string]$Path)
    $target = (Get-Item -LiteralPath $Path -Force).Target
    if ($target -is [array]) { $target = $target[0] }
    if (-not $target) { return '' }
    if (-not [System.IO.Path]::IsPathRooted($target)) {
        $target = Join-Native (Split-Path -Parent $Path) $target
    }
    return $target
}

function Invoke-SymlinkModeCheck {
    param([string]$Root)
    $spinePath = Join-Native $Root '.spine'
    $marker = Join-Native $Root '.spine-vendor'
    $spineIsLink = Test-ReparsePoint $spinePath
    $ideLinks = @()
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) { $ideLinks = Get-IdeLinks $Root }

    if (-not $spineIsLink -and $ideLinks.Count -eq 0) { return }

    if (-not $Force) {
        Write-Host '  x Symlink-mode Spine detected in ' -ForegroundColor Red -NoNewline
        Write-Host $Root
        if ($spineIsLink) { Write-Host "       .spine is a symlink -> $(Get-LinkTarget $spinePath)" }
        if ($ideLinks.Count -gt 0) { Write-Host '       IDE paths contain symlinks and .spine-vendor is missing.' }
        Write-Host '       Vendor install refuses to mix modes.'
        Write-Host '       Re-run with -Force to convert to vendor mode (copies real files).'
        exit 3
    }

    if ($spineIsLink -and -not $script:SpineDirGiven) {
        $linkTarget = Get-LinkTarget $spinePath
        if ($linkTarget -and (Test-Path -LiteralPath $linkTarget -PathType Container)) {
            $script:SpineDirCandidate = $linkTarget
            Write-Info "Using symlink target as -SpineDir: $linkTarget"
        }
    }

    Write-Section 'Removing symlink-mode artefacts:'
    $toRemove = @($ideLinks)
    if ($spineIsLink) { $toRemove += $spinePath }
    foreach ($link in $toRemove) {
        $relative = Get-RelativeToProject $link
        if ($DryRun) {
            Write-DryRun "Would remove symlink: $relative"
        } else {
            Remove-Link $link
            Write-Ok "removed symlink: $relative"
        }
        $script:Removed++
    }
}

# =============================================================================
# Source resolution and vendoring
# =============================================================================

function Resolve-SourceSpineDir {
    param([string]$Root)
    if ($Update -and -not $script:SpineDirGiven -and -not $script:SpineDirCandidate) {
        Stop-Install '-Update requires -SpineDir PATH (source must differ from vendored .spine).'
    }

    $candidate = $script:SpineDirCandidate
    if (-not $candidate) { $candidate = $PSScriptRoot }
    if (-not (Test-Path -LiteralPath $candidate -PathType Container)) {
        Stop-Install "-SpineDir not found: $candidate"
    }
    $source = Resolve-FullPath $candidate

    if (-not (Test-SpineRoot $source)) {
        Stop-Install "Cannot find rules\, skills\, or commands\ in $source"
    }
    if ($source -eq $Root) {
        Stop-Install "-ProjectRoot must differ from the Spine source directory ($source)."
    }

    $destSpine = Join-Native $Root '.spine'
    if ((Test-Path -LiteralPath $destSpine -PathType Container) -and -not (Test-ReparsePoint $destSpine)) {
        if ((Resolve-FullPath $destSpine) -eq $source) {
            Stop-Install ("-SpineDir points at the project's vendored .spine ($source).`n" +
                "       Pass the upstream Spine directory, e.g. -SpineDir C:\tools\spine")
        }
    }
    return $source
}

function Remove-NestedExcludedDirs {
    param([string]$Dest)
    $nested = @(Get-ChildItem -LiteralPath $Dest -Directory -Recurse -Force |
        Where-Object { $SPINE_ANY_EXCLUDE_DIRS -contains $_.Name })
    foreach ($dir in $nested) {
        if (Test-Path -LiteralPath $dir.FullName) { Remove-PathSafe $dir.FullName }
    }
}

function Copy-SpineIntoProject {
    param([string]$Source, [string]$Dest)
    Write-Section 'Vendoring Spine -> .spine\:'

    if ($DryRun) {
        Write-DryRun "Would mirror $Source -> $Dest (exclude .git, docs, IDE dirs, caches)"
        $script:Copied++
        return
    }

    if (Test-RobocopyAvailable) {
        $excludeDirs = @($SPINE_ROOT_EXCLUDE_DIRS | ForEach-Object { Join-Native $Source $_ }) + $SPINE_ANY_EXCLUDE_DIRS
        $extra = @('/XD') + $excludeDirs + @('/XF') + $SPINE_EXCLUDE_FILES
        Invoke-Robocopy $Source $Dest $extra
    } else {
        Write-Warn 'robocopy not found; using Copy-Item (full replace of .spine\)'
        $script:Warnings++
        Remove-PathSafe $Dest
        New-Item -ItemType Directory -Path $Dest -Force | Out-Null
        Get-ChildItem -LiteralPath $Source -Force |
            Where-Object { ($SPINE_ROOT_EXCLUDE_DIRS -notcontains $_.Name) -and ($SPINE_EXCLUDE_FILES -notcontains $_.Name) } |
            Copy-Item -Destination $Dest -Recurse -Force
        Remove-NestedExcludedDirs $Dest
    }

    # Never leave a nested git repo inside the consumer project.
    $nestedGit = Join-Native $Dest '.git'
    if (Test-PathOrLink $nestedGit) {
        Remove-PathSafe $nestedGit
        Write-Ok 'removed nested .git from .spine\'
    }

    Write-Ok ".spine\ vendored from $Source"
    $script:Copied++
}

# =============================================================================
# IDE trees
# =============================================================================

function Install-Skills {
    param([string]$Root, [string]$Vendored, [string[]]$SkillList)
    $agentsSkills = Join-Native $Root '.agents\skills'
    Write-Section 'Skills (.agents\skills\ as real directories):'
    New-DirectorySafe $agentsSkills

    if ($Update -and -not $DryRun -and (Test-Path -LiteralPath $agentsSkills -PathType Container)) {
        foreach ($existing in (Get-ChildItem -LiteralPath $agentsSkills -Directory -Force)) {
            if ($SkillList -notcontains $existing.Name) {
                Remove-PathSafe $existing.FullName
                Write-Ok "removed skill (not in selection): $($existing.Name)"
                $script:Removed++
            }
        }
    }

    foreach ($skill in $SkillList) {
        $src = Join-Native $Vendored "skills\$skill"
        if (-not (Test-Path -LiteralPath $src -PathType Container)) {
            Write-Warn "Skill '$skill' not found in vendored .spine, skipping"
            $script:Warnings++
            continue
        }
        if (Sync-Directory $src (Join-Native $agentsSkills $skill)) { Write-Ok "skill: $skill" }
    }
}

function Sync-SkillsHub {
    param([string]$Root, [string]$HubRelative)
    Write-Host ''
    Write-Host "Skills hub ($HubRelative\ copy of .agents\skills\):"
    $agentsSkills = Join-Native $Root '.agents\skills'
    if ($DryRun) {
        Write-DryRun "Would copy .agents\skills\ -> $HubRelative\"
        return
    }
    if (Sync-Directory $agentsSkills (Join-Native $Root $HubRelative)) { Write-Ok "$HubRelative\" }
}

function Install-CursorTree {
    param([string]$Root, [string]$Vendored)
    Write-Section '=== Cursor (copied files) ==='
    $cursorRules = Join-Native $Root '.cursor\rules'
    $cursorCommands = Join-Native $Root '.cursor\commands'
    New-DirectorySafe $cursorRules
    New-DirectorySafe $cursorCommands

    foreach ($rule in $CORE_RULES) {
        if (Copy-FileSafe (Join-Native $Vendored "rules\$rule") (Join-Native $cursorRules $rule)) { Write-Ok "rule: $rule" }
    }
    foreach ($command in (Get-MarkdownFileNames (Join-Native $Vendored 'commands'))) {
        if (Copy-FileSafe (Join-Native $Vendored "commands\$command") (Join-Native $cursorCommands $command)) {
            Write-Ok "command: $command"
        }
    }
    Sync-SkillsHub $Root '.cursor\skills'
}

function Install-ClaudeTree {
    param([string]$Root)
    Write-Section '=== Claude Code (copied files) ==='
    Sync-SkillsHub $Root '.claude\skills'
}

function Install-OpencodeTree {
    param([string]$Root, [string]$Vendored)
    Write-Section '=== OpenCode (copied files) ==='
    $ocCommands = Join-Native $Root '.opencode\commands'
    $ocAgents = Join-Native $Root '.opencode\agents'
    New-DirectorySafe $ocCommands
    New-DirectorySafe $ocAgents

    foreach ($command in (Get-MarkdownFileNames (Join-Native $Vendored 'commands'))) {
        if (Copy-FileSafe (Join-Native $Vendored "commands\$command") (Join-Native $ocCommands $command)) {
            Write-Ok "command: $command"
        }
    }
    foreach ($agent in (Get-MarkdownFileNames (Join-Native $Vendored 'agents'))) {
        if (Copy-FileSafe (Join-Native $Vendored "agents\$agent") (Join-Native $ocAgents $agent)) { Write-Ok "agent: $agent" }
    }
}

function Install-AntigravityTree {
    param([string]$Root, [string]$Vendored)
    Write-Section '=== Antigravity (copied files) ==='
    $agentsRules = Join-Native $Root '.agents\rules'
    $agentsWorkflows = Join-Native $Root '.agents\workflows'
    $cursorRules = Join-Native $Root '.cursor\rules'
    New-DirectorySafe $agentsRules
    New-DirectorySafe $agentsWorkflows

    foreach ($rule in $CORE_RULES) {
        if (Copy-FileSafe (Join-Native $Vendored "rules\$rule") (Join-Native $agentsRules $rule)) { Write-Ok "agy-rule: $rule" }
    }

    # Mirror project-local Cursor rules (graphify.mdc, ansible.mdc, ...).
    if (Test-Path -LiteralPath $cursorRules -PathType Container) {
        foreach ($file in (Get-ChildItem -LiteralPath $cursorRules -File | Sort-Object Name)) {
            if ($CORE_RULES -contains $file.Name) { continue }
            if (Copy-FileSafe $file.FullName (Join-Native $agentsRules $file.Name)) { Write-Ok "agy-rule (project): $($file.Name)" }
        }
    }

    foreach ($command in (Get-MarkdownFileNames (Join-Native $Vendored 'commands'))) {
        if (Copy-FileSafe (Join-Native $Vendored "commands\$command") (Join-Native $agentsWorkflows $command)) {
            Write-Ok "agy-workflow: $command"
        }
    }
}

# =============================================================================
# docs\, opencode.json, .gitignore, marker
# =============================================================================

function Initialize-DocsTemplates {
    param([string]$Root, [string]$Source)
    Write-Section 'Docs templates:'
    $templatesDocs = Join-Native $Source 'templates\docs'
    if (-not (Test-Path -LiteralPath $templatesDocs -PathType Container)) {
        Write-Warn "templates\docs\ not found in $Source"
        $script:Warnings++
        return
    }

    $seeded = 0
    $skipped = 0
    $missing = 0
    foreach ($relative in $DOCS_SEED_PATHS) {
        $windowsRelative = $relative -replace '/', '\'
        $src = Join-Native $templatesDocs $windowsRelative
        $dest = Join-Native $Root "docs\$windowsRelative"
        if (-not (Test-Path -LiteralPath $src -PathType Leaf)) {
            Write-Warn "template missing: templates/docs/$relative"
            $missing++
            continue
        }
        if (Test-Path -LiteralPath $dest -PathType Leaf) {
            Write-Skip "docs/$relative (already exists, not overwriting)"
            $skipped++
            $script:Skipped++
            continue
        }
        if ($DryRun) {
            Write-DryRun "Would copy: docs/$relative"
        } else {
            $parent = Split-Path -Parent $dest
            if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
            Copy-Item -LiteralPath $src -Destination $dest
            Write-Ok "docs/$relative (seeded from templates/)"
        }
        $seeded++
    }

    foreach ($dir in @('docs\documentation', 'docs\memory\active_tasks', 'docs\memory\completed_tasks')) {
        New-DirectorySafe (Join-Native $Root $dir)
    }
    foreach ($gitkeep in @('docs\memory\active_tasks\.gitkeep', 'docs\memory\completed_tasks\.gitkeep')) {
        $gitkeepPath = Join-Native $Root $gitkeep
        if (Test-Path -LiteralPath $gitkeepPath -PathType Leaf) {
            Write-Skip "$gitkeep (already exists)"
            continue
        }
        if ($DryRun) {
            Write-DryRun "Would create: $gitkeep"
        } else {
            Write-Utf8NoBom $gitkeepPath ''
            Write-Ok "$gitkeep (created)"
        }
    }

    Write-Host ''
    Write-Host "  Docs seed: $seeded copied, $skipped skipped (existing), $missing template gaps"
}

function Read-JsonFile {
    param([string]$Path)
    $raw = [System.IO.File]::ReadAllText($Path)
    if (-not $raw.Trim()) { throw "empty JSON file: $Path" }
    return ($raw | ConvertFrom-Json)
}

function Merge-OpencodeJson {
    <# Union of Spine `instructions` into the project's opencode.json (port of merge-opencode.py). #>
    param([string]$Root, [string]$Source)
    Write-Section 'opencode.json:'
    $templatePath = Join-Native $Source 'templates\opencode.json'
    $projectPath = Join-Native $Root 'opencode.json'

    if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
        Write-Warn "templates\opencode.json not found in $Source"
        $script:Warnings++
        return
    }

    if (-not (Test-Path -LiteralPath $projectPath -PathType Leaf)) {
        if ($DryRun) {
            Write-DryRun 'Would create: opencode.json from template'
        } else {
            Copy-Item -LiteralPath $templatePath -Destination $projectPath
            Write-Ok "opencode.json (created: $projectPath)"
        }
        return
    }

    if ($DryRun) {
        Write-DryRun 'Would merge Spine instructions into: opencode.json'
        return
    }

    try {
        $template = Read-JsonFile $templatePath
        $project = Read-JsonFile $projectPath
    } catch {
        Write-Warn "opencode.json merge failed (left unchanged): $($_.Exception.Message)"
        $script:Warnings++
        return
    }

    $required = @()
    if ($template.PSObject.Properties['instructions']) { $required = @($template.instructions) }

    $existing = @()
    $instructionsProperty = $project.PSObject.Properties['instructions']
    if ($instructionsProperty -and ($instructionsProperty.Value -is [System.Array])) {
        $existing = @($instructionsProperty.Value)
    }

    $merged = New-Object System.Collections.Generic.List[object]
    foreach ($item in ($existing + $required)) {
        if (($item -is [string]) -and -not $merged.Contains($item)) { $merged.Add($item) }
    }
    $mergedArray = [object[]]$merged.ToArray()

    if ($instructionsProperty) {
        $project.instructions = $mergedArray
    } else {
        $project | Add-Member -NotePropertyName 'instructions' -NotePropertyValue $mergedArray
    }
    if (-not $project.PSObject.Properties['$schema'] -and $template.PSObject.Properties['$schema']) {
        $project | Add-Member -NotePropertyName '$schema' -NotePropertyValue $template.'$schema'
    }

    $json = ($project | ConvertTo-Json -Depth 32) -replace "`r`n", "`n"
    Write-Utf8NoBom $projectPath ($json + "`n")
    Write-Ok "opencode.json (merged: $projectPath)"
}

function Update-GitignoreForVendor {
    param([string]$Root)
    Write-Section 'Gitignore (vendor mode - trees are versioned):'
    $gitignore = Join-Native $Root '.gitignore'

    if (-not (Test-Path -LiteralPath $gitignore -PathType Leaf)) {
        if ($DryRun) {
            Write-DryRun 'Would create .gitignore with vendor note (no Spine path ignores)'
        } else {
            Write-Utf8NoBom $gitignore ($VENDOR_GITIGNORE_NOTE + "`n")
            Write-Ok '.gitignore (created with vendor note)'
        }
        return
    }

    $raw = [System.IO.File]::ReadAllText($gitignore)
    $newline = "`n"
    if ($raw.Contains("`r`n")) { $newline = "`r`n" }
    $lines = @($raw -split "`r?`n")
    if ($lines.Count -gt 0 -and $lines[-1] -eq '') { $lines = @($lines | Select-Object -First ($lines.Count - 1)) }

    $kept = @()
    $removedEntries = @()
    foreach ($line in $lines) {
        if ($VENDOR_GITIGNORE_ENTRIES -contains $line) {
            $removedEntries += $line
        } else {
            $kept += $line
        }
    }
    $hasNote = [bool]($kept | Where-Object { $_ -like '*Spine vendor mode*' })

    if ($DryRun) {
        foreach ($entry in $removedEntries) { Write-DryRun "Would remove ignore entry: $entry" }
        if (-not $hasNote) { Write-DryRun 'Would add vendor mode note to .gitignore' }
        return
    }

    foreach ($entry in $removedEntries) { Write-Ok "gitignore: removed ignore for $entry" }
    if ($hasNote) {
        Write-Skip 'gitignore: vendor mode note (already present)'
    } else {
        $kept += ''
        $kept += $VENDOR_GITIGNORE_NOTE
        Write-Ok 'gitignore: added vendor mode note'
    }
    if ($removedEntries.Count -eq 0) { Write-Skip 'gitignore: no Spine path ignores to remove' }

    if ($removedEntries.Count -gt 0 -or -not $hasNote) {
        Write-Utf8NoBom $gitignore (($kept -join $newline) + $newline)
    }
}

function Write-VendorMarker {
    param([string]$Root, [string]$Source)
    $marker = Join-Native $Root '.spine-vendor'
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
    if ($DryRun) {
        Write-DryRun "Would write $marker"
        return
    }
    Write-Utf8NoBom $marker ("mode=vendor`nupdated_at=$timestamp`nsource=$Source`n")
    Write-Ok ".spine-vendor (updated_at=$timestamp)"
}

# =============================================================================
# Uninstall and summary
# =============================================================================

function Invoke-Uninstall {
    param([string]$Root)
    Write-Host 'Spine Vendor Uninstaller'
    Write-Host "Project: $Root"
    Write-Host ''

    if (Test-ReparsePoint (Join-Native $Root '.spine')) {
        Stop-Install ".spine is a symlink (symlink mode).`n       Use: bash .spine/install.sh --uninstall"
    }

    $paths = @(
        '.spine-vendor', '.spine', '.agents',
        '.cursor\rules', '.cursor\commands', '.cursor\skills',
        '.opencode\commands', '.opencode\agents',
        '.claude\skills'
    )
    foreach ($relative in $paths) {
        $path = Join-Native $Root $relative
        if (-not (Test-PathOrLink $path)) { continue }
        if ($DryRun) {
            Write-DryRun "Would remove: $relative"
        } else {
            Remove-PathSafe $path
            Write-Ok "removed: $relative"
        }
        $script:Removed++
    }

    Write-Host ''
    Write-Host 'Note: docs\ and opencode.json were NOT removed.'
    Write-Host "Done. Removed $($script:Removed) path(s)."
}

function Write-NextSteps {
    param([string]$Root)
    Write-Host ''
    Write-Host '==========================================='
    Write-Host '  Vendor install complete'
    Write-Host '==========================================='
    Write-Host ''
    Write-Host "  Copied : $($script:Copied)"
    Write-Host "  Skipped: $($script:Skipped)"
    Write-Host "  Warns  : $($script:Warnings)"
    Write-Host "  Removed: $($script:Removed)"
    Write-Host ''
    Write-Host 'Next steps:'
    Write-Host '  1. Review changes under:'
    Write-Host '       .spine\ .agents\ .cursor\ .opencode\ .claude\ .spine-vendor'
    Write-Host '  2. Commit and push so teammates get Spine via git clone / pull:'
    Write-Host '       git add .spine .agents .cursor .opencode .claude .spine-vendor docs opencode.json .gitignore'
    Write-Host '       git commit -m "chore: vendor Spine into project"'
    Write-Host '  3. Open the project in the IDE and run /spine-bootstrap, then /spine-plan.'
    Write-Host ''
    Write-Host 'Update later (from an upstream Spine directory):'
    Write-Host "  powershell -ExecutionPolicy Bypass -File $Root\.spine\install.ps1 -Update -ProjectRoot $Root -SpineDir C:\path\to\spine"
    Write-Host ''
    Write-Host 'Note: slash-command validators run `bash .spine/scripts/*.sh`; install Git for Windows'
    Write-Host '      (Git Bash) and set it as the IDE default terminal so those steps can run.'
    if ($DryRun) {
        Write-Host ''
        Write-Host 'This was a dry run. No changes were made.'
    }
}

# =============================================================================
# Main
# =============================================================================

if ($Update -and $Uninstall) { Stop-Install '-Update and -Uninstall cannot be combined.' }

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    Stop-Install "-ProjectRoot not found: $ProjectRoot"
}
$script:ProjectRootFull = Resolve-FullPath $ProjectRoot

$script:SpineDirGiven = [bool]$SpineDir
$script:SpineDirCandidate = $SpineDir

$requestedSource = $PSScriptRoot
if ($SpineDir) { $requestedSource = $SpineDir }
if ((Test-Path -LiteralPath $requestedSource -PathType Container) -and
    ((Resolve-FullPath $requestedSource) -eq $script:ProjectRootFull)) {
    Stop-Install "-ProjectRoot must differ from the Spine source directory ($script:ProjectRootFull)."
}

$script:TargetList = Split-ListArgument $Targets
foreach ($target in $script:TargetList) {
    if ($VALID_TARGETS -notcontains $target) {
        Stop-Install "Unknown target '$target'. Valid: $($VALID_TARGETS -join ',')"
    }
}

Write-Host 'Spine Vendor Install (PowerShell)'
Write-Host "Project: $script:ProjectRootFull"
if ($Force) { Write-Host 'Mode:   force' }
if ($DryRun) { Write-Host 'Mode:   dry-run' }
if ($Update) { Write-Host 'Mode:   update (overwrite)' }
if ($Uninstall) { Write-Host 'Mode:   uninstall' }
Write-Host ''

if ($Uninstall) {
    Invoke-Uninstall $script:ProjectRootFull
    exit 0
}

Invoke-SymlinkModeCheck $script:ProjectRootFull

$sourceSpine = Resolve-SourceSpineDir $script:ProjectRootFull
Write-Host "Source: $sourceSpine"

$destSpine = Join-Native $script:ProjectRootFull '.spine'
$markerPath = Join-Native $script:ProjectRootFull '.spine-vendor'
if ($Update -and -not (Test-Path -LiteralPath $markerPath) -and -not (Test-Path -LiteralPath $destSpine)) {
    Write-Warn 'No existing vendor install found; performing first-time vendor install.'
    $script:Warnings++
}

Copy-SpineIntoProject $sourceSpine $destSpine

# After copy, materialize from the vendored tree (stable relative layout).
$vendored = $destSpine
if ($DryRun) { $vendored = $sourceSpine }

$skillList = Resolve-SkillList $sourceSpine
Install-Skills $script:ProjectRootFull $vendored $skillList

if (Test-TargetEnabled 'cursor') { Install-CursorTree $script:ProjectRootFull $vendored }
if (Test-TargetEnabled 'claude') { Install-ClaudeTree $script:ProjectRootFull }
if (Test-TargetEnabled 'opencode') { Install-OpencodeTree $script:ProjectRootFull $vendored }
if (Test-TargetEnabled 'antigravity') { Install-AntigravityTree $script:ProjectRootFull $vendored }

Initialize-DocsTemplates $script:ProjectRootFull $sourceSpine
Merge-OpencodeJson $script:ProjectRootFull $sourceSpine
Update-GitignoreForVendor $script:ProjectRootFull
Write-VendorMarker $script:ProjectRootFull $sourceSpine

Write-NextSteps $script:ProjectRootFull
