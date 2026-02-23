import os

file_path = '/home/kalki/PYTHON PROJECTS/2-5/LPUM(UMS)/templates/results/student_results.html'

with open(file_path, 'r') as f:
    lines = f.readlines()

errors = []
for i, line in enumerate(lines):
    if ('{{' in line and '}}' not in line) or ('}}' in line and '{{' not in line):
        errors.append(f"Line {i+1}: Token split detected: {line.strip()}")
    if ('{%' in line and '%}' not in line) or ('%}' in line and '{%' not in line):
        # Allow multi-line blocks if they are standard, but check for weird splits
        if 'if' in line or 'for' in line or 'block' in line:
            continue
        errors.append(f"Line {i+1}: Tag split detected: {line.strip()}")

if errors:
    print("ERRORS FOUND:")
    for e in errors:
        print(e)
else:
    print("NO SPLIT TOKENS FOUND")
