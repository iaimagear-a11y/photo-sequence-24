import os,json,pathlib,urllib.request,urllib.error,hashlib
repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_TOKEN'];root=pathlib.Path(os.environ['RUNNER_TEMP'])/'ps24-output'
headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
def request(url,data=None,method=None):
 h=dict(headers)
 if data is not None:h['Content-Type']='application/json'
 r=urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,headers=h,method=method)
 with urllib.request.urlopen(r,timeout=120) as response:return json.load(response)
base='https://api.github.com/repos/'+repo
try:release=request(base+'/releases/tags/v3.5')
except urllib.error.HTTPError as e:
 if e.code!=404:raise
 release=request(base+'/releases',{'tag_name':'v3.5','target_commitish':'main','name':'Photo Sequence 24 v3.5 - Beta','draft':False,'prerelease':True,'make_latest':'false','body':'Windows: instalador con desinstalador y EXE portable autónomo, compilados en GitHub Windows. Verificados mediante pruebas de exportación FFmpeg y arranque del puente nativo. Manuales ilustrados ES/EN incluidos. No tienen firma comercial; faltan pruebas de uso en distintas PC. Android/Linux y sus notas de validación se adjuntarán por separado. El código permanece privado.'},'POST')
files=[]
for pattern in ['Instalador_PHOTO_SEQUENCE_24_v3.5.exe','PHOTO-SEQUENCE-24-Windows-v3.5.exe','Manual_PhotoSequence24_v3.5_Castellano.pdf','Manual_PhotoSequence24_v3.5_English.pdf']:
 matches=list(root.glob('Windows-*/'+pattern));assert len(matches)==1,(pattern,len(matches));files+=matches
checksums=root/'SHA256SUMS-WINDOWS';checksums.write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name for f in files)+'\n');files.append(checksums)
existing={a['name'] for a in release['assets']}
for f in files:
 if f.name in existing:raise RuntimeError('Existing release asset will not be overwritten: '+f.name)
 url=release['upload_url'].split('{')[0]+'?name='+f.name
 r=urllib.request.Request(url,data=f.read_bytes(),headers={**headers,'Content-Type':'application/octet-stream'},method='POST')
 with urllib.request.urlopen(r,timeout=300) as response:result=json.load(response)
 print('Uploaded:',result['name'],result['size'],flush=True)
print('Release:',release['html_url'],flush=True)
