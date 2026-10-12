import json
from pathlib import Path
from server.research import DATA, evidence_pack


def test_registry_has_traceable_dates_and_no_local_certification():
    assert len(DATA['records']) == 24
    assert DATA['reviewed_by_local_expert'] is False
    assert len({r['id'] for r in DATA['records']}) == 24
    for r in DATA['records']:
        assert r['url'].startswith('https://')
        assert r['expert_reviewed'] is False
        assert r['checked_at'] == DATA['as_of']
        assert len(r['limitations']) > 45
        assert r['year'] is None or r['year'] <= 2026


def test_model_pack_is_small_and_keeps_limitations_not_treatment_rates():
    pack = evidence_pack({'tree_part':'ریشه و طوقه','reported_by_farmer':{'irrigation':'شوری آب'}})
    assert len(pack)==6
    assert all(r['limitations'] and r['source'] and r['access'] for r in pack)
    assert any('پایه' in r['finding'] or 'آب' in r['finding'] for r in pack)


def test_shared_source_has_no_duplicate_parallel_copy():
    assert DATA == json.loads(Path('src/data/research.json').read_text())


def test_container_runtime_includes_the_shared_research_registry():
    docker = Path('Dockerfile').read_text()
    runtime = docker.split('FROM python:',1)[1]
    assert 'COPY src/data ./src/data' in runtime
