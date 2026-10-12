"""Synthetic FX/transfer tests, not quotes from any real dollar market."""
import io
import json
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import server.api as service
from server.database import connect
from server.pricing import PricingInput, amount_toman, iran_today, ready
from server.security import ATTEMPTS


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('DATABASE_PATH',str(tmp_path/'pricing.sqlite3'))
    monkeypatch.setenv('UPLOAD_DIR',str(tmp_path/'receipts'))
    monkeypatch.setenv('ADMIN_EMAIL','pricing-admin@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD','pricing-test-password-2026')
    monkeypatch.setenv('LOAD_OWNER_DRAFT','false')
    monkeypatch.setenv('BILLING_PRICING_MODE','usd')
    monkeypatch.setenv('MANUAL_PAYMENTS_ENABLED','true')
    monkeypatch.setenv('DEMO_MODE','true');monkeypatch.setenv('COOKIE_SECURE','false')
    for name in ['VISION_PROVIDER','VISION_MODEL','GROQ_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GEMINI_REQUESTS_ENABLED']:
        monkeypatch.delenv(name,raising=False)
    ATTEMPTS.clear()
    with TestClient(service.app) as c:yield c


def admin(c):
    assert c.post('/api/auth/login',json={'email':'pricing-admin@example.com','password':'pricing-test-password-2026'}).status_code==200


def register(c):
    assert c.post('/api/auth/register',json={'name':'باغدار آزمون','email':'usd-farmer@example.com','password':'usd-test-password-2026'}).status_code==200


def price_input(rate='200000'):
    return {'receiving_requested':True,'confirmed':True,'rate_toman_per_usd':rate,'rate_date':str(iran_today()),'source':'SYNTHETIC TEST RATE - NOT TODAY MARKET','source_url':'','usd_prices':{'trial':'10','season':'35','large':'80'}}


def bank(c):
    assert c.put('/api/billing/admin/bank',json={'card_number':'4111111111111111','holder':'حساب تست','bank':'بانک تست'}).status_code==200


def enable_model(monkeypatch):
    # Configuration mock only; no request goes to a model in these receipt tests.
    monkeypatch.setenv('VISION_PROVIDER','groq');monkeypatch.setenv('VISION_MODEL','fake-model');monkeypatch.setenv('GROQ_API_KEY','dummy-test-key')


def receipt(c, quote_id,tracking='USD-TEST-1'):
    buffer=io.BytesIO();Image.new('RGB',(300,300),(200,210,200)).save(buffer,'JPEG')
    return c.post('/api/billing/receipts',files={'image':('test-receipt.jpg',buffer.getvalue(),'image/jpeg')},data={'name':'باغدار تست','tracking':tracking,'package_id':'trial','quote_id':quote_id})


def test_default_usd_packages_never_invent_a_rate_or_price(client):
    c=client.get('/api/billing/config').json()
    assert c['pricing']['mode']=='usd' and not c['pricing']['ready'] and not c['enabled']
    assert all(p['price_toman'] is None and p['price_usd'] is None for p in c['packages'])


def test_pricing_requires_admin_and_complete_dated_sourced_confirmation(client):
    register(client)
    assert client.put('/api/billing/admin/pricing',json=price_input()).status_code==403
    admin(client)
    for field in ['source','usd_prices','rate_toman_per_usd','rate_date']:
        data=price_input();data[field]={} if field=='usd_prices' else '' if field=='source' else None
        assert client.put('/api/billing/admin/pricing',json=data).status_code==422
    data=price_input();data['rate_date']=str(iran_today()+timedelta(days=1))
    assert client.put('/api/billing/admin/pricing',json=data).status_code==422
    data=price_input();data['source_url']='javascript:alert(1)'
    assert client.put('/api/billing/admin/pricing',json=data).status_code==422


@pytest.mark.parametrize('invalid',[True,'NaN','Infinity','0','-1','10.001'])
def test_unusable_usd_base_values_are_rejected(invalid):
    with pytest.raises(ValueError):PricingInput.model_validate({**price_input(),'usd_prices':{'trial':invalid}})


def test_toman_conversion_is_decimal_and_rounded_without_rial_factor():
    assert amount_toman(Decimal('10'),Decimal('200000'))==2_000_000
    assert amount_toman(Decimal('0.01'),Decimal('200000'))==2000
    assert amount_toman(Decimal('10.01'),Decimal('200001'))==2_003_000


def test_receiving_request_does_not_override_missing_model_or_destination(client,monkeypatch):
    admin(client)
    pricing=client.put('/api/billing/admin/pricing',json=price_input()).json()
    assert pricing['ready'] and pricing['receiving_requested']
    c=client.get('/api/billing/config').json();assert not c['enabled']
    assert c['packages'][0]['price_toman']==2_000_000
    bank(client);assert not client.get('/api/billing/config').json()['enabled']
    enable_model(monkeypatch);assert client.get('/api/billing/config').json()['enabled']
    monkeypatch.setenv('MANUAL_PAYMENTS_ENABLED','false')
    assert not client.get('/api/billing/config').json()['enabled']


def test_pending_card_holder_draft_is_private_and_cannot_enable_receiving(client,monkeypatch):
    admin(client);enable_model(monkeypatch)
    assert client.put('/api/billing/admin/bank',json={'card_number':'','holder':'نام مالک تست','bank':''}).status_code==200
    client.put('/api/billing/admin/pricing',json=price_input())
    c=client.get('/api/billing/config').json();assert not c['enabled'] and c['holder']==''
    assert client.get('/api/billing/admin').json()['config']['holder']=='نام مالک تست'


def test_rate_change_never_reprices_a_receipt_or_its_credit_count(client,monkeypatch):
    admin(client);bank(client);enable_model(monkeypatch)
    quote1=client.put('/api/billing/admin/pricing',json=price_input()).json()['quote_id']
    quote2=client.put('/api/billing/admin/pricing',json=price_input('250000')).json()['quote_id']
    assert quote1!=quote2
    assert client.get('/api/billing/config').json()['packages'][0]['price_toman']==2_500_000
    register(client)
    # The old quote is still valid today; accept the exact amount already shown,
    # never tell the payer to pay the difference or re-transfer automatically.
    r=receipt(client,quote1);assert r.status_code==201,r.text
    assert r.json()['price_toman']==2_000_000 and r.json()['analyses']==10
    assert r.json()['price_snapshot']['rate_toman_per_usd']=='200000'
    with connect() as db:
        assert db.execute('SELECT price_toman FROM credit_receipts').fetchone()[0]==2_000_000


def test_forged_or_stale_quote_never_records_a_charge_or_receipt(client,monkeypatch):
    admin(client);bank(client);enable_model(monkeypatch)
    quote=client.put('/api/billing/admin/pricing',json=price_input()).json()['quote_id']
    register(client)
    assert receipt(client,'fake-quote-id').status_code==409
    with connect() as db:
        data=json.loads(db.execute('SELECT data FROM billing_price_quotes WHERE id=?',(quote,)).fetchone()[0])
        data['rate_date']=str(iran_today()-timedelta(days=1))
        db.execute('UPDATE billing_price_quotes SET data=? WHERE id=?',(json.dumps(data),quote))
    assert not client.get('/api/billing/config').json()['enabled']
    assert receipt(client,quote).status_code==503
    with connect() as db:
        assert db.execute('SELECT COUNT(*) FROM credit_receipts').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM credit_ledger').fetchone()[0]==0


def test_no_legacy_fixed_price_gateway_is_activated_in_usd_mode(client,monkeypatch):
    monkeypatch.setenv('ZARINPAL_MERCHANT_ID','test-id');monkeypatch.setenv('PUBLIC_BASE_URL','https://test.example')
    assert service.payment_configured() is False
