
def refine_path_and_convert_to_moves(path):
    p = path
    for i in range(len(p) - 2, 0, -1):
        b_sid, c_sid, f_sid = p[i - 1], p[i], p[i + 1]
        b_col, b_row = list(b_sid)
        c_col, c_row = list(c_sid)
        f_col, f_row = list(f_sid)
        if b_col == c_col == f_col:
            p.pop(i)
        if b_row == c_row == f_row:
            p.pop(i)
    return [f"{p[i]}{p[i + 1]}" for i in range(len(p) - 1)]

print(refine_path_and_convert_to_moves(['a1', 'a2', 'a3', 'b3', 'b4', 'b5', 'c5', 'd5', 'e5']))