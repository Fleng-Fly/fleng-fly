from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
p = root / 'frontend/team.html'
s = p.read_text(encoding='utf-8')
icons = iter(['pen', 'code', 'screen', 'shield', 'shield', 'cap', 'case'])
s = re.sub(r'<span aria-hidden="true">[^<]*</span>(?=UI/UX|Full Stack|Frontend|Q&A|Mentor|Project Manager)', lambda m: '<svg aria-hidden="true"><use href="/assets/figma/icons.svg#' + next(icons) + '" /></svg>', s)
p.write_text(s, encoding='utf-8')

base = (root / 'frontend/assets/figma/avatar.svg').read_text()
for i, (skin, shirt, triangle) in enumerate([
    ('#ffbe65', '#9138ed', '#b76bff'), ('#f8ccea', '#8621ad', '#cc42f5'),
    ('#f8ccea', '#8621ad', '#cc42f5'), ('#fff0d2', '#6324d1', '#9238f0'),
    ('#ffdaa7', '#802186', '#a52dc5'), ('#f8ccea', '#521c88', '#8225c7'),
    ('#ffdb48', '#7b27af', '#a832e7'),
]):
    (root / f'frontend/assets/figma/avatar-{i}.svg').write_text(base.replace('#f8ccea', skin).replace('#8621ad', shirt).replace('#cc42f5', triangle))
