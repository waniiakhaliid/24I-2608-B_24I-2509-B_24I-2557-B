"""Module: radio (log, six patterns, two reports) incl. trap 49."""
from collections import Counter
from .common import ALPHABET, PATTERN_LENGTHS, ceil_pct


def count_overlap(text, p):
    c, i = 0, text.find(p)
    while i != -1:
        c += 1
        i = text.find(p, i + 1)
    return c


def _rand_str(rng, n, alpha=ALPHABET):
    return "".join(rng.choice(alpha) for _ in range(n))


def _beacon_log(rng, N):
    dom = rng.choice(ALPHABET)
    others = [c for c in ALPHABET if c != dom]
    msgs = [''.join(dom if rng.random() < 0.45 else rng.choice(others) for _ in range(rng.randint(8, 25)))
            for _ in range(rng.randint(3, 5))]
    parts, tot = [], 0
    while tot < N:
        m = rng.choice(msgs)
        parts.append(m)
        tot += len(m)
    t = list(''.join(parts)[:N])
    need = ceil_pct(N, 28)
    cnt = t.count(dom)
    if cnt < need:
        for i in rng.sample([i for i, c in enumerate(t) if c != dom], need - cnt):
            t[i] = dom
    return ''.join(t)


def gen_log(rng, N, scen):
    if scen == 6:
        return _beacon_log(rng, N)
    bank = [_rand_str(rng, rng.choice([3, 5, 8, 12, 20])) for _ in range(rng.randint(4, 8))]
    parts, tot = [], 0
    while tot < N:
        s = rng.choice(bank) if rng.random() < 0.3 else _rand_str(rng, rng.randint(1, 12))
        parts.append(s)
        tot += len(s)
    t = list(''.join(parts)[:N])
    if scen == 3:  # noisy radio: at least 30 of the 38 symbols (aim for 34+)
        cnt = Counter(t)
        for ch in [c for c in ALPHABET if c not in cnt]:
            if len(cnt) >= 34:
                break
            while True:
                i = rng.randrange(N)
                if cnt[t[i]] > 1:
                    break
            cnt[t[i]] -= 1
            t[i] = ch
            cnt[ch] += 1
    return ''.join(t)


def gen_patterns(rng, text):
    """Six patterns (2,4,8,12,20,40). 0,1 always occur; 5 never does; 2-4 are near-misses or hits."""
    N, pats = len(text), []
    for idx, m in enumerate(PATTERN_LENGTHS):
        if idx in (0, 1) or (idx < 5 and rng.random() < 0.5):
            i = rng.randint(0, N - m)
            p = text[i:i + m]
        else:
            p = None
            for _ in range(200):  # near-miss: a real substring with a wrong last symbol
                i = rng.randint(0, N - m)
                q = text[i:i + m - 1] + rng.choice([c for c in ALPHABET if c != text[i + m - 1]])
                if count_overlap(text, q) == 0:
                    p = q
                    break
            while p is None or count_overlap(text, p) != 0:
                p = _rand_str(rng, m)
        pats.append((idx, p, count_overlap(text, p)))
    return pats


def split_parts(text):
    return [(i + 1, text[o:o + 10000]) for i, o in enumerate(range(0, len(text), 10000))]


def trap49(rng):
    """Log = one symbol repeated (>= 94%) + a short noise tail that never uses the reserved symbol z.
    Patterns a^(m-1)+z (m = 8,12,20,40) never occur, but their (m-1)-prefix matches at ~95% of positions."""
    N = rng.randint(50000, 100000)
    a, z = rng.sample(ALPHABET, 2)
    noise_alpha = [c for c in ALPHABET if c not in (a, z)]
    nz = rng.randint(N // 100, N // 20)
    text = a * (N - nz) + _rand_str(rng, nz, noise_alpha)
    pats = [(0, a * 2), (1, a * 4)] + [(i, a * (m - 1) + z) for i, m in enumerate(PATTERN_LENGTHS) if i >= 2]
    return text, [(i, p, count_overlap(text, p)) for i, p in pats]


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            x = prev[j - 1] + (ca != cb)
            y = prev[j] + 1
            z = cur[j - 1] + 1
            cur[j] = x if x < y and x < z else (y if y < z else z)
        prev = cur
    return prev[-1]


def gen_reports(rng, lo, hi):
    small = rng.sample(ALPHABET, rng.randint(4, 12))
    a = _rand_str(rng, rng.randint(lo, hi), small)
    rate, out = rng.uniform(0.05, 0.3), []
    for ch in a:
        r = rng.random()
        if r < rate / 3:
            continue
        out.append(rng.choice(small) if r < 2 * rate / 3 else ch)
        if 2 * rate / 3 <= r < rate:
            out.append(rng.choice(small))
    b = ''.join(out)[:hi]
    b += _rand_str(rng, max(0, lo - len(b)), small)
    bound = min(len(a) + len(b), edit_distance(a, b) + rng.randint(0, 2))
    return a, b, bound
