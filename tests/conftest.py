from pathlib import Path
import re

import pytest


@pytest.fixture
def unbounded_kelly_source(tmp_path):
    """Remove K6's upper stopping boundary for the unbounded-domain regression."""
    project = Path(__file__).resolve().parents[1]
    text = (project/'contractive_examples/kelly/K6_two_sided_exit.pp').read_text()
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = text.replace('wealth >= 0.5 and wealth < 2', 'wealth >= 0.5')
    text = text.replace('0.4 <= wealth and wealth <= 2.4', '0 < wealth')
    text = text.replace('0.5 <= wealth and wealth <= 2', '0.5 <= wealth')
    text = text.replace('refute (wealth < 0.5)', 'refute (wealth <= 0.45)')
    source = tmp_path/'unbounded-domain.pp'
    source.write_text(text)
    return source
