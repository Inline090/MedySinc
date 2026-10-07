# Stops the MedSync PostgreSQL Docker container if it is running.
$Name = "medsync-postgres"

if (docker ps --filter "name=^/$Name$" --format "{{.Names}}") {
    docker stop $Name | Out-Null
    Write-Host "$Name stopped"
}
else {
    Write-Host "$Name is not running"
}
