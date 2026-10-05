
t, s = "a", "n"

counter = [0] * 26

for a, b in zip(t,s):
    print(ord(a), ord(b))
    counter[ord(a)-97] += 1
    counter[ord(b)-97] -= 1

print(all(c == 0 for c in counter))


def anagramCheck(t, s: str) -> bool:
    count = dict()
    for c in t:
        if c in count:
            count[c] += 1
        else:
            count[c] = 1

    for c in s:
        if c not in count or count[c] == 0: return False
        count[c] -= 1
    return True
print(anagramCheck(t, s))
            
