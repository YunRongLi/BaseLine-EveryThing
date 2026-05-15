<#
.SYNOPSIS
    Installs AI Agent rules, skills, and workflows.

.DESCRIPTION
    Copies the rules, skills, and workflows from the current project structure into
    the target directory corresponding to the specified AI Agent and Scope.

.PARAMETER Agent
    Which agent format to target: antigravity (default), copilot, or claude.

.PARAMETER Scope
    Installation scope: global (default) or workspace.

.PARAMETER Rules
    An array of rule names to install. Defaults to 'all'. Select specific rules by name.

.PARAMETER Path
    Specific location to install into when Scope is workspace.

.EXAMPLE
    .\install.ps1 -Agent antigravity -Scope workspace
    Installs for Antigravity in the local workspace (.agents folder).

.EXAMPLE
    .\install.ps1 -Agent antigravity -Scope workspace -Path "C:\MyProject"
    Installs for Antigravity in the specified workspace path (C:\MyProject\.agents folder).
#>
[CmdletBinding()]
param (
    [ValidateSet("antigravity", "copilot", "claude")]
    [string]$Agent = "antigravity",
    
    [ValidateSet("global", "workspace")]
    [string]$Scope = "global",
    
    [string[]]$Rules = @("all"),
    
    [string]$Path = ""
)

# Define Base Directories based on Agent and Scope
if ($Scope -eq "workspace") {
    switch ($Agent) {
        "antigravity" {
            $BaseDir = if ([string]::IsNullOrWhiteSpace($Path)) { ".agents" } else { Join-Path $Path ".agents" }
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
        "copilot" {
            $BaseDir = if ([string]::IsNullOrWhiteSpace($Path)) { ".github" } else { Join-Path $Path ".github" }
            $TargetRules = $BaseDir  # Copilot instructions usually go in .github/
            $TargetSkills = Join-Path $BaseDir "skills"
        }
        "claude" {
            $BaseDir = if ([string]::IsNullOrWhiteSpace($Path)) { ".claude" } else { Join-Path $Path ".claude" }
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
    }
    Write-Host "[Building] Installing for $Agent into Workspace: $BaseDir" -ForegroundColor Cyan
} else {
    switch ($Agent) {
        "antigravity" {
            $BaseDir = Join-Path $HOME ".antigravity"
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
        "copilot" {
            $BaseDir = Join-Path $HOME ".copilot"
            $TargetRules = $BaseDir
            $TargetSkills = Join-Path $BaseDir "skills"
        }
        "claude" {
            $BaseDir = Join-Path $HOME ".claude"
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
    }
    Write-Host "[Global] Installing for $Agent into Global: $BaseDir" -ForegroundColor Cyan
}

# Create target directories if they don't exist
if (-not (Test-Path $TargetRules)) {
    New-Item -ItemType Directory -Path $TargetRules -Force | Out-Null
}
if (-not (Test-Path $TargetSkills)) {
    New-Item -ItemType Directory -Path $TargetSkills -Force | Out-Null
}

# Install Rules
if (Test-Path "rules") {
    # For other agents or workspace scope, copy everything except GEMINI.md (unless it's antigravity workspace)
    $ExcludeList = @()
    if ($Agent -ne "antigravity") {
        $ExcludeList += "GEMINI.md"
    }
    
    Write-Host "[Packaging] Copying rules from .\rules to $TargetRules..." -ForegroundColor Yellow
    Get-ChildItem -Path "rules" -Filter "*.md" -Recurse -File | Where-Object { 
        ($ExcludeList -notcontains $_.Name) -and 
        ($Rules -contains "all" -or $Rules -contains $_.BaseName -or $Rules -contains $_.Name) 
    } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $TargetRules -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Rules installed." -ForegroundColor Green
} else {
    Write-Host "[Warning] No .\rules directory found." -ForegroundColor DarkYellow
}

# Install Skills
if (Test-Path "skills") {
    Write-Host "[Packaging] Copying skills from .\skills to $TargetSkills..." -ForegroundColor Yellow
    Copy-Item -Path "skills\*" -Destination $TargetSkills -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Skills installed." -ForegroundColor Green
} else {
    Write-Host "[Info] No .\skills directory found." -ForegroundColor Blue
}

# Install Workflows
$TargetWorkflows = Join-Path $BaseDir "workflows"
if (Test-Path "workflows") {
    if (-not (Test-Path $TargetWorkflows)) {
        New-Item -ItemType Directory -Path $TargetWorkflows -Force | Out-Null
    }
    Write-Host "[Packaging] Copying workflows from .\workflows to $TargetWorkflows..." -ForegroundColor Yellow
    Copy-Item -Path "workflows\*" -Destination $TargetWorkflows -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Workflows installed." -ForegroundColor Green
} else {
    Write-Host "[Info] No .\workflows directory found." -ForegroundColor Blue
}

Write-Host "Done! $Agent is now configured ($Scope scope)." -ForegroundColor Cyan
