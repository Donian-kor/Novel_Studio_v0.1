import os

target = r'c:/Users/donian/Desktop/python/Novel_Studio/novel_studio/ui/views/entities.py'

content = open(r'c:/Users/donian/Desktop/python/Novel_Studio/_tmp_entities_content.txt', 'r', encoding='utf-8').read()

with open(target, 'w', encoding='utf-8') as f:
    f.write(content)

print('entities.py 재작성 완료')
