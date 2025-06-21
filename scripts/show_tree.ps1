$basePath = Get-Location

# Define icons for directories and files
$folderSymbol = "[D]"
$fileSymbol = "[F]"
$indentation = "    "

# Use only normal ASCII characters for the connectors
$branchConnector = "|-- "
$lastBranchConnector = "``-- "
$verticalLine = "|   "

# Function for recursive display of the directory structure
function Show-Tree {
    param (
        [string]$Path,
        [int]$Level = 0,
        [string]$CurrentPrefix = ""
    )

    $items = Get-ChildItem -Path $Path -Force |
             Where-Object {
                 # Ensure that the match is applied to the complete path
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\\.pytest_cache' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\\.git' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\\.ruff' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\\.venv' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\\.github' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\build' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\dist' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\\.idea' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\htmlcov' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\__pycache__' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\__main__' -and
                 $_.FullName -notmatch [regex]::Escape($basePath.FullName) + '\\site' -and
                 $_.FullName -notmatch '\.pyc$' # Matches any .pyc file, regardless of path
             } |
             Sort-Object -Property @{Expression={$_.PSIsContainer}; Descending=$true}, Name # Explizite Sortierung

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $isLast = ($i -eq ($items.Count - 1))

        $connector = if ($isLast) { $lastBranchConnector } else { $branchConnector }

        $displaySymbol = if ($item.PSIsContainer) { $folderSymbol } else { $fileSymbol }

        Write-Host "$CurrentPrefix$connector$displaySymbol $($item.Name)"

        if ($item.PSIsContainer) {
            $nextPrefix = if ($isLast) { $CurrentPrefix + $indentation } else { $CurrentPrefix + $verticalLine }
            Show-Tree -Path $item.FullName -Level ($Level + 1) -CurrentPrefix $nextPrefix
        }
    }
}

# Start the display from the current path
Show-Tree -Path $basePath.Path