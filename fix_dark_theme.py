import re

files = [
    '/home/kalki/PYTHON PROJECTS/2-5/LPU-UMS--Python-Project/templates/results/manage_grades.html',
    '/home/kalki/PYTHON PROJECTS/2-5/LPU-UMS--Python-Project/templates/results/manage_section_exams.html',
    '/home/kalki/PYTHON PROJECTS/2-5/LPU-UMS--Python-Project/templates/results/manage_exam_marks.html'
]

def fix_dark(match):
    prefix = match.group(1) # 'dark:' or 'hover:', etc.
    cls = match.group(2) # the utility class
    if not cls.startswith('!'):
        return f"{prefix}!{cls}"
    return match.group(0)

# Pattern to catch dark:, dark:hover:, dark:focus:, dark:group-hover:, hover:, etc.
pattern = re.compile(r'(dark:(?:(?:hover|focus|group-hover):)?)([\w\-/#]+)')

for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    # 1. Fix missing !
    content = pattern.sub(fix_dark, content)
    
    # 2. Fix broken django tags split across lines that break formatting
    content = re.sub(r'\{\{([^}]+)\}\}', lambda m: '{{ ' + ' '.join(m.group(1).split()) + ' }}', content)
    content = re.sub(r'\{%([^%]+)%\}', lambda m: '{% ' + ' '.join(m.group(1).split()) + ' %}', content)

    with open(f, 'w') as file:
        file.write(content)
print("Finished fixing templates")
