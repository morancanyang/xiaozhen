"""Keep a real MCP client/server session alive while local Blender renders."""
import asyncio,json,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
async def main():
    server=StdioServerParameters(command=sys.executable,args=[str(ROOT/'tools/blender_mcp.py')])
    async with stdio_client(server) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize();print('MCP_CONNECTED',flush=True)
            r=await session.call_tool('blender_inspect',{});print(r.model_dump_json(),flush=True)
            r=await session.call_tool('blender_render_landmark',{'samples':64,'preview':False});print(r.model_dump_json(),flush=True)
            if r.isError:raise RuntimeError('MCP render start failed')
            while True:
                await asyncio.sleep(5);r=await session.call_tool('blender_render_status',{});data=json.loads(r.content[0].text);print(json.dumps(data,ensure_ascii=True),flush=True)
                if data['status']=='complete':return
                if data['status']=='failed':raise RuntimeError('Blender render failed')
asyncio.run(main())
