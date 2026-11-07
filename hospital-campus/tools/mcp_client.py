import socket,json,sys
from pathlib import Path
def call(code,timeout=180):
    s=socket.create_connection(('127.0.0.1',9876),5);s.settimeout(timeout)
    s.sendall(json.dumps({'type':'execute_code','params':{'code':code}}).encode())
    data=b''
    while True:
        part=s.recv(65536)
        if not part:break
        data+=part
        try:r=json.loads(data);break
        except json.JSONDecodeError:pass
    s.close();return r
if __name__=='__main__':
    code=Path(sys.argv[1]).read_text(encoding='utf8') if len(sys.argv)>1 else "import bpy; print('Blender',bpy.app.version_string); print('devices',[(d.name,d.type) for d in bpy.context.preferences.addons['cycles'].preferences.devices])"
    result=call(code,600);print(json.dumps(result,ensure_ascii=False));Path('mcp_last_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
