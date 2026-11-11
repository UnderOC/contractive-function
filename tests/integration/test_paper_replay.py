"""The archived tail proofs must survive removing the assertion implementation."""
import json
from pathlib import Path
import shutil

import pytest

from contractive_tool.analysis.symbolic_workflow import verify_workflow
from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
from contractive_tool.errors import AnalysisError

PROJECT = Path(__file__).resolve().parents[2]


def test_historical_options_ignore_only_retired_assertion_fields():
    options = SearchOptions.from_artifact({
        'max_degree': 2, 'assertion_margin': '1/1000000', 'assertion_variables': None})
    assert options.max_degree == 2
    assert 'assertion_margin' not in options.__dataclass_fields__
    with pytest.raises(TypeError):
        SearchOptions.from_artifact({'unknown_option': True})


def test_removed_goal_rejected_before_creating_artifacts(tmp_path):
    out = tmp_path/'result'
    with pytest.raises(AnalysisError, match='Only tailbound'):
        run_analysis(tmp_path/'absent.pp', 'assertion_violation', out)
    assert not out.exists()


def test_saved_tail_replays_after_checkout_move_and_rejects_wrong_source(tmp_path):
    index = json.loads((PROJECT/'experiments/paper_tailbounds/manifest.json').read_text())
    row = next(r for r in index['examples'] if r['label'] == 'R4')
    root = tmp_path/'relocated'
    shutil.copytree(PROJECT/row['run'], root)
    path = root/'manifest.json'
    manifest = json.loads(path.read_text())
    source = tmp_path/'old-checkout.pp'
    manifest['source'] = str(source)
    path.write_text(json.dumps(manifest))
    assert verify_workflow(root)['status'] == 'proved'
    source.write_text('x := 0; refute true;')
    assert verify_workflow(root) == {
        'status': 'verification_failed', 'reason': 'Source hash mismatch'}
    source.unlink()
    (root/'shared/source.pp').write_text('x := 0; refute true;')
    assert verify_workflow(root) == {
        'status': 'verification_failed', 'reason': 'Source hash mismatch'}
