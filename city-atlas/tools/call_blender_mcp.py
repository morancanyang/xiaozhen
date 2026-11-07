import asyncio,json,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]
async def main():
    server=StdioServerParameters(command=sys.executable,args=[str(ROOT/'tools/blender_mcp.py')])
    async with stdio_client(server) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=40)) as session:
            await session.initialize()
            tools=await session.list_tools()
            print(json.dumps({'tools':[t.name for t in tools.tools]}))
            name=sys.argv[1] if len(sys.argv)>1 else 'blender_inspect_environment'
            arguments=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
            result=await session.call_tool(name,arguments)
            print(result.model_dump_json())
            if result.isError:raise RuntimeError('MCP tool failed')
            if name=='blender_start_city_render':
                content=json.loads(result.content[0].text)
                (ROOT/'outputs/active-render.json').write_text(json.dumps(content,indent=2),encoding='utf-8')
                while True:
                    await asyncio.sleep(5)
                    status=await session.call_tool('blender_get_render_status',{'job_id':content['job_id']})
                    report=json.loads(status.content[0].text)
                    print(json.dumps(report,ensure_ascii=True),flush=True)
                    if report['status']!='running':
                        if report['status']=='failed':raise RuntimeError('Blender render failed: '+str(report['recent_log']))
                        break

asyncio.run(main())
