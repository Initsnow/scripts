# ====================================================================
# setup_scoop_and_run_deploy.ps1
# Description:
#   1. Check if Scoop is installed in the user's home directory (non-administrator installation).
#   2. If Scoop is not installed, set the execution policy to RemoteSigned and install Scoop via the web script.
#   3. Install jq and git using Scoop.
#   4. Locate the Bash executable (provided by Git) from the PATH.
#   5. Assume that the deploy.sh script is in the current directory and run it using Git Bash.
# ====================================================================

# 1. Check if Scoop is installed (by checking if the 'scoop' folder exists in the user's home directory)
if (-not (Test-Path "$env:USERPROFILE\scoop")) {
    Write-Output "Scoop not detected, starting Scoop installation..."
    
    # Set the execution policy for the current user to RemoteSigned (affects only the current user in non-administrator mode)
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

    # Download and run the Scoop installation script
    try {
        iwr -UseB get.scoop.sh | iex
        Write-Output "Scoop installed successfully."
    }
    catch {
        Write-Error "Scoop installation failed. Please check your internet connection or execution policy settings."
        exit 1
    }
}
else {
    Write-Output "Scoop is already installed."
}

# 2. Install jq and git using Scoop
Write-Output "Installing jq and git using Scoop..."
scoop install jq git

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install jq or git using Scoop!"
    exit 1
}

# 3. Locate the Bash executable (should be Git Bash) from PATH
$bashPath = (Get-Command bash.exe -ErrorAction SilentlyContinue).Source
if (-not $bashPath) {
    Write-Error "bash.exe not found. Please ensure that Git is correctly installed and added to PATH."
    exit 1
}
else {
    Write-Output "Found bash.exe at: $bashPath"
}

# 4. Check if the deploy.sh script exists in the current directory
$deployScript = Join-Path -Path (Get-Location) -ChildPath "deploy.sh"
if (-not (Test-Path $deployScript)) {
    Write-Error "deploy.sh not found in the current directory. Please ensure the file exists."
    exit 1
}

# 5. Run the deploy.sh script using Git Bash
Write-Output "Running deploy.sh via Git Bash..."
& "$bashPath" "$deployScript"
