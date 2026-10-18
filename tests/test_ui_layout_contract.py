"""Guards the CSS rules that stop long user text breaking the phone layout.

This is a contract check on the stylesheet text, not a browser test. The measured check is
`python -m scripts.check_layout_overflow`, which needs a Chromium browser and is run by hand.
"""

import re
from pathlib import Path

STYLE = (Path(__file__).resolve().parents[1] / "src/web/static/style.css").read_text(encoding="utf-8")


def test_user_entered_text_can_wrap_anywhere():
    rule = re.search(r"h1,[^{]*\bdd\b[^{]*\btd\b[^{]*\{([^}]*)\}", STYLE)
    assert rule and "overflow-wrap: anywhere" in rule.group(1)


def test_detail_grid_and_flex_children_can_shrink():
    assert "minmax(0, 1fr)" in STYLE
    assert re.search(r"\.detail-head > div[^{]*\{[^}]*min-width: 0", STYLE)
    assert re.search(r"table\.responsive td \{[^}]*min-width: 0", STYLE)


def test_a_long_signed_in_email_cannot_widen_the_header_or_the_admin_action_cells():
    assert re.search(r"\.nav__user \{[^}]*overflow-wrap: anywhere", STYLE)
    assert re.search(r"\.site-header nav \{[^}]*min-width: 0", STYLE)
    assert re.search(r'td\[data-label="Actions"\] \{[^}]*flex-direction: column', STYLE)
