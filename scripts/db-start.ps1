$ErrorActionPreference = "Stop"

$Name = "medsync-postgres"
$Volume = "medsync-pgdata"
$HostPort = 5434

if (docker ps --filter "name=^/$Name$" --format "{{.Names}}") {
    Write-Host "$Name is already running on port $HostPort"
    exit 0
}

if (docker ps -a --filter "name=^/$Name$" --format "{{.Names}}") {
    docker start $Name | Out-Null
}
else {
    docker run -d `
        --name $Name `
        -e POSTGRES_USER=postgres `
        -e POSTGRES_PASSWORD=postgres `
        -e POSTGRES_DB=medsync `
        -p "${HostPort}:5432" `
        -v "${Volume}:/var/lib/postgresql/data" `
        pgvector/pgvector:pg17 | Out-Null
}

$attempts = 0
$ready = $false
while ($attempts -lt 60 -and -not $ready) {
    docker exec $Name pg_isready -U postgres *> $null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
    }
    else {
        Start-Sleep -Milliseconds 500
    }
    $attempts++
}

if (-not $ready) {
    Write-Error "postgres did not become ready"
}

Write-Host "postgres ready on localhost:$HostPort (database: medsync)"
