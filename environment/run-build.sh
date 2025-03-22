#!/usr/bin/env bash

files_limit=1048576
if [ "$(ulimit -n)" -gt $files_limit ]; then
  ulimit -n $files_limit || exit 2
fi

if [ -z "$JAVA_TOOL_OPTIONS" ]; then
  unset JAVA_TOOL_OPTIONS
fi

cp -r "$PROJECT_SRC/." . || exit 2

builder=$1

case "$builder" in
  gradlew | mvnw | antw)
    builder="source ./$builder"
esac

case "$1" in
  gradle | gradlew)
    command="$builder clean assemble --no-daemon --stacktrace --console=plain" ;;
  mvn | mvnw)
    command="$builder clean package -DskipTests --errors --batch-mode" ;;
  ant | antw)
    command="$builder clean; $builder jar || $builder war || $builder dist || $builder -verbose" ;;
  *)
    echo "Usage: $0 gradle|gradlew|..."
    exit 2
esac

timeout -k1m 1h bash -c "$command" </dev/null 2>&1
