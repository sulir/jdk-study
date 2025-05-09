#!/usr/bin/env bash

FILES_LIMIT=1048576
ERR_OTHER=2

if [ "$(ulimit -n)" -gt $FILES_LIMIT ]; then
  ulimit -n $FILES_LIMIT || exit $ERR_OTHER
fi

if [ -z "$JAVA_TOOL_OPTIONS" ]; then
  unset JAVA_TOOL_OPTIONS
fi

if [ ! -d "$PROJECT_SRC" ]; then
  echo "Project should be mounted at $PROJECT_SRC"
  exit $ERR_OTHER
fi

cp -r "$PROJECT_SRC/." . || exit $ERR_OTHER

builder=$1

case "$builder" in
  gradlew | mvnw | antw)
    builder="bash ./$builder"
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
    exit $ERR_OTHER
esac

timeout -k1m 1h bash -c "$command" </dev/null 2>&1
