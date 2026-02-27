param (
    [ValidateSet("antigravity", "copilot", "claude")]
    [string]$Agent = "antigravity",
    
    [ValidateSet("global", "workspace")]
    [string]$Scope = "global"
)

# Define Base Directories based on Agent and Scope
if ($Scope -eq "workspace") {
    switch ($Agent) {
        "antigravity" {
            $BaseDir = ".agent"
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
        "copilot" {
            $BaseDir = ".github"
            $TargetRules = $BaseDir  # Copilot instructions usually go in .github/
            $TargetSkills = Join-Path $BaseDir "skills"
        }
        "claude" {
            $BaseDir = ".claude"
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
    }
    Write-Host "[Building] Installing for $Agent into Workspace: $BaseDir" -ForegroundColor Cyan
} else {
    switch ($Agent) {
        "antigravity" {
            $BaseDir = Join-Path $HOME ".gemini"
            $TargetRules = $BaseDir  # Global rules in ~/.gemini/GEMINI.md
            $TargetSkills = Join-Path $BaseDir "antigravity\skills"
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
    if ($Agent -eq "antigravity" -and $Scope -eq "global") {
        # Antigravity Global: GEMINI.md goes to ~/.gemini/, others to ~/.gemini/rules/
        Write-Host "[Packaging] Installing Antigravity global rules..." -ForegroundColor Yellow
        if (Test-Path "rules\GEMINI.md") {
            Copy-Item -Path "rules\GEMINI.md" -Destination $TargetRules -Force
            Write-Host "[OK] GEMINI.md installed to $TargetRules" -ForegroundColor Green
        }
        
        $SecondaryRules = Join-Path $TargetRules "rules"
        if (-not (Test-Path $SecondaryRules)) {
            New-Item -ItemType Directory -Path $SecondaryRules -Force | Out-Null
        }
        
        # Copy everything EXCEPT GEMINI.md to the 'rules' subfolder
        Get-ChildItem -Path "rules\*" -Exclude "GEMINI.md" | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $SecondaryRules -Recurse -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[OK] Secondary rules installed to $SecondaryRules" -ForegroundColor Green
    } else {
        # For other agents or workspace scope, copy everything except GEMINI.md (unless it's antigravity workspace)
        $ExcludeList = @()
        if ($Agent -ne "antigravity") {
            $ExcludeList += "GEMINI.md"
        }
        
        Write-Host "[Packaging] Copying rules from .\rules to $TargetRules..." -ForegroundColor Yellow
        Get-ChildItem -Path "rules\*" -Exclude $ExcludeList | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $TargetRules -Recurse -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[OK] Rules installed." -ForegroundColor Green
    }
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
