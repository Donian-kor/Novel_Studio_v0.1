from types import SimpleNamespace

from novel_studio.plot.plot_manager import PlotManager


def test_detail_ranges_are_count_based_for_500_chapters():
    manager = PlotManager(None, None, SimpleNamespace(settings={'target_chapters': 500, 'detail_section_count': 10}))
    assert manager.detail_ranges() == [
        (1, 50), (51, 100), (101, 150), (151, 200), (201, 250),
        (251, 300), (301, 350), (351, 400), (401, 450), (451, 500),
    ]


def test_detail_ranges_distribute_remainder_from_front():
    manager = PlotManager(None, None, SimpleNamespace(settings={'target_chapters': 503, 'detail_section_count': 10}))
    ranges = manager.detail_ranges()
    assert len(ranges) == 10
    assert ranges[0] == (1, 51)
    assert ranges[-1] == (454, 503)


def test_detail_ranges_never_creates_more_ranges_than_chapters():
    manager = PlotManager(None, None, SimpleNamespace(settings={'target_chapters': 5, 'detail_section_count': 10}))
    assert manager.detail_ranges() == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
