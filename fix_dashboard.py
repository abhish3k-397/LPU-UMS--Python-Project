import re

with open('templates/core/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Make all dark:bg-* classes !important where they might conflict
content = re.sub(r'dark:bg-slate-([0-9]+(?:/[0-9]+)?)', r'dark:!bg-slate-\1', content)
content = re.sub(r'dark:bg-blue-([0-9]+(?:/[0-9]+)?)', r'dark:!bg-blue-\1', content)
content = re.sub(r'dark:bg-emerald-([0-9]+(?:/[0-9]+)?)', r'dark:!bg-emerald-\1', content)
content = re.sub(r'dark:bg-purple-([0-9]+(?:/[0-9]+)?)', r'dark:!bg-purple-\1', content)
content = re.sub(r'dark:bg-orange-([0-9]+(?:/[0-9]+)?)', r'dark:!bg-orange-\1', content)
content = re.sub(r'dark:from-orange-([0-9]+(?:/[0-9]+)?)', r'dark:!from-orange-\1', content)
content = re.sub(r'dark:to-rose-([0-9]+(?:/[0-9]+)?)', r'dark:!to-rose-\1', content)
content = re.sub(r'dark:from-blue-([0-9]+(?:/[0-9]+)?)', r'dark:!from-blue-\1', content)
content = re.sub(r'dark:to-indigo-([0-9]+(?:/[0-9]+)?)', r'dark:!to-indigo-\1', content)

# Fix 2: Wrap Django variables in solitary span tags so formators don't break them
# Top Stats
content = re.sub(
    r'<h3 class="text-2xl font-black text-slate-800 dark:text-white m-0 leading-none">\s*\{\{\s*enrolled_courses\.count\s*\}\}\s*</h3>',
    '<h3 class="text-2xl font-black text-slate-800 dark:text-white m-0 leading-none">\n                                <span>{{ enrolled_courses.count }}</span>\n                            </h3>',
    content
)
content = re.sub(
    r'<h3 class="text-2xl font-black text-slate-800 dark:text-white m-0 leading-none">\s*\{\{\s*total_sessions\s*\}\}\s*</h3>',
    '<h3 class="text-2xl font-black text-slate-800 dark:text-white m-0 leading-none">\n                                <span>{{ total_sessions }}</span>\n                            </h3>',
    content
)
content = re.sub(
    r'<h3 class="text-2xl font-black text-slate-800 dark:text-white m-0 leading-none">\s*\{\{\s*remedial_attended\s*\}\}\s*</h3>',
    '<h3 class="text-2xl font-black text-slate-800 dark:text-white m-0 leading-none">\n                                <span>{{ remedial_attended }}</span>\n                            </h3>',
    content
)

# Active Subjects
content = re.sub(
    r'<span\s*class="text-sm font-bold text-slate-700 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-300">\s*\{\{\s*course\.code\|slice:"3:"\s*\}\}\s*</span>',
    '<span class="text-sm font-bold text-slate-700 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-300">\n                                <span>{{ course.code|slice:"3:" }}</span>\n                            </span>',
    content
)

content = re.sub(
    r'<span class="text-sm font-bold text-slate-700 dark:text-slate-200 truncate">Prof\.\s*\{\{\s*course\.faculty\.username\s*\}\}\s*</span>',
    '<span class="text-sm font-bold text-slate-700 dark:text-slate-200 truncate">\n                                Prof. <span>{{ course.faculty.username }}</span>\n                            </span>',
    content
)

with open('templates/core/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement successful")
