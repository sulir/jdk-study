FROM ubuntu:24.04

ENV JAVA_HOME=/opt/java

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    ca-certificates \
    p11-kit \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG GRADLE
RUN curl -L "https://services.gradle.org/distributions/gradle-${GRADLE:?}-bin.zip" -o /tmp/gradle.zip && \
    unzip -q /tmp/gradle.zip -d /opt && \
    rm -f /tmp/gradle.zip && \
    ln -s /opt/gradle-*/bin/gradle /usr/bin/

ARG MAVEN
RUN curl "https://archive.apache.org/dist/maven/maven-3/${MAVEN:?}/binaries/apache-maven-${MAVEN:?}-bin.tar.gz" \
    | tar -xzC /opt && \
    ln -s /opt/apache-maven-*/bin/mvn /usr/bin/

ARG ANT
ARG IVY
RUN curl "https://dlcdn.apache.org/ant/binaries/apache-ant-${ANT:?}-bin.tar.gz" \
    | tar -xzC /opt && \
    ln -s /opt/apache-ant-*/bin/ant /usr/bin/ && \
    curl "https://archive.apache.org/dist/ant/ivy/${IVY:?}/apache-ivy-${IVY:?}-bin.tar.gz" \
    | tar -xzC /opt && \
    ln -s /opt/apache-ivy-*/ivy-*.jar /opt/apache-ant-*/lib/

ARG ZULU
ARG JDK
RUN curl "https://cdn.azul.com/zulu/bin/zulu${ZULU:?}-ca-jdk${JDK:?}-linux_x64.tar.gz" \
    | tar -xz --one-top-level=$JAVA_HOME --strip-components=1 && \
    find $JAVA_HOME/bin/* ! -name apt -exec ln -s {} /usr/bin/ \; && \
    [ -d $JAVA_HOME/lib/security ] && dir=$JAVA_HOME/lib/security || dir=$JAVA_HOME/jre/lib/security && \
    trust extract --format=java-cacerts --overwrite $dir/cacerts

ARG BOUNCY_CASTLE
RUN if [ -z "$BOUNCY_CASTLE" ]; then exit 0; fi && \
    url=https://repo1.maven.org/maven2/org/bouncycastle && \
    for library in bcprov bcprov-ext bctls; do \
      curl "$url/${library}-jdk15to18/$BOUNCY_CASTLE/${library}-jdk15to18-$BOUNCY_CASTLE.jar" \
      > $JAVA_HOME/jre/lib/ext/$library.jar; \
    done && \
    \
    file=$JAVA_HOME/jre/lib/security/java.security && \
    perl -i -pe 's/^(security\.provider\.)(\d+)/$1.($2+2)/eg' $file && \
    providers="security.provider.1=org.bouncycastle.jce.provider.BouncyCastleProvider\n" && \
    providers="${providers}security.provider.2=org.bouncycastle.jsse.provider.BouncyCastleJsseProvider\n" && \
    sed -i "s/^security\.provider\.3=.*/$providers\0/" $file
