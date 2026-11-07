import asyncio,json,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
async def main():
 async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(ROOT/'tools/blender_mcp.py')])) as (read,write):
  async with ClientSession(read,write) as s:
   await s.initialize();print('MCP_CONNECTED',flush=True);r=await s.call_tool('prepare_park_scene',{});print(r.model_dump_json(),flush=True)
   opened=False
   while True:
    await asyncio.sleep(5);r=await s.call_tool('render_status',{});d=json.loads(r.content[0].text);print(json.dumps(d,ensure_ascii=True),flush=True)
    if d['status']=='prepared' and not opened:
     r=await s.call_tool('open_blender_and_render',{});print(r.model_dump_json(),flush=True);opened=True
    if d['status']=='complete':return
    if d['status']=='failed':raise RuntimeError(str(d))
asyncio.run(main())
