#!/bin/bash
# Runs INSIDE the container: partitioned CSVs -> HDFS -> Hadoop Streaming (mapper.py / reducer.py) -> result file.
# HDFS layout:  /earthscape/input/year=YYYY/station=NAME/climate.csv
set -e
IN=/earthscape/input
OUT=/earthscape/output/monthly
hdfs dfs -mkdir -p /earthscape
hdfs dfs -rm -r -f "$IN" >/dev/null 2>&1 || true
hdfs dfs -put /project/data/hdfs_partitioned "$IN"
hdfs dfs -rm -r -f "$OUT" >/dev/null 2>&1 || true
JAR=$(ls "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar | head -1)
hadoop jar "$JAR" \
  -D mapreduce.input.fileinputformat.input.dir.recursive=true \
  -files file:///project/mapper.py,file:///project/reducer.py \
  -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
  -input "$IN" -output "$OUT"
mkdir -p /project/data/hadoop_output
hdfs dfs -cat "$OUT"/part-* > /project/data/hadoop_output/part-00000.tsv
echo "Output rows: $(wc -l < /project/data/hadoop_output/part-00000.tsv)"
hdfs dfs -ls -R "$IN" | head -25
