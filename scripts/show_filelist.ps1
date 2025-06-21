$basePath = (Get-Location).Path

Get-ChildItem -Recurse -Force |
Where-Object {
    $_.FullName -notmatch '\.pytest_cache|\.git|\.ruff|\.venv|\.github|\\build|\\dist|\.idea|\\htmlcov|\\__pycache__|\\__main__|\\__init__|\\site|\.pyc$'
} |
ForEach-Object {
    $relativePath = $_.FullName.Substring($basePath.Length)
    # Falls der Pfad nicht mit "\" beginnt (z.B. gleiche Ebene), manuell voranstellen
    if (-not $relativePath.StartsWith("\")) {
        $relativePath = "\" + $relativePath
    }
    Write-Output $relativePath
}
