<#
.SYNOPSIS
    Installs AI Agent rules, skills, and workflows.

.DESCRIPTION
    Copies the rules, skills, and workflows from the current project structure into
    the target directory corresponding to the specified AI Agent and Scope.

.PARAMETER Agent
    Which agent format to target: antigravity (default), antigravity-ide, or opencode.

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
    [ValidateSet("antigravity", "antigravity-ide", "opencode")]
    [string]$Agent = "antigravity",
    
    [ValidateSet("global", "workspace")]
    [string]$Scope = "global",
    
    [string[]]$Rules = @("all"),
    
    [string]$Path = "",

    [string]$PluginName = "baseline-everything"
)

# Define Base Directories based on Agent and Scope
if ($Scope -eq "workspace") {
    $WorkspaceRoot = if ([string]::IsNullOrWhiteSpace($Path)) { "." } else { $Path }
    switch ($Agent) {
        "antigravity" {
            $BaseDir = Join-Path $WorkspaceRoot ".agents\plugins\$PluginName"
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
            $TargetWorkflows = Join-Path $BaseDir "workflows"
            $LegacyRulesDir = Join-Path $WorkspaceRoot ".agents\rules"
            $LegacySkillsDir = Join-Path $WorkspaceRoot ".agents\skills"
            $LegacyWorkflowsDir = Join-Path $WorkspaceRoot ".agents\workflows"
        }
        "antigravity-ide" {
            $BaseDir = Join-Path $WorkspaceRoot ".agents\plugins\$PluginName"
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
            $TargetWorkflows = Join-Path $BaseDir "workflows"
            $LegacyRulesDir = Join-Path $WorkspaceRoot ".agents\rules"
            $LegacySkillsDir = Join-Path $WorkspaceRoot ".agents\skills"
            $LegacyWorkflowsDir = Join-Path $WorkspaceRoot ".agents\workflows"
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
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
            $TargetWorkflows = Join-Path $BaseDir "workflows"
            $DirectGlobalRules = Join-Path $HOME ".gemini\antigravity-cli\rules"
            $DirectGlobalSkills = Join-Path $HOME ".gemini\antigravity-cli\skills"
            $DirectGlobalWorkflows = Join-Path $HOME ".gemini\antigravity-cli\workflows"
            $SharedRules = Join-Path $HOME ".gemini\rules"
            $SharedSkills = Join-Path $HOME ".gemini\skills"
            $SharedWorkflows = Join-Path $HOME ".gemini\workflows"
        }
        "antigravity-ide" {
            $BaseDir = Join-Path $HOME ".gemini\antigravity-ide\plugins\$PluginName"
            $TargetRules = Join-Path $BaseDir "rules"
            $TargetSkills = Join-Path $BaseDir "skills"
            $TargetWorkflows = Join-Path $BaseDir "workflows"
            $DirectGlobalRules = Join-Path $HOME ".gemini\antigravity-ide\rules"
            $DirectGlobalSkills = Join-Path $HOME ".gemini\antigravity-ide\skills"
            $DirectGlobalWorkflows = Join-Path $HOME ".gemini\antigravity-ide\workflows"
            $SharedRules = Join-Path $HOME ".gemini\rules"
            $SharedSkills = Join-Path $HOME ".gemini\skills"
            $SharedWorkflows = Join-Path $HOME ".gemini\workflows"
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
if ($TargetRules -and -not (Test-Path $TargetRules)) {
    New-Item -ItemType Directory -Path $TargetRules -Force | Out-Null
}
if ($TargetSkills -and -not (Test-Path $TargetSkills)) {
    New-Item -ItemType Directory -Path $TargetSkills -Force | Out-Null
}
if ($TargetWorkflows -and -not (Test-Path $TargetWorkflows)) {
    New-Item -ItemType Directory -Path $TargetWorkflows -Force | Out-Null
}
if ($Scope -eq "workspace" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
    if (-not (Test-Path $LegacyRulesDir)) {
        New-Item -ItemType Directory -Path $LegacyRulesDir -Force | Out-Null
    }
    if (-not (Test-Path $LegacySkillsDir)) {
        New-Item -ItemType Directory -Path $LegacySkillsDir -Force | Out-Null
    }
    if (-not (Test-Path $LegacyWorkflowsDir)) {
        New-Item -ItemType Directory -Path $LegacyWorkflowsDir -Force | Out-Null
    }
} elseif ($Scope -eq "global" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
    foreach ($Dir in @($SharedRules, $SharedSkills, $SharedWorkflows, $DirectGlobalRules, $DirectGlobalSkills, $DirectGlobalWorkflows)) {
        if (-not (Test-Path $Dir)) {
            New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        }
    }
}

# Install Rules
if ($TargetRules -and (Test-Path "rules")) {
    # For other agents or workspace scope, copy everything except GEMINI.md (unless it's antigravity workspace)
    $ExcludeList = @()
    if ($Agent -ne "antigravity" -and $Agent -ne "antigravity-ide") {
        $ExcludeList += "GEMINI.md"
    }
    
    Write-Host "[Packaging] Copying rules from .\rules to $TargetRules..." -ForegroundColor Yellow
    Get-ChildItem -Path "rules" -Filter "*.md" -Recurse -File | Where-Object { 
        ($ExcludeList -notcontains $_.Name) -and 
        ($Rules -contains "all" -or $Rules -contains $_.BaseName -or $Rules -contains $_.Name) 
    } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $TargetRules -Force -ErrorAction SilentlyContinue
        if ($Scope -eq "workspace" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
            Copy-Item -Path $_.FullName -Destination $LegacyRulesDir -Force -ErrorAction SilentlyContinue
        } elseif ($Scope -eq "global" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
            Copy-Item -Path $_.FullName -Destination $SharedRules -Force -ErrorAction SilentlyContinue
            Copy-Item -Path $_.FullName -Destination $DirectGlobalRules -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[OK] Rules installed." -ForegroundColor Green
} elseif ($TargetRules) {
    Write-Host "[Warning] No .\rules directory found." -ForegroundColor DarkYellow
}

# Install Skills
if ($TargetSkills -and (Test-Path "skills")) {
    Write-Host "[Packaging] Copying skills from .\skills to $TargetSkills..." -ForegroundColor Yellow
    Copy-Item -Path "skills\*" -Destination $TargetSkills -Recurse -Force -ErrorAction SilentlyContinue
    if ($Scope -eq "workspace" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
        Copy-Item -Path "skills\*" -Destination $LegacySkillsDir -Recurse -Force -ErrorAction SilentlyContinue
    } elseif ($Scope -eq "global" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
        Copy-Item -Path "skills\*" -Destination $SharedSkills -Recurse -Force -ErrorAction SilentlyContinue
        Copy-Item -Path "skills\*" -Destination $DirectGlobalSkills -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Skills installed." -ForegroundColor Green
} elseif ($TargetSkills) {
    Write-Host "[Info] No .\skills directory found." -ForegroundColor Blue
}

# Install Workflows
if ($TargetWorkflows -and (Test-Path "workflows")) {
    Write-Host "[Packaging] Copying workflows from .\workflows to $TargetWorkflows..." -ForegroundColor Yellow
    Copy-Item -Path "workflows\*" -Destination $TargetWorkflows -Recurse -Force -ErrorAction SilentlyContinue
    if ($Scope -eq "workspace" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
        Copy-Item -Path "workflows\*" -Destination $LegacyWorkflowsDir -Recurse -Force -ErrorAction SilentlyContinue
    } elseif ($Scope -eq "global" -and ($Agent -eq "antigravity" -or $Agent -eq "antigravity-ide")) {
        Copy-Item -Path "workflows\*" -Destination $SharedWorkflows -Recurse -Force -ErrorAction SilentlyContinue
        Copy-Item -Path "workflows\*" -Destination $DirectGlobalWorkflows -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Workflows installed." -ForegroundColor Green
} elseif ($TargetWorkflows) {
    Write-Host "[Info] No .\workflows directory found." -ForegroundColor Blue
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
  "description": "Centralized rules, skills, and workflows for Antigravity"
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
