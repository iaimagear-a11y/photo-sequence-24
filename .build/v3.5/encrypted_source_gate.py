# Public build transport only. Application source never enters this repository as plaintext.
import os,json,time,base64,hashlib,io,zipfile,pathlib,urllib.request,urllib.error
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
repo=os.environ['GITHUB_REPOSITORY'];branch=os.environ['SOURCE_BRANCH'];token=os.environ['GH_TOKEN'];run=os.environ['GITHUB_RUN_ID']
def api(path,data=None,method=None):
 headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
 if data is not None:headers['Content-Type']='application/json'
 req=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
 with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
pem=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
fingerprint=hashlib.sha256(pem.encode()).hexdigest()
info={'run_id':run,'fingerprint':fingerprint,'public_key':pem}
path='.build/v3.5/public-key.json'
try:previous=api('contents/'+path+'?ref='+branch);sha=previous['sha']
except urllib.error.HTTPError as e:
 if e.code!=404:raise
 sha=None
body={'message':'Publish temporary Windows build public key','branch':branch,'content':base64.b64encode(json.dumps(info).encode()).decode()}
if sha:body['sha']=sha
api('contents/'+path,body,'PUT')
print('Public build key available. Private key stays only in this runner memory.',flush=True)
for attempt in range(180):
 try:
  pointer=api('contents/.build/v3.5/encrypted-pointer.json?ref='+branch)
  pointer=json.loads(base64.b64decode(pointer['content']))
  if pointer['run_id']!=run or pointer['fingerprint']!=fingerprint:raise ValueError('Waiting for the current run payload')
  blob=api('git/blobs/'+pointer['blob_sha']);envelope=json.loads(base64.b64decode(blob['content']))
  if envelope['fingerprint']!=fingerprint:raise ValueError('Wrong recipient key')
  aeskey=key.decrypt(base64.b64decode(envelope['wrapped_key']),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
  plain=AESGCM(aeskey).decrypt(base64.b64decode(envelope['nonce']),base64.b64decode(envelope['ciphertext']),run.encode())
  if hashlib.sha256(plain).hexdigest()!=envelope['sha256']:raise ValueError('Source checksum mismatch')
  dest=pathlib.Path(os.environ['RUNNER_TEMP'])/'ps24-private-source';dest.mkdir(exist_ok=True)
  with zipfile.ZipFile(io.BytesIO(plain)) as archive:
   for item in archive.infolist():
    path=pathlib.PurePosixPath(item.filename)
    if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe ZIP path')
   archive.extractall(dest)
  del plain,aeskey,key
  print('Authenticated source decrypted privately. No private keys or plaintext source are uploaded.',flush=True)
  break
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
 except ValueError as e:
  if str(e)!='Waiting for the current run payload':raise
 time.sleep(10)
else:raise TimeoutError('No encrypted source received within 30 minutes')
