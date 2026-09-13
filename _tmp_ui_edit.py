path = r'c:/Users/donian/Desktop/python/Novel_Studio/novel_studio/ui/forms/entities.ui'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = '<widget class="QPlainTextEdit" name="detail"/>'
new_text = '<widget class="QWidget" name="formContainer"><layout class="QVBoxLayout" name="formLayout"/></widget>'

if old_text in content:
    content = content.replace(old_text, new_text)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('entities.ui 수정 완료: detail -> formContainer')
else:
    print('매칭 실패: QPlainTextEdit 위젯을 찾지 못했습니다')
    idx = content.find('detail')
    if idx >= 0:
        print('detail 주변:', repr(content[idx-30:idx+80]))
