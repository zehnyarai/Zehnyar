import pytest
from tools import check_online_server as gate


def test_online_build_cannot_label_an_unconnected_image_service_as_active(monkeypatch):
    monkeypatch.setattr(gate.time,'sleep',lambda _:None)
    schema={'info':{'title':'Pestino API'},'paths':{'/api/analyses':{},'/api/vision/status':{}}}
    health={'status':'ok','app':'pestino','services':{'vision_configured':True,'vision_verified':False}}
    monkeypatch.setattr(gate,'get_json',lambda u:schema if u.endswith('openapi.json') else health)
    with pytest.raises(RuntimeError):gate.verify_server('https://pestino-test.example')
    health['services']['vision_verified']=True
    assert gate.verify_server('https://pestino-test.example')==health
    del schema['paths']['/api/analyses']
    with pytest.raises(RuntimeError):gate.verify_server('https://pestino-test.example')
