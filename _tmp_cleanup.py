# 임시 검증 스크립트: 구버전 클래스 잔여 제거 + 문법 검사
import io
import py_compile

p = r'c:/Users/donian/Desktop/python/Novel_Studio/novel_studio/ui/views/entities.py'
s = io.open(p, encoding='utf-8').read()
marker = 'class EntitiesView(BaseView):'
first = s.find(marker)
second = s.find(marker, first + 1)
print('first at', first, '| second at', second)
if second != -1:
    s = s[:second].rstrip() + '\n'
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('removed old duplicate class')
py_compile.compile(p, doraise=True)
py_compile.compile(r'c:/Users/donian/Desktop/python/Novel_Studio/novel_studio/ui/main_window.py', doraise=True)
print('COMPILE_OK')
