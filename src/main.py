import os
import sys

from agent import agent

print("Financial Agent")
print("Ask for an asset analysis, for example: Analyze AAPL daily")
print("You can also ask: Analyze BTC-USD hourly")
print("The agent reads CSV files from data/raw and graphical analysis from outputs/frontend_payload.json")
print("Type exit to stop.\n")

while True:
    question = input("Ask AI: ").strip()

    if question.lower() in {"exit", "quit"}:
        print("Goodbye.")
        sys.stdout.flush()
        os._exit(0)

    if not question:
        continue

    response = agent.invoke(question)

    print(f"\n{response['output']}\n")
