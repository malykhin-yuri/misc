"""
Get array of merged numbers.

Given an m-bit number base and list of n indices {0..m+n-1}, for any n-bit number x
we merge it with m-bit base, putting x's bits in given positions.
For example, if m=5, base=0b01101, index_list=[3,0]; x=0b01, then merged number is:
0b1010101
  ^  ^     <- bits "^" come from x
  0  3
Returns: the list of merged numbers for x in range(2^n).
Note: this corresponds to the usual "msb" qbits numeration.
"""
def merge_bits_array(m, base, index_list):
    n = len(index_list)
    index_set = set(index_list)

    base_index = 0
    merged_base = 0
    for j in range(n + m):
        if j in index_set:
            # here comes bit from x, so nothing to do
            continue
        if base & (1 << (m - 1 - base_index)) != 0:
            merged_base |= (1 << (n + m - 1 - j))
        base_index += 1

    merged_list = []
    for x in range((1<<n)):
        merged = merged_base
        for i, j in enumerate(index_list):
            if x & (1 << (n - 1 - i)) != 0:
                merged |= (1 << (n + m - 1 - j))
        merged_list.append(merged)

    return merged_list
