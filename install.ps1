<#
.SYNOPSIS
    Installs AI Agent skills.

.DESCRIPTION
    Copies the skills from the current project structure into
    the target directory corresponding to the specified AI Agent and Scope.

.PARAMETER Agent
    Which agent format to target: antigravity (default), antigravity-ide, or opencode.

.PARAMETER Scope
    Installation scope: global (default) or workspace.

.PARAMETER Path
    Specific location to install into when Scope is workspace.

.PARAMETER PluginName
    Name of the plugin bundle (default: baseline-everything).

.EXAMPLE
    .\install.ps1 -Agent antigravity -Scope workspace
    Installs for Antigravity in the local workspace (.agents folder).

.EXAMPLE
    .\install.ps1 -Agent antigravity -Scope workspace -Path "C:\MyProject"
    Installs for Antigravity in the specified workspace path (C:\MyProject\.agents folder).
#>
[CmdletBinding()]
param (
    [ValidateSet("antigravity", "antigravity-ide", "opencode")]
    [string]$Agent = "antigravity",
    
    [ValidateSet("global", "workspace")]
    [string]$Scope = "global",
    
    [string]$Path = "",

    [string]$PluginName = "baseline-everything"
)

# Define Base Directories based on Agent and Scope
if ($Scope -eq "workspace") {
    $WorkspaceRoot = if ([string]::IsNullOrWhiteSpace($Path)) { "." } else { $Path }
    switch ($Agent) {
        "antigravity" {
            $BaseDir = Join-Path $WorkspaceRoot ".agents\plugins\$PluginName"
            $TargetSkills = Join-Path $BaseDir "skills"
            $LegacySkillsDir = Join-Path $WorkspaceRoot ".agents\skills"
        }
        "antigravity-ide" {
            $BaseDir = Join-Path $WorkspaceRoot ".agents\plugins\$PluginName"
            $TargetSkills = Join-Path $BaseDir "skills"
            $DirectWorkspaceSkills = Join-Path $WorkspaceRoot ".agents\skills"
            $LegacySkillsDir = Join-Path $WorkspaceRoot ".agents\skills"
        }
        "opencode" {
            $BaseDir = Join-Path $WorkspaceRoot ".opencode"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
    }
    Write-Host "[Building] Installing for $Agent into Workspace: $BaseDir" -ForegroundColor Cyan
} else {
    switch ($Agent) {
        "antigravity" {
            $BaseDir = Join-Path $HOME ".gemini\antigravity-cli\plugins\$PluginName"
            $TargetSkills = Join-Path $BaseDir "skills"
            $DirectGlobalSkills = Join-Path $HOME ".gemini\antigravity-cli\skills"
            $SharedSkills = Join-Path $HOME ".gemini\skills"
        }
        "antigravity-ide" {
            $BaseDir = Join-Path $HOME ".gemini\antigravity-ide\plugins\$PluginName"
            $TargetSkills = Join-Path $BaseDir "skills"
            $DirectGlobalSkills = Join-Path $HOME ".gemini\config\skills"
            $SharedSkills = Join-Path $HOME ".gemini\skills"
        }
        "opencode" {
            $BaseDir = Join-Path $HOME ".config\opencode"
            $TargetSkills = Join-Path $BaseDir "skills"
        }
    }
    Write-Host "[Global] Installing for $Agent into Global: $BaseDir" -ForegroundColor Cyan
}

# Create target directories if they don't exist
if (-not (Test-Path $BaseDir)) {
    New-Item -ItemType Directory -Path $BaseDir -Force | Out-Null
}
if ($TargetSkills -and -not (Test-Path $TargetSkills)) {
    New-Item -ItemType Directory -Path $TargetSkills -Force | Out-Null
}
if ($Scope -eq "workspace" -and $Agent -eq "antigravity") {
    if (-not (Test-Path $LegacySkillsDir)) {
        New-Item -ItemType Directory -Path $LegacySkillsDir -Force | Out-Null
    }
} elseif ($Scope -eq "workspace" -and $Agent -eq "antigravity-ide") {
    if (-not (Test-Path $LegacySkillsDir)) {
        New-Item -ItemType Directory -Path $LegacySkillsDir -Force | Out-Null
    }
    if (-not (Test-Path $DirectWorkspaceSkills)) {
        New-Item -ItemType Directory -Path $DirectWorkspaceSkills -Force | Out-Null
    }
} elseif ($Scope -eq "global" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
    foreach ($Dir in @($SharedSkills, $DirectGlobalSkills)) {
        if (-not (Test-Path $Dir)) {
            New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        }
    }
}

# Install Skills
if ($TargetSkills -and (Test-Path "skills")) {
    Write-Host "[Packaging] Copying skills from .\skills to $TargetSkills..." -ForegroundColor Yellow
    Copy-Item -Path "skills\*" -Destination $TargetSkills -Recurse -Force -ErrorAction SilentlyContinue
    if ($Scope -eq "workspace" -and $Agent -eq "antigravity") {
        Copy-Item -Path "skills\*" -Destination $LegacySkillsDir -Recurse -Force -ErrorAction SilentlyContinue
    } elseif ($Scope -eq "workspace" -and $Agent -eq "antigravity-ide") {
        Copy-Item -Path "skills\*" -Destination $LegacySkillsDir -Recurse -Force -ErrorAction SilentlyContinue
        # Flatten each skills/<DirName>/SKILL.md -> .agents/skills/<DirName>.md
        Get-ChildItem -Path "skills" -Directory | ForEach-Object {
            $SkillFile = Join-Path $_.FullName "SKILL.md"
            if (Test-Path $SkillFile) {
                Copy-Item -Path $SkillFile -Destination (Join-Path $DirectWorkspaceSkills "$($_.Name).md") -Force -ErrorAction SilentlyContinue
            }
        }
    } elseif ($Scope -eq "global" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
        Copy-Item -Path "skills\*" -Destination $SharedSkills -Recurse -Force -ErrorAction SilentlyContinue
        Copy-Item -Path "skills\*" -Destination $DirectGlobalSkills -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Skills installed." -ForegroundColor Green
} elseif ($TargetSkills) {
    Write-Host "[Info] No .\skills directory found." -ForegroundColor Blue
}

# Generate/Copy Plugin Manifests for Antigravity Agents
if ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide") {
    if (Test-Path "plugin.json") {
        Copy-Item -Path "plugin.json" -Destination $BaseDir -Force -ErrorAction SilentlyContinue
    } else {
        $PluginJsonContent = @"
{
  "name": "$PluginName",
  "version": "2.0.0",
  "description": "Centralized skills for Antigravity"
}
"@
        $PluginJsonPath = Join-Path $BaseDir "plugin.json"
        Set-Content -Path $PluginJsonPath -Value $PluginJsonContent -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path "mcp_config.json") {
        Copy-Item -Path "mcp_config.json" -Destination $BaseDir -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path "hooks.json") {
        Copy-Item -Path "hooks.json" -Destination $BaseDir -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Done! $Agent is now configured ($Scope scope)." -ForegroundColor Cyan
