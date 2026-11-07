"""A real MCP client which keeps its session alive while Blender stays open.

Windows MCP subprocess cleanup also closes child processes in its job group.
Therefore render completion is reported once, and the session deliberately
remains alive until the user closes the visible Blender window.
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]

async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT/'tools/blender_mcp.py')])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            available = await session.list_tools()
            print(json.dumps({'mcp_tools':[t.name for t in available.tools]}), flush=True)
            result = await session.call_tool('blender_start_mixeduse_render', {})
            if result.isError:
                raise RuntimeError(str(result.content))
            print(result.content[0].text, flush=True)
            completed = False
            last_progress = None
            while True:
                await asyncio.sleep(15 if completed else 5)
                result = await session.call_tool('blender_mixeduse_status', {})
                data = json.loads(result.content[0].text)
                if data['status'] == 'complete':
                    if not completed:
                        print(json.dumps(data,ensure_ascii=True), flush=True)
                        print(json.dumps({'mcp_session':'holding-visible-Blender','pid':data.get('pid'),'render_complete':True,'close_Blender_to_end_session':True}), flush=True)
                        completed = True
                    if not data.get('window_running'):
                        return
                    continue
                if data['status'] == 'failed':
                    raise RuntimeError(json.dumps(data,ensure_ascii=True))
                progress_key = (data.get('status'),data.get('view'),data.get('index'))
                if progress_key != last_progress:
                    print(json.dumps(data,ensure_ascii=True), flush=True)
                    last_progress = progress_key

if __name__ == '__main__':
    asyncio.run(main())
