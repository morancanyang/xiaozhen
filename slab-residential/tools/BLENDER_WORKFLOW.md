Blender 使用真实 MCP stdio 会话启动，与已经打开的 Blender 工程隔离。

先从已审阅的 Three.js 模型导出 `outputs/scene.json`，然后在项目目录执行：

```powershell
& '..\city-atlas\.venv\Scripts\python.exe' tools/run_blender_mcp.py
```

此命令通过 MCP 初始化、列举工具、调用 `blender_start_slab_render`，再使用
`blender_slab_status` 读取进度。它打开新的本机 Blender 5.2 可见窗口，保留原有
Blender 窗口，调用 Cycles 的真实界面渲染任务。完成后新窗口继续保留。

Windows 会在 MCP stdio 子进程清理时关闭同一进程组内的 Blender。为保留可见窗口，
客户端在渲染完成后输出一次完整结果，然后安静地保持 MCP 会话，每 15 秒检查窗口状态。
命令此时继续运行是预期行为；用户关闭 Blender 窗口后客户端才正常结束。
不要在渲染完成时终止这个保留会话，否则窗口也可能被系统清理。

几何来自 Three.js 的真实世界坐标快照，坐标转换为 `(x,-z,y)`，保留 UV、几何颜色、
实例颜色和可嵌入纹理。按楼栋所有者与材质合并，保留楼栋分组。摄影环境另置于独立集合。

输出包括 `浅序住区.blend`、3840×2880 总览、2560×1920 立面、入口和黄昏图。
`outputs/blender-result.json` 记录实际引擎、设备、采样、图片尺寸、源对象与导入几何统计。
优先使用可用的 OPTIX GPU；实际设备以该结果文件为准。

HTML 的程序化风动、窗帘与渐变灯光在浏览器中运行；Blender 保存其导出姿态和摄影灯光，
不声称包含相同的实时 JavaScript 动画系统。
