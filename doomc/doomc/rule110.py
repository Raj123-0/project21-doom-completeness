"""Bounded, periodic Rule 110; compile-time reference, not Doom computation."""

def cell(left, center, right):
    return (110 >> (4 * left + 2 * center + right)) & 1


def trace(initial, steps):
    if not initial or any(type(b) is not int or b not in (0, 1) for b in initial):
        raise ValueError("initial must be a nonempty list of binary integers")
    if type(steps) is not int or not 0 <= steps <= 31 or len(initial) > 32:
        raise ValueError("bounded backend supports width 1..32 and steps 0..31")
    rows = [list(initial)]
    for _ in range(steps):
        old = rows[-1]
        rows.append([cell(old[(i-1) % len(old)], old[i], old[(i+1) % len(old)])
                     for i in range(len(old))])
    return rows
