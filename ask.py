"""Command-line demo:  python ask.py beach-resort "Can a guest bring a dog?" """

import sys

from src.generate import answer
from src.retrieve import Retriever

if len(sys.argv) < 3:
    sys.exit('Usage: python ask.py <property> "<question>"')

prop, question = sys.argv[1], " ".join(sys.argv[2:])
hits = Retriever().search(question, prop)
result = answer(question, prop, hits)
print("\n" + result["answer"] + "\n")
for c in result["citations"]:
    print(f"  [{c['n']}] {c['source']} > {c['section']}")
