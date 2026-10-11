"""Structured user observations; they are not verified image findings."""
import json
import math
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal
from fastapi import HTTPException

class DiagnosticContext(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    province: str = Field(default='', max_length=160)
    cultivar: str = Field(default='', max_length=160)
    stage: str = Field(default='', max_length=160)
    age: str = Field(default='', max_length=160)
    duration: str = Field(default='', max_length=160)
    distribution: str = Field(default='', max_length=160)
    affected_percent: str = Field(default='', max_length=160)
    irrigation: str = Field(default='', max_length=160)
    recent_inputs: str = Field(default='', max_length=1000)
    goal: str = Field(default='سلامت درخت و کیفیت محصول', max_length=160)
    symptoms: list[Literal['yellowing', 'sticky', 'spots', 'wilting', 'fruit', 'wood', 'yield']] = Field(default_factory=list, max_length=7)

    @model_validator(mode='after')
    def numeric_context(self):
        for key, maximum in [('age',150), ('duration',3650), ('affected_percent',100)]:
            raw = getattr(self, key)
            if raw:
                try:
                    number = float(raw)
                except ValueError:
                    raise ValueError('Invalid numeric context')
                if not math.isfinite(number) or number < 0 or number > maximum:
                    raise ValueError('Numeric context outside bounds')
        self.symptoms = list(dict.fromkeys(self.symptoms))
        return self


def read_context(raw):
    try:
        if len(raw) > 8192:
            raise ValueError('Context too long')
        return DiagnosticContext.model_validate(json.loads(raw) if raw else {}).model_dump()
    except (ValueError, TypeError):
        raise HTTPException(422, 'اطلاعات زمینه باغ یا نشانه‌ها معتبر نیستند.')


def photo_record(part, notes, context, knowledge_version):
    return {
        'title': f'عکس ثبت‌شده {part}', 'summary': 'این پرونده فقط عکس‌ها و اطلاعات ثبت‌شده باغدار است. هیچ مدل یا کارشناس، تصاویر را تحلیل نکرده و از آنها تشخیص یا درصد اطمینان تولید نشده است.',
        'quality': 'تحلیل نشده', 'is_pistachio': None, 'observations': [f'یادداشت شما: {notes}'] if notes else [], 'hypotheses': [],
        'actions': ['برای بررسی تخصصی، تصاویر، سابقه باغ و نتایج آزمایش را با کارشناس محلی مرور کنید.'],
        'needed_tests': [], 'follow_up_questions': [], 'urgency': 'low', 'knowledge_ids': ['sampling'],
        'disclaimer': 'ثبت پرونده بدون تحلیل تصویر؛ نسخه سم و کود نیست.', 'provider': 'photo-storage', 'knowledge_version': knowledge_version, 'context': context,
    }
