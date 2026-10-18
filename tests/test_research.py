import json
from pathlib import Path
from server.research import DATA, evidence_pack


def test_registry_has_traceable_dates_and_no_local_certification():
    assert len(DATA['records']) == 27
    assert DATA['reviewed_by_local_expert'] is False
    assert len({r['id'] for r in DATA['records']}) == 27
    for r in DATA['records']:
        assert r['url'].startswith('https://')
        assert r['expert_reviewed'] is False
        assert r['checked_at'] <= DATA['as_of']
        assert len(r['limitations']) > 45
        assert r['year'] is None or r['year'] <= 2026


def test_model_pack_is_small_and_keeps_limitations_not_treatment_rates():
    pack = evidence_pack({'tree_part':'ریشه و طوقه','reported_by_farmer':{'irrigation':'شوری آب'}})
    assert 1 <= len(pack) <= 6
    assert all(r['limitations'] and r['source'] and r['access'] for r in pack)
    assert any('پایه' in r['finding'] or 'آب' in r['finding'] for r in pack)


def test_shared_source_has_no_duplicate_parallel_copy():
    assert DATA == json.loads(Path('src/data/research.json').read_text())


def test_container_runtime_includes_the_shared_research_registry():
    docker = Path('Dockerfile').read_text()
    runtime = docker.split('FROM python:',1)[1]
    assert 'COPY src/data ./src/data' in runtime


def test_selection_matches_shared_hand_reviewed_cases_in_both_runtimes():
    for case in json.loads(Path('tests/fixtures/evidence-cases.json').read_text()):
        assert [r['id'] for r in evidence_pack(case['context'])] == case['ids'], case['name']
    assert evidence_pack({'notes': 'پسیل'}, 0) == []


def test_scientific_basis_cannot_adopt_generated_source_metadata():
    from server.scientific_evidence import DecisionReasoning, scientific_basis
    reasoning = json.loads(Path('tests/fixtures/decision-reasoning.json').read_text())
    pack = evidence_pack({'notes': 'خشکیدگی تنه'})
    reasoning['research_ids'] = [pack[0]['id'], pack[0]['id'], 'pgpr-salinity-2026', 'made-up']
    reasoning['research_claims'] = [{'statement': 'تشخیص به آزمایش نیاز دارد.', 'source_ids': [pack[0]['id'], 'made-up'], 'application_limit': 'نمونه از این باغ گرفته نشده است.'}]
    basis = scientific_basis(DecisionReasoning(**reasoning), pack)
    assert basis['reasoning']['research_ids'] == [pack[0]['id']]
    assert basis['sources'] == [pack[0]]
    assert not basis['live_search'] and not basis['locally_validated']
    assert basis['catalog_version'] == DATA['version']


def test_missing_differential_checks_or_reasoning_is_not_a_new_scientific_report():
    import pytest
    from pydantic import ValidationError
    from server.scientific_evidence import DecisionReasoning, scientific_basis
    reasoning = json.loads(Path('tests/fixtures/decision-reasoning.json').read_text())
    with pytest.raises(ValidationError):
        DecisionReasoning(**{**reasoning, 'discriminating_checks': []})
    with pytest.raises(ValueError):
        scientific_basis(None, [])


def test_selective_refresh_is_not_a_fake_full_recheck():
    assert next(r for r in DATA['records'] if r['id'] == 'rootstock-review')['checked_at'] == '2026-10-12'
    assert next(r for r in DATA['records'] if r['id'] == 'iran-trunk-pathogens-2026')['access'] == 'publisher-abstract'
    assert DATA['as_of'] == '2026-10-18'
