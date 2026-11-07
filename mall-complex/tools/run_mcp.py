import asyncio,json,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
async def main():
    async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(ROOT/'tools/blender_mcp.py')])) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=60)) as session:
            await session.initialize();print('MCP tools:',[t.name for t in (await session.list_tools()).tools],flush=True)
            inspect=await session.call_tool('blender_inspect',{});print(inspect.model_dump_json(),flush=True)
            start=await session.call_tool('blender_render_landmark',{'samples':24 if '--preview' in sys.argv else 64,'preview':'--preview' in sys.argv});print(start.model_dump_json(),flush=True)
            if start.isError:raise RuntimeError('MCP render call failed')
            while True:
                await asyncio.sleep(8);status=await session.call_tool('blender_render_status',{});report=json.loads(status.content[0].text);print(json.dumps(report,ensure_ascii=True),flush=True)
                if report['status']!='running':
                    (ROOT/'outputs/mcp-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                    if report['status']!='complete':raise RuntimeError('Blender rendering failed')
                    break
asyncio.run(main())
