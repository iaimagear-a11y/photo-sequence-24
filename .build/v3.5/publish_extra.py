import os,json,pathlib,urllib.request,hashlib,tarfile,shutil
repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_TOKEN'];root=pathlib.Path(os.environ['RUNNER_TEMP'])/'ps24-private-source';out=pathlib.Path(os.environ['RUNNER_TEMP'])/'additional-packages';out.mkdir()
headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
base='https://api.github.com/repos/'+repo
with urllib.request.urlopen(urllib.request.Request(base+'/releases/tags/v3.5',headers=headers)) as response:release=json.load(response)
for src,name in [('android/app/build/outputs/apk/debug/app-debug.apk','PhotoSequence24-Android-v3.5-beta.apk'),('android/app/build/outputs/bundle/release/app-release.aab','PhotoSequence24-Android-v3.5-sin-firmar.aab')]:shutil.copyfile(root/src,out/name)
stage=out/'PhotoSequence24-Linux-v3.5';stage.mkdir();shutil.copytree(root/'desktop/dist/PhotoSequence24',stage/'PhotoSequence24')
for name in ['Instalar.sh','Desinstalar.sh','LEEME.txt']:
 shutil.copyfile(root/'desktop/installer/linux-studio'/name,stage/name)
 if name.endswith('.sh'):(stage/name).chmod(0o755)
for pdf in (root/'docs/manuales').glob('*.pdf'):shutil.copyfile(pdf,stage/pdf.name)
archive=out/'PhotoSequence24-Linux-v3.5-beta.tar.gz'
with tarfile.open(archive,'w:gz') as tar:tar.add(stage,arcname=stage.name)
files=[out/'PhotoSequence24-Android-v3.5-beta.apk',out/'PhotoSequence24-Android-v3.5-sin-firmar.aab',archive]
checksums=out/'SHA256SUMS-ANDROID-LINUX';checksums.write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name for f in files)+'\n');files.append(checksums)
existing={a['name'] for a in release['assets']}
for f in files:
 if f.name in existing:raise RuntimeError('Existing asset will not be overwritten: '+f.name)
 req=urllib.request.Request(release['upload_url'].split('{')[0]+'?name='+f.name,data=f.read_bytes(),headers={**headers,'Content-Type':'application/octet-stream'},method='POST')
 with urllib.request.urlopen(req,timeout=300) as response:r=json.load(response)
 print('Uploaded:',r['name'],r['size'],flush=True)
body=release['body']+'\n\nAndroid: APK beta firmado para pruebas (debug), AAB sin firmar; compilación y lint verificados. No está listo para Play Store sin firma propia y pruebas en dispositivos. Linux x86_64: paquete portable con instalación y desinstalación por usuario; arranque nativo y exportación FFmpeg verificados en Ubuntu 22.04. Requiere entorno gráfico y FFmpeg/FFprobe instalados. iOS: no se publica IPA; requiere Xcode, firma y pruebas en dispositivos.'
req=urllib.request.Request(base+'/releases/'+str(release['id']),data=json.dumps({'body':body}).encode(),headers={**headers,'Content-Type':'application/json'},method='PATCH')
with urllib.request.urlopen(req) as response:json.load(response)
