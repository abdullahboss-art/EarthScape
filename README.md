# Hadoop pipeline (EarthScape)

Flow: MongoDB -> CSV (partitioned by year and station) -> HDFS -> Hadoop Streaming (mapper.py / reducer.py on YARN) -> MongoDB -> Pipeline Monitor page.

HDFS layout: /earthscape/input/year=YYYY/station=NAME/climate.csv  (output: /earthscape/output/monthly)

## Requirements
Docker Desktop (running), Python with the project's requirements, MongoDB running.

## Run (Windows PowerShell, from the project root)
    .\hadoop\run_pipeline.ps1
First run builds the image (downloads Hadoop 3.3.6, about 700 MB). Later runs take about a minute.

## Show real HDFS numbers in the app
Add this line at the TOP of .streamlit/secrets.toml (above the [smtp] section):
    HDFS_URL = "http://localhost:9870"

## Without Docker (fallback / quick test)
    python hadoop\bridge.py demo
Runs the same mapper.py and reducer.py locally (engine is shown as "streaming-local").

## Useful
    docker logs earthscape-hadoop            Hadoop start-up log
    docker exec earthscape-hadoop hdfs dfs -ls -R /earthscape
    docker compose -f hadoop\docker-compose.yml down        stop (add -v to delete HDFS data)
UI: HDFS http://localhost:9870   YARN http://localhost:8088
