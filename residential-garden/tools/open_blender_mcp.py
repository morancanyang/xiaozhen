import asyncio,sys,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
async def main():
    async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(ROOT/'tools/blender_mcp.py')])) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize();r=await session.call_tool('blender_open_residential_scene',{});print(r.content[0].text,flush=True)
            while True:
                await asyncio.sleep(15);r=await session.call_tool('blender_residential_status',{});d=json.loads(r.content[0].text)
                if not d['window_running']:break
asyncio.run(main())
