# Full pipeline on Windows (PowerShell). Needs Docker Desktop running.
#   .\hadoop\run_pipeline.ps1          (run from the project root, EarthScape_py)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$sw = [System.Diagnostics.Stopwatch]::StartNew()

Write-Host "1/4  MongoDB -> data\climate_for_hdfs.csv"
python hadoop\bridge.py export

Write-Host "2/4  Starting Hadoop (first run downloads ~700 MB and takes a few minutes)"
Set-Location "$root\hadoop"
docker compose up -d --build
for ($i = 0; $i -lt 60; $i++) {
    docker exec earthscape-hadoop test -f /tmp/ready 2>$null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 5
}
if ($LASTEXITCODE -ne 0) { throw "Hadoop did not become ready. Check: docker logs earthscape-hadoop" }

Write-Host "3/4  CSV -> HDFS -> MapReduce (Hadoop Streaming)"
docker exec earthscape-hadoop bash -c 'tr -d "\r" < /project/hadoop/hdfs_job.sh | bash'
if ($LASTEXITCODE -ne 0) { throw "Hadoop job failed" }

Write-Host "4/4  Result -> MongoDB (shows in Pipeline Monitor)"
Set-Location $root
python hadoop\bridge.py import --engine hadoop --seconds ([math]::Round($sw.Elapsed.TotalSeconds, 1))
Write-Host "Done. HDFS UI: http://localhost:9870   YARN UI: http://localhost:8088"
