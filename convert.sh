#!/bin/bash
# Сохраняем оригиналы? (true/false)
KEEP_ORIGINAL=false

# Расширения для конвертации
EXTENSIONS=("py" "js" "yml" "Makefile" "sql" "json" "html" "css" "Dockerfile" "csv")

for ext in "${EXTENSIONS[@]}"; do
    for file in *."$ext"; do
        if [ -f "$file" ]; then
            if [ "$KEEP_ORIGINAL" = true ]; then
                cp "$file" "${file%.$ext}.md"
            else
                mv "$file" "${file%.$ext}.md"
            fi
            echo "Конвертирован: $file -> ${file%.$ext}.md"
        fi
    done
done
