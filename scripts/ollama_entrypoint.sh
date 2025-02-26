#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
# Record Process ID.
pid=$!

# Pause for Ollama to start.
sleep 5

model="deepseek-r1:1.5b"

echo "🔴 Retrieve ${model} "
ollama pull ${model}
echo "🟢 Done!"

# Wait for Ollama process to finish.
wait $pid