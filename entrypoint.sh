#!/bin/bash
# Starts HDFS + YARN inside the container and creates /tmp/ready when everything is up.
set -e
rm -f /tmp/ready
export JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(which javac)")")")
echo "export JAVA_HOME=$JAVA_HOME" >> "$HADOOP_CONF_DIR/hadoop-env.sh"

cat > "$HADOOP_CONF_DIR/core-site.xml" <<XML
<configuration>
  <property><name>fs.defaultFS</name><value>hdfs://localhost:9000</value></property>
  <property><name>hadoop.http.staticuser.user</name><value>root</value></property>
</configuration>
XML
cat > "$HADOOP_CONF_DIR/hdfs-site.xml" <<XML
<configuration>
  <property><name>dfs.replication</name><value>1</value></property>
  <property><name>dfs.namenode.name.dir</name><value>file:///data/nn</value></property>
  <property><name>dfs.datanode.data.dir</name><value>file:///data/dn</value></property>
  <property><name>dfs.webhdfs.enabled</name><value>true</value></property>
  <property><name>dfs.permissions.enabled</name><value>false</value></property>
</configuration>
XML
cat > "$HADOOP_CONF_DIR/mapred-site.xml" <<XML
<configuration>
  <property><name>mapreduce.framework.name</name><value>yarn</value></property>
  <property><name>yarn.app.mapreduce.am.env</name><value>HADOOP_MAPRED_HOME=$HADOOP_HOME</value></property>
  <property><name>mapreduce.map.env</name><value>HADOOP_MAPRED_HOME=$HADOOP_HOME</value></property>
  <property><name>mapreduce.reduce.env</name><value>HADOOP_MAPRED_HOME=$HADOOP_HOME</value></property>
</configuration>
XML
cat > "$HADOOP_CONF_DIR/yarn-site.xml" <<XML
<configuration>
  <property><name>yarn.nodemanager.aux-services</name><value>mapreduce_shuffle</value></property>
  <property><name>yarn.nodemanager.vmem-check-enabled</name><value>false</value></property>
  <property><name>yarn.nodemanager.resource.memory-mb</name><value>4096</value></property>
  <property><name>yarn.scheduler.maximum-allocation-mb</name><value>4096</value></property>
</configuration>
XML

[ -d /data/nn/current ] || hdfs namenode -format -force -nonInteractive
hdfs --daemon start namenode
hdfs --daemon start datanode
yarn --daemon start resourcemanager
yarn --daemon start nodemanager

until hdfs dfsadmin -safemode get 2>/dev/null | grep -q OFF; do sleep 3; done
until yarn node -list 2>/dev/null | grep -q RUNNING; do sleep 3; done
touch /tmp/ready
echo "Hadoop is ready: HDFS http://localhost:9870  YARN http://localhost:8088"
exec tail -f /dev/null
