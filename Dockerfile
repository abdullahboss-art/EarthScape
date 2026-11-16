# Single-container Hadoop 3.3.6 (HDFS + YARN, pseudo-distributed) with python3 for Hadoop Streaming.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      openjdk-11-jdk-headless python3 curl ca-certificates procps \
    && rm -rf /var/lib/apt/lists/*
ARG HADOOP_VERSION=3.3.6
RUN curl -fsSL https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    | tar -xz -C /opt && ln -s /opt/hadoop-${HADOOP_VERSION} /opt/hadoop
ENV HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    HDFS_NAMENODE_USER=root HDFS_DATANODE_USER=root HDFS_SECONDARYNAMENODE_USER=root \
    YARN_RESOURCEMANAGER_USER=root YARN_NODEMANAGER_USER=root
ENV PATH=$PATH:/opt/hadoop/bin:/opt/hadoop/sbin
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh
EXPOSE 9870 8088 9864
ENTRYPOINT ["/entrypoint.sh"]
