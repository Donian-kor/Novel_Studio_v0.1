from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1] / 'novel_studio' / 'ui' / 'forms'

def test_ui_items_have_single_child_widget_or_layout():
    for path in BASE.glob('*.ui'):
        root = ET.parse(path).getroot()
        for item in root.iter('item'):
            children = [c for c in item if c.tag in {'widget', 'layout', 'spacer'}]
            assert len(children) <= 1, f'{path.name}: <item> has {len(children)} child elements'

def test_v131_added_widget_names_exist():
    for filename, names in {
        'planning.ui': {'diffMasterBtn'},
        'plots.ui': {'hierBtn'},
        'memory.ui': {'refreshMemoryBtn', 'auditBtn'},
    }.items():
        root = ET.parse(BASE / filename).getroot()
        actual = {w.attrib.get('name') for w in root.iter('widget')}
        assert names <= actual
