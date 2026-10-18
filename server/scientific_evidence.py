"""Shared explanation contract. Structural completeness is NOT scientific validation."""
import json
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .research import DATA, ROOT

CONTRACT = json.loads((ROOT / 'decision-contract.json').read_text())
NOTICE = 'این گزارش بر منابع گزینشیِ تاریخ‌دار تکیه دارد؛ جست‌وجوی زنده و جامعِ تازه‌ترین مقالات یا تأیید کارشناس محلی نیست.'


class ResearchClaim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    statement: str = Field(min_length=1, max_length=1000)
    source_ids: list[str] = Field(min_length=1, max_length=4)
    application_limit: str = Field(min_length=1, max_length=1000)


class DecisionReasoning(BaseModel):
    model_config = ConfigDict(extra='forbid')
    supporting_evidence: list[str] = Field(min_length=1, max_length=8)
    alternatives: list[str] = Field(min_length=1, max_length=8)
    discriminating_checks: list[str] = Field(min_length=1, max_length=8)
    missing_information: list[str] = Field(min_length=1, max_length=8)
    reassessment: list[str] = Field(min_length=1, max_length=8)
    referral_triggers: list[str] = Field(min_length=1, max_length=8)
    research_ids: list[str] = Field(max_length=8)
    research_claims: list[ResearchClaim] = Field(max_length=6)

    @field_validator('supporting_evidence', 'alternatives', 'discriminating_checks', 'missing_information', 'reassessment', 'referral_triggers', 'research_ids')
    @classmethod
    def bounded(cls, values):
        if any(not v.strip() or len(v) > 1000 for v in values):
            raise ValueError('Empty or overlong scientific reasoning')
        return values


def evidence_prompt(pack):
    return {'catalog_version': DATA['version'], 'catalog_updated_at': DATA['as_of'], 'live_search': False,
            'locally_validated': False, 'notice': NOTICE, 'records': pack}


def scientific_basis(reasoning, pack):
    if reasoning is None:
        raise ValueError('Scientific reasoning missing; do not consume an analysis')
    raw = reasoning.model_dump() if isinstance(reasoning, DecisionReasoning) else DecisionReasoning.model_validate(reasoning).model_dump()
    allowed = {r['id'] for r in pack}
    claims = []
    for claim in raw['research_claims']:
        ids = list(dict.fromkeys(i for i in claim['source_ids'] if i in allowed))
        if ids and claim['statement'].strip() and claim['application_limit'].strip():
            claims.append({**claim, 'source_ids': ids})
    raw['research_claims'] = claims
    raw['research_ids'] = list(dict.fromkeys(i for claim in claims for i in claim['source_ids']))
    return {'version': 1, 'catalog_version': DATA['version'], 'catalog_updated_at': DATA['as_of'],
            'live_search': False, 'locally_validated': False, 'notice': NOTICE, 'reasoning': raw,
            'sources': [r for r in pack if r['id'] in raw['research_ids']],
            'supplied_source_ids': [r['id'] for r in pack]}


def require_reasoning_schema(schema):
    """Old saved reports remain readable; NEW generated answers must include the contract."""
    schema['required'] = list(dict.fromkeys([*schema.get('required', []), 'decision_reasoning']))
    schema['properties']['decision_reasoning'] = {'$ref': '#/$defs/DecisionReasoning'}
    definition = schema['$defs']['DecisionReasoning']
    definition['required'] = list(dict.fromkeys([*definition.get('required', []), 'research_claims']))
    return schema
