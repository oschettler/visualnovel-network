#!/bin/bash
# Erzeugt SVG-Diagramme aus den nomnoml-Quelldateien
# Aufruf: ./build/generate-diagrams.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIAGRAMS_SRC="$PROJECT_DIR/diagrams"
DIAGRAMS_OUT="$PROJECT_DIR/src/diagrams"

if ! command -v nomnoml &> /dev/null; then
    echo "Fehler: nomnoml ist nicht installiert"
    echo "Installieren mit: npm install -g nomnoml"
    exit 1
fi

mkdir -p "$DIAGRAMS_OUT"

echo "Generiere Diagramme..."

count=0
for file in "$DIAGRAMS_SRC"/*.nomnoml; do
    if [ -f "$file" ]; then
        basename="${file##*/}"
        name="${basename%.nomnoml}"
        output="$DIAGRAMS_OUT/${name}.svg"

        nomnoml "$file" "$output"
        echo "  erzeugt: ${name}.svg"
        count=$((count+1))
    fi
done

echo "Fertig: $count Diagramme erzeugt"
