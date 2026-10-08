import json,time,urllib.request,websocket
for attempt in range(90):
 try:
  with urllib.request.urlopen('http://127.0.0.1:9222/json',timeout=2) as response:pages=json.load(response)
  targets=[p for p in pages if p.get('type')=='page']
  if targets:break
 except Exception:pass
 time.sleep(1)
else:raise RuntimeError('No browser debugging target')
for page in targets:
 print('Browser target:',page.get('url'),page.get('title'),flush=True)
 ws=websocket.create_connection(page['webSocketDebuggerUrl'],timeout=10,suppress_origin=True)
 expression="JSON.stringify({url:location.href,title:document.title,body:document.body?.innerText.slice(0,500),styles:document.querySelectorAll('#style option').length,ready:document.readyState})"
 for index in range(3):
  ws.send(json.dumps({'id':index+1,'method':'Runtime.evaluate','params':{'expression':expression,'returnByValue':True}}))
  while True:
   response=json.loads(ws.recv())
   if response.get('id')==index+1:break
  print('Browser state:',response.get('result'),flush=True);time.sleep(3)
 ws.close()
 if page.get('url','').startswith('http://127.0.0.1'):
  try:
   with urllib.request.urlopen(page['url'],timeout=5) as response:print('Local HTTP:',response.status,response.headers.get('Content-Type'),len(response.read()),flush=True)
  except Exception as error:print('Local HTTP error:',str(error),flush=True)
