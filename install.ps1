# CATWIZ-ytdl installer for Windows PowerShell
function Install-CatwizYtdl {
    $repo = 'https://github.com/Dr-Jesus1225/ytdl-termux.git'
    $dir = Join-Path $HOME 'CATWIZ-ytdl'

    function Test-Cmd($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }
    function Test-Py {
        if (-not (Test-Cmd 'py')) { return $false }
        py -3 --version *> $null
        return ($LASTEXITCODE -eq 0)
    }
    function Test-YtDlp {
        if (-not (Test-Py)) { return $false }
        py -3 -m pip show yt-dlp *> $null
        return ($LASTEXITCODE -eq 0)
    }
    function Update-SessionPath {
        $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    }

    $items = @(
        @{ Name = 'Git';    Id = 'Git.Git';            Size = 350; Found = (Test-Cmd 'git') },
        @{ Name = 'Python'; Id = 'Python.Python.3.12'; Size = 100; Found = (Test-Py) },
        @{ Name = 'FFmpeg'; Id = 'Gyan.FFmpeg';        Size = 300; Found = (Test-Cmd 'ffmpeg') },
        @{ Name = 'yt-dlp'; Id = $null;                Size = 20;  Found = (Test-YtDlp) }
    )

    $found = @($items | Where-Object { $_.Found } | ForEach-Object { $_.Name })
    $missing = @($items | Where-Object { -not $_.Found })
    $total = 0
    foreach ($m in $missing) { $total += $m.Size }

    Write-Host ''
    Write-Host '======================================' -ForegroundColor Cyan
    Write-Host ' CATWIZ-ytdl installer'
    Write-Host '--------------------------------------' -ForegroundColor Cyan
    Write-Host 'CATWIZ-ytdl needs: Git, Python, FFmpeg, yt-dlp'
    if ($found.Count -gt 0) { Write-Host ('Found:   ' + ($found -join ', ')) } else { Write-Host 'Found:   none' }

    if ($missing.Count -gt 0) {
        $list = ($missing | ForEach-Object { '{0} (~{1} MB)' -f $_.Name, $_.Size }) -join ', '
        Write-Host ('Missing: ' + $list)
        Write-Host ('Total to install: about {0} MB' -f $total)
        do {
            $ans = (Read-Host 'Install the missing items? [y/n]').Trim().ToLower()
        } while ($ans -ne 'y' -and $ans -ne 'n')
        if ($ans -eq 'n') { Write-Host 'Install cancelled.'; return }
    } else {
        Write-Host 'Everything is already installed.' -ForegroundColor Green
    }
    Write-Host ''

    $needWinget = @($missing | Where-Object { $_.Id })
    if ($needWinget.Count -gt 0) {
        if (-not (Test-Cmd 'winget')) {
            Write-Host 'winget was not found. Install "App Installer" from the Microsoft Store, then run this again.' -ForegroundColor Red
            return
        }
        foreach ($m in $needWinget) {
            Write-Host ('Installing ' + $m.Name + '...')
            winget install -e --id $m.Id --accept-package-agreements --accept-source-agreements
        }
        Update-SessionPath
    }

    if (-not (Test-Cmd 'git') -or -not (Test-Py) -or -not (Test-Cmd 'ffmpeg')) {
        Write-Host 'Something did not install correctly. Close this window, open a new PowerShell, and run the command again.' -ForegroundColor Red
        return
    }

    if (Test-Path (Join-Path $dir '.git')) {
        git -C $dir pull
    } elseif (Test-Path $dir) {
        Write-Host "$dir already exists and is not a git copy, leaving it as it is." -ForegroundColor Yellow
    } else {
        git clone $repo $dir
        if ($LASTEXITCODE -ne 0) { Write-Host 'Could not download the project.' -ForegroundColor Red; return }
    }

    py -3 -m pip install -U yt-dlp
    if ($LASTEXITCODE -ne 0) { Write-Host 'Could not install yt-dlp.' -ForegroundColor Red; return }

    # ytdl shortcut: a small .cmd file in a folder that is normally already on PATH
    $shortcutNote = ''
    $shortcutOk = $false
    try {
        $binDir = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps'
        if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }
        # One line on purpose: cmd reads it fully before running, so the file can be deleted while it runs
        $cmdLine = '@echo off & pushd "%TEMP%" & py -3 "%USERPROFILE%\CATWIZ-ytdl\main_cli.py" %* & popd'
        Set-Content -Path (Join-Path $binDir 'ytdl.cmd') -Value $cmdLine -Encoding ASCII
        $shortcutOk = $true
        $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        if (($userPath -split ';') -notcontains $binDir) {
            [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ';' + $binDir), 'User')
            $env:Path = $env:Path + ';' + $binDir
            $shortcutNote = ' (open a new terminal first)'
        }
    } catch {
        Write-Host ('Could not create the ytdl shortcut: ' + $_.Exception.Message) -ForegroundColor Yellow
    }

    Write-Host ''
    if ($shortcutOk) {
        Write-Host ('Installed. Starting CATWIZ-ytdl (type ytdl next time' + $shortcutNote + ').') -ForegroundColor Green
    } else {
        Write-Host 'Installed. Starting CATWIZ-ytdl.' -ForegroundColor Green
    }
    # Run from the temp folder so nothing keeps the program folder locked (needed for uninstall)
    Push-Location $env:TEMP
    try { py -3 (Join-Path $dir 'main_cli.py') } finally { Pop-Location }
}

Install-CatwizYtdl
