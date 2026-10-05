import sys
import time

from rag import ask, gen, MODEL

K = int(sys.argv[1]) if len(sys.argv) > 1 else 4


def judge(q, ref, ans):
    p = (
        f"Question: {q}\nReference answer: {ref}\nBot answer: {ans}\n"
        "Does the bot answer convey the same key information as the reference? "
        "Reply with only YES or NO."
    )
    r = gen(model=MODEL, contents=p)
    return r.text.strip().upper().startswith("YES")


rows = [l.strip() for l in open("questions.txt", encoding="utf-8") if l.strip()]
score = 0
errors = 0
page_hits = 0
page_total = 0
wrong = []

for n, line in enumerate(rows, 1):
    q, ref, page = [x.strip() for x in line.split("|")]
    has_page = page.lower() != "none"
    try:
        ans, src = ask(q, k=K)
        if has_page:
            ok = judge(q, ref, ans)
        else:
            ok = "could not find" in ans.lower()
    except Exception as e:
        ans, src, ok = f"ERROR: {e}", [], False
        errors += 1
    if has_page:
        page_total += 1
        if any(str(m["page"]) == page for m in src):
            page_hits += 1
    score += ok
    print(f"{n:2d}. {'OK ' if ok else 'BAD'} {q}")
    if not ok:
        wrong.append(f"{q} | bot: {ans[:150]}")
    time.sleep(6)

print(f"\nK={K}  SCORE: {score}/{len(rows)} = {score / len(rows) * 100:.0f}%")
print(f"API errors: {errors}")
print(f"Correct page retrieved: {page_hits}/{page_total}")
with open(f"wrong_k{K}.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(wrong))
print(f"Galat sawal wrong_k{K}.txt mein save hue.")