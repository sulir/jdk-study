#!/usr/bin/env bash

ULIMIT_FILES=1048576

if [ "$(ulimit -n)" -gt $ULIMIT_FILES ]; then
  ulimit -n $ULIMIT_FILES
fi

cp -r "$PROJECT_SRC/." .

builder=$1
if [[ $builder == *w ]]; then
  builder="source ./$builder"
fi

case "$1" in
  gradle | gradlew)
    command="$builder clean assemble --no-daemon --stacktrace --console=plain" ;;
  mvn | mvnw)
    command="$builder clean package -DskipTests --batch-mode" ;;
  ant | antw)
    command="$builder clean; $builder jar || $builder war || $builder dist || $builder" ;;
  *)
    echo "Usage: $0 gradle|gradlew|..."
    exit 1 ;;
esac

timeout -k1m 1h bash -c "$command" </dev/null 2>&1
