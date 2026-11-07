import asyncio,json,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
async def main():
    async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(ROOT/'tools/blender_mcp.py')])) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize();print((await session.list_tools()).model_dump_json(),flush=True)
            print((await session.call_tool('blender_start_residential_render',{})).model_dump_json(),flush=True)
            while True:
                await asyncio.sleep(5);r=await session.call_tool('blender_residential_status',{});report=json.loads(r.content[0].text);print(json.dumps(report,ensure_ascii=True),flush=True)
                if report['status']!='running':
                    if report['status']!='complete':raise RuntimeError(str(report))
                    break
asyncio.run(main())
