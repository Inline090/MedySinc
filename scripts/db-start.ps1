$ErrorActionPreference = "Stop"

$Name = "medsync-postgres"
$Volume = "medsync-pgdata"
$HostPort = 5434

$running = docker ps --filter "name=^/$Name$" --format "{{.Names}}"
$exists = docker ps -a --filter "name=^/$Name$" --format "{{.Names}}"

if (-not $running) {
    if ($exists) {
        docker start $Name | Out-Null
    }
    else {
        docker run -d `
            --name $Name `
            --restart unless-stopped `
            -e POSTGRES_USER=postgres `
            -e POSTGRES_PASSWORD=postgres `
            -e POSTGRES_DB=medsync `
            -p "${HostPort}:5432" `
            -v "${Volume}:/var/lib/postgresql/data" `
            pgvector/pgvector:pg17 | Out-Null
    }
}

docker update --restart unless-stopped $Name | Out-Null

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
