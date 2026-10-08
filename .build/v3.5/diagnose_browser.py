import json,time,urllib.request,websocket,psutil
local=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for attempt in range(60):
 ports=set()
 for process in psutil.process_iter(['name']):
  if 'PHOTO-SEQUENCE-24' not in (process.info['name'] or ''):continue
  try:
   ports.update(c.laddr.port for c in process.net_connections(kind='inet') if c.status=='LISTEN' and c.laddr.ip=='127.0.0.1')
  except Exception:pass
 if ports:break
 time.sleep(.5)
print('Application local ports:',sorted(ports),flush=True)
for port in ports:
 try:
  with local.open('http://127.0.0.1:'+str(port)+'/',timeout=3) as response:
   data=response.read();print('Local application HTTP:',port,response.status,response.headers.get('Content-Type'),len(data),b'id="style"' in data,flush=True)
 except Exception as error:print('Local application HTTP error:',port,str(error),flush=True)
for attempt in range(15):
 try:
  with local.open('http://127.0.0.1:9222/json',timeout=1) as response:pages=json.load(response)
  targets=[p for p in pages if p.get('type')=='page']
  if targets:break
 except Exception:pass
 time.sleep(1)
else:
 print('No browser debugging target; local HTTP diagnosis completed.',flush=True);raise SystemExit(0)
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
