"""Protocol-only mocks; never call Google or consume the owner's API quota."""
import io
import json
import math
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import server.api as service
from server.database import connect, now_iso, sample_report
from server.fieldwork import LabInput
from server.gemini import model_name
from server.laboratory import calculations, measured_units
from server.security import ATTEMPTS


@pytest.fixture
def client(tmp_path, monkeypatch):
    for name in ['ADMIN_EMAIL','ADMIN_PASSWORD','GROQ_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GEMINI_REQUESTS_ENABLED','MANUAL_PAYMENTS_ENABLED','VISION_MODEL','VISION_PROVIDER','OLLAMA_BASE_URL','PUBLIC_BASE_URL']:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'gemini.sqlite3'))
    monkeypatch.setenv('UPLOAD_DIR', str(tmp_path / 'images'))
    monkeypatch.setenv('DEMO_MODE','true'); monkeypatch.setenv('COOKIE_SECURE','false')
    monkeypatch.setenv("BILLING_PRICING_MODE","fixed")
    monkeypatch.setenv("LOAD_OWNER_DRAFT", "false")
    ATTEMPTS.clear()
    with TestClient(service.app) as c: yield c


def register(c, email='gemini-farmer@example.com'):
    assert c.post('/api/auth/register',json={'name':'باغدار آزمایشی','email':email,'password':'local-test-pass-2026'}).status_code == 200
    return c.get('/api/bootstrap').json()['user']['id']


def enable(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER','gemini')
    monkeypatch.setenv('VISION_MODEL','gemini-3.1-pro-preview')
    monkeypatch.setenv('GEMINI_API_KEY','dummy-gemini-server-key')
    monkeypatch.setenv('GEMINI_REQUESTS_ENABLED','true')


def photo():
    out=io.BytesIO(); image=Image.new('RGB',(500,400),(30,160,70)); exif=Image.Exif();exif[270]='private test EXIF'
    image.save(out,'JPEG',exif=exif);return out.getvalue()


def photo_request(c, consent='true'):
    return c.post('/api/analyses', files=[('image',('leaf.jpg',photo(),'image/jpeg')),('additional_images',('back.jpg',photo(),'image/jpeg'))], data={'tree_part':'برگ','consent':consent})


def lab_input(kind='water'):
    return {'kind':kind,'values':{'ph':8,'ec':2},'method':'water' if kind=='water' else 'unknown','sample_date':'2026-10-11','depth':'','orchard_id':None,'notes':''}


def lab_result():
    return {'title':'بررسی احتمالی آزمایش','summary':'تفسیر نیازمند بررسی روش آزمایشگاه و شرایط باغ است.','findings':['واحد و روش را با آزمایشگاه کنترل کنید.'],'nutrition_considerations':['برای نتیجه تغذیه، روش استخراج و آزمایش برگ نیز لازم است.'],'irrigation_considerations':['یکنواختی آبیاری و زهکشی را بررسی کنید.'],'care_plan':['ثبت روند و بازدید کارشناس محلی.'],'yield_quality_plan':['مدیریت محصول وابسته به رقم و مرحله رشد است.'],'needed_tests':['در صورت نیاز، آزمون بافت برگ.'],'limitations':['اعداد ورودی خوداظهاری هستند؛ دقت علمی محلی تأیید نشده است.'],'follow_up_questions':['مرحله رشد و سابقه آبیاری چیست؟'],'knowledge_ids':['nutrition']}


def provider_mock(monkeypatch, result, inspect=None, finish='STOP', response=None, status=200):
    calls=[]
    class MockClient:
        def __init__(self, **kw): assert kw['follow_redirects'] is False
        async def __aenter__(self): return self
        async def __aexit__(self,*_): pass
        async def post(self, url, headers, json):
            calls.append((url,headers,json))
            assert headers == {'x-goog-api-key':'dummy-gemini-server-key'}
            assert 'dummy-gemini-server-key' not in url
            assert 'dummy-gemini-server-key' not in __import__('json').dumps(json)
            assert url == 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent'
            assert json['generationConfig']['responseMimeType']=='application/json'
            assert json['generationConfig']['responseJsonSchema']['additionalProperties'] is False
            if inspect: inspect(json)
            answer=response if response is not None else {'candidates':[{'finishReason':finish,'content':{'parts':[{'thought':True,'text':'internal reasoning must not be a result'},{'text':__import__('json').dumps(result)}]}}]}
            return httpx.Response(status,json=answer,request=httpx.Request('POST',url))
    monkeypatch.setattr(service.httpx,'AsyncClient',MockClient)
    return calls


def test_key_alone_never_enables_potentially_billable_gemini_calls(client, monkeypatch):
    register(client)
    enable(monkeypatch); monkeypatch.delenv('GEMINI_REQUESTS_ENABLED')
    calls=provider_mock(monkeypatch,{})
    assert not client.get('/api/health').json()['services']['vision_configured']
    assert photo_request(client).status_code==503
    assert client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':True}).status_code==503
    assert calls==[]
    health=client.get('/api/health').text
    assert 'dummy-gemini-server-key' not in health


@pytest.mark.parametrize('name',['','../gemini-x','gemini-x?key=leak','gemini-x:generateContent','gemini-x/path','not-a-vision-model'])
def test_model_cannot_inject_a_url_or_be_silently_substituted(name):
    assert model_name(name) is None


def test_multi_photo_uses_native_gemini_schema_and_strips_metadata(client, monkeypatch):
    register(client);enable(monkeypatch)
    result=sample_report()
    for key in ['provider','disclaimer','knowledge_version']: result.pop(key)
    result['is_pistachio']=True;result['hypotheses'][0]['confidence']=.8
    def inspect(payload):
        import base64
        parts=payload['contents'][0]['parts']; assert len(parts)==3
        for part in parts[1:]:
            assert part['inlineData']['mimeType']=='image/jpeg'
            image=Image.open(io.BytesIO(base64.b64decode(part['inlineData']['data'])))
            assert not image.getexif()
    calls=provider_mock(monkeypatch,result,inspect)
    assert photo_request(client, 'false').status_code==422 and calls==[]
    r=photo_request(client);assert r.status_code==201,r.text
    assert r.json()['data']['provider']=='gemini'
    assert r.json()['data']['hypotheses'][0]['confidence'] is None
    assert len(r.json()['image_urls'])==2


@pytest.mark.parametrize('response',[
    {'promptFeedback':{'blockReason':'SAFETY'}},
    {'candidates':[]},
    {'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'{}'}]}}]},
    {'candidates':[{'finishReason':'STOP','safetyRatings':[{'blocked':True}],'content':{'parts':[{'text':'{}'}]}}]},
    {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':None}]}}]},
    {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'not JSON'}]}}]},
])
def test_blocked_truncated_or_invalid_result_never_spends_internal_credit(client, monkeypatch,response):
    register(client);enable(monkeypatch);provider_mock(monkeypatch,{},response=response)
    assert photo_request(client).status_code==502
    assert client.get('/api/bootstrap').json()['usage']['used']==0
    assert not list(Path(os.environ['UPLOAD_DIR']).glob('*.jpg'))


def test_lab_interpretation_has_owned_inputs_units_and_server_calculations(client, monkeypatch):
    register(client);enable(monkeypatch)
    orchard=client.post('/api/orchards',json={'name':'باغ خصوصی','province':'کرمان','city':'رفسنجان','cultivar':'اکبری','area':2,'trees':200,'irrigation':'قطره‌ای','age':10}).json()['id']
    sample=lab_input();sample['orchard_id']=orchard
    sample['values']={'sodium':229.898,'calcium':40.078,'magnesium':24.305,'bicarbonate':122.0336,'carbonate':0,'ec':2}
    def inspect(payload):
        assert len(payload['contents'][0]['parts'])==1 # No invented image.
        text=payload['contents'][0]['parts'][0]['text']
        assert orchard not in text and 'باغ خصوصی' not in text
        data=json.loads(text.split(': ',1)[1])
        assert data['user_entered_laboratory']['units']['calcium']=='mg/L'
        assert data['user_entered_laboratory']['units']['ec']=='dS/m'
        assert data['server_calculations'][0]['value']==pytest.approx(10/math.sqrt(2))
        assert data['server_calculations'][1]['value']==pytest.approx(-2)
    calls=provider_mock(monkeypatch,lab_result(),inspect)
    r=client.post('/api/lab-analyses',json={'sample':sample,'consent':True})
    assert r.status_code==201,r.text
    data=r.json();assert data['result']['provider']=='gemini' and data['result']['basis']=='user-entered-laboratory'
    assert data['calculations'][1]['value']==pytest.approx(-2)
    assert data['input']['values']==sample['values'] and len(calls)==1
    boot=client.get('/api/bootstrap').json()
    assert boot['usage']['used']==1 and boot['reports']==[]
    assert len(client.get('/api/lab-analyses').json())==1
    other=TestClient(service.app); register(other,'another-lab@example.com')
    assert other.get('/api/lab-analyses').json()==[]
    assert other.delete('/api/lab-analyses/'+data['id']).status_code==404
    assert client.get('/api/reports/'+data['id']).status_code==404
    assert client.get('/api/reports/'+data['id']+'/image').status_code==404
    assert client.delete('/api/lab-analyses/'+data['id']).status_code==200
    assert client.get('/api/lab-analyses').json()==[]
    assert client.get('/api/bootstrap').json()['usage']['used']==1 # Cannot reset quota by deletion.


def test_missing_ions_are_not_zero_and_unknown_soil_method_is_preserved():
    s=lab_input();s['values']={'sodium':10,'calcium':0}
    assert calculations(LabInput(**s))==[]
    s['values']={'sodium':10,'calcium':0,'magnesium':0}
    assert calculations(LabInput(**s))==[]
    soil=LabInput(**lab_input('soil'))
    assert soil.method=='unknown' and measured_units(soil)['ec']=='dS/m'
    assert calculations(soil)==[]


def test_lab_requires_consent_real_account_and_valid_measurements(client,monkeypatch):
    enable(monkeypatch);client.get('/api/bootstrap')
    calls=provider_mock(monkeypatch,lab_result())
    assert client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':True}).status_code==401
    register(client)
    assert client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':False}).status_code==422
    sample=lab_input();sample['method']='saturated'
    assert client.post('/api/lab-analyses',json={'sample':sample,'consent':True}).status_code==422
    sample=lab_input();sample['values']={'ph':True}
    assert client.post('/api/lab-analyses',json={'sample':sample,'consent':True}).status_code==422
    sample=lab_input();sample['orchard_id']='foreign-orchard'
    assert client.post('/api/lab-analyses',json={'sample':sample,'consent':True}).status_code==404
    assert calls==[]


@pytest.mark.parametrize('bad',[
    {'care_plan':['۴ کیلوگرم کود اضافه کنید.']},
    {'summary':'تشخیص با دقت ۹۹٪'},
    {'confidence':.99},
    {'calculations':[{'sar':1000}]},
])
def test_lab_does_not_accept_a_forged_numeric_dose_confidence_or_calculation(client,monkeypatch,bad):
    register(client);enable(monkeypatch);result={**lab_result(),**bad};provider_mock(monkeypatch,result)
    r=client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':True})
    assert r.status_code==502,r.text
    assert client.get('/api/bootstrap').json()['usage']['used']==0
    assert client.get('/api/lab-analyses').json()==[]


def test_photo_and_laboratory_share_atomic_free_quota(client,monkeypatch):
    register(client);enable(monkeypatch);calls=provider_mock(monkeypatch,lab_result())
    for _ in range(3):
        assert client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':True}).status_code==201
    assert client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':True}).status_code==402
    assert photo_request(client).status_code==402
    assert len(calls)==3


def test_interrupted_lab_reservation_is_refunded_on_restart(client, monkeypatch):
    user=register(client)
    with connect() as db:
        db.execute('INSERT INTO reports (id,user_id,tree_part,notes,data,status,created_at,report_kind) VALUES (?,?,?,?,?,?,?,?)',('interrupted-lab',user,'آزمایش آب','','{}','processing',now_iso(),'lab'))
        db.execute('INSERT INTO credit_ledger VALUES (?,?,?,?,?,?)',('analysis-interrupted-lab',user,-1,'analysis','test reservation',now_iso()))
    with TestClient(service.app): pass
    with connect() as db:
        assert db.execute('SELECT status FROM reports WHERE id=?',('interrupted-lab',)).fetchone()[0]=='failed'
        assert db.execute('SELECT COUNT(*) FROM credit_ledger').fetchone()[0]==0


def test_paid_lab_success_debits_once_and_failure_restores_reservation(client,monkeypatch):
    user=register(client);enable(monkeypatch)
    monkeypatch.setenv('MANUAL_PAYMENTS_ENABLED','true')
    # Seed an isolated test ledger, not an actual transfer or the owner's card.
    with connect() as db:
        db.execute('INSERT INTO billing_settings VALUES (1,?,?,?)',('4111111111111111','حساب تست','بانک تست'))
        db.execute('INSERT INTO credit_ledger VALUES (?,?,?,?,?,?)',('test-lab-purchase',user,10,'purchase','TEST ONLY',now_iso()))
    provider_mock(monkeypatch,lab_result())
    r=client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':True})
    assert r.status_code==201,r.text
    assert client.get('/api/billing/my').json()['balance']==9
    provider_mock(monkeypatch,{},status=429)
    assert client.post('/api/lab-analyses',json={'sample':lab_input(),'consent':True}).status_code==502
    assert client.get('/api/billing/my').json()['balance']==9
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM credit_ledger WHERE kind='analysis'").fetchone()[0]==1


def test_image_configuration_is_not_a_real_success_and_rotation_invalidates_evidence(client, monkeypatch):
    from server import vision_readiness
    from datetime import datetime, timedelta, timezone
    register(client);enable(monkeypatch)
    status=client.get('/api/vision/status').json()
    assert status['vision_configured'] and not status['vision_verified']
    assert status['vision_connection_state']=='untested' and not status['vision_scientifically_validated']
    key=service.vision_settings()[2]
    vision_readiness.record(service.vision_settings(),True) # Test-only connection evidence.
    status=client.get('/api/vision/status').json()
    assert status['vision_verified'] and status['vision_connection_state']=='responded'
    assert key not in json.dumps(status)
    monkeypatch.setenv('GEMINI_API_KEY','rotated-dummy-key')
    assert client.get('/api/vision/status').json()['vision_connection_state']=='untested'
    vision_readiness.record(service.vision_settings(),True)
    with connect() as db:
        db.execute('UPDATE vision_connection SET checked_at=? WHERE id=1', ((datetime.now(timezone.utc)-timedelta(hours=25)).isoformat(),))
    assert client.get('/api/vision/status').json()['vision_connection_state']=='expired'
    vision_readiness.record(service.vision_settings(),False)
    assert client.get('/api/vision/status').json()['vision_connection_state']=='failed'


def test_validated_gemini_image_response_records_connection_not_scientific_accuracy(client,monkeypatch):
    register(client);enable(monkeypatch)
    result=sample_report()
    for key in ['provider','disclaimer','knowledge_version']:result.pop(key)
    result['is_pistachio']=True
    provider_mock(monkeypatch,result)
    assert photo_request(client).status_code==201
    status=client.get('/api/vision/status').json()
    assert status['vision_verified'] and not status['vision_scientifically_validated']
    provider_mock(monkeypatch,{},finish='MAX_TOKENS')
    assert photo_request(client).status_code==502
    status=client.get('/api/vision/status').json()
    assert not status['vision_verified'] and status['vision_connection_state']=='failed'


def test_owner_image_test_requires_admin_consent_and_creates_no_invoice(client,monkeypatch):
    from server.security import password_hash
    import uuid
    with connect() as db:
        db.execute('INSERT INTO users (id,name,email,password_hash,role,is_demo,created_at) VALUES (?,?,?,?,?,?,?)',(uuid.uuid4().hex,'مدیر آزمایشی','vision-admin@example.com',password_hash('vision-test-password-2026'),'admin',0,now_iso()))
    register(client);enable(monkeypatch)
    result=sample_report()
    for key in ['provider','disclaimer','knowledge_version']:result.pop(key)
    result['is_pistachio']=True
    calls=provider_mock(monkeypatch,result)
    path='/api/admin/vision/test'
    def run(consent='true'):
        return client.post(path,files={'image':('owner.jpg',photo(),'image/jpeg')},data={'tree_part':'میوه','consent':consent})
    assert run().status_code==403 and calls==[]
    assert client.post('/api/auth/login',json={'email':'vision-admin@example.com','password':'vision-test-password-2026'}).status_code==200
    assert run('false').status_code==422 and calls==[]
    r=run();assert r.status_code==200,r.text
    assert r.json()['image_response_received'] and r.json()['services']['vision_verified']
    assert len(calls)==1
    assert client.get('/api/bootstrap').json()['usage']['used']==0
    with connect() as db:
        assert db.execute('SELECT COUNT(*) FROM reports WHERE is_sample=0').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM credit_ledger').fetchone()[0]==0
    assert not Path(os.environ['UPLOAD_DIR']).exists()
