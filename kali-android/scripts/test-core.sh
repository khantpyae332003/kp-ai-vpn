#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .tools/core-tests
if [[ ! -f .tools/junit.jar || ! -f .tools/hamcrest.jar ]]; then
    exec python3 scripts/gradle.py :kali-core:test
fi
JDK=.tools/jdk-17.0.17+10
CP=.tools/junit.jar:.tools/hamcrest.jar
mapfile -t SOURCES < <(find engine/kali-core/src/main/java engine/kali-core/src/test/java -name '*.java' | sort)
mapfile -t TESTS < <(find engine/kali-core/src/test/java -name '*Test.java' | sed 's|engine/kali-core/src/test/java/||;s|/|.|g;s|.java$||' | sort)
"$JDK/bin/javac" --release 8 -cp "$CP" -d .tools/core-tests "${SOURCES[@]}"
"$JDK/bin/java" -cp ".tools/core-tests:$CP" org.junit.runner.JUnitCore "${TESTS[@]}"
