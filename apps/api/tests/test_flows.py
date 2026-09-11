def test_lead_creation_and_validation(client,lead_payload):
    ok=client.post('/api/public/leads',json=lead_payload)
    assert ok.status_code==201
    assert ok.json()['stage']=='New Lead'
    bad=client.post('/api/public/leads',json={**lead_payload,'email':'bad'})
    assert bad.status_code==422

def test_qualification_persistence_and_webhook_auth(client,lead_payload,auth):
    lead=client.post('/api/public/leads',json=lead_payload).json()
    payload={"score":86,"classification":"Hot","intent":"high","fit":"high","urgency":"high","conversion_likelihood":78,"summary":"A high-intent buyer with authority and a near-term implementation goal.","needs":["Automated qualification"],"objections":["Migration time"],"recommended_action":"Offer a tailored implementation call.","follow_up":"Thanks for sharing your goals. Let us map the fastest route to launch."}
    assert client.post(f"/api/internal/leads/{lead['id']}/qualification",json=payload).status_code==401
    saved=client.post(f"/api/internal/leads/{lead['id']}/qualification",json=payload,headers={'X-SalesFlow-Secret':'test-webhook'})
    assert saved.status_code==200
    detail=client.get(f"/api/leads/{lead['id']}",headers=auth).json()
    assert detail['score']==86
    assert detail['stage']=='Qualified'
    assert detail['qualification']['classification']=='Hot'

def test_pipeline_change_records_activity(client,lead_payload,auth):
    lead=client.post('/api/public/leads',json=lead_payload).json()
    response=client.patch(f"/api/leads/{lead['id']}/stage",json={'stage':'Contacted'},headers=auth)
    assert response.status_code==200
    detail=client.get(f"/api/leads/{lead['id']}",headers=auth).json()
    assert detail['stage']=='Contacted'
    assert any(a['type']=='pipeline_changed' for a in detail['activities'])

def test_appointment_association_is_idempotent(client,lead_payload,auth):
    lead=client.post('/api/public/leads',json=lead_payload).json()
    payload={"external_id":"cal-evt-1","email":lead['email'],"starts_at":"2026-09-15T10:00:00Z","ends_at":"2026-09-15T10:30:00Z","booking_url":"https://cal.com/example/demo"}
    headers={'X-SalesFlow-Secret':'test-webhook'}
    first=client.post('/api/internal/appointments',json=payload,headers=headers)
    second=client.post('/api/internal/appointments',json=payload,headers=headers)
    assert first.status_code==200
    assert second.json()['status']=='duplicate'
    detail=client.get(f"/api/leads/{lead['id']}",headers=auth).json()
    assert detail['stage']=='Meeting Scheduled'
    assert len(detail['appointments'])==1
