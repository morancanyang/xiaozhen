# 林序住区 · LINXU RESIDENTIAL GARDEN

双击 `林序住区.html` 即可离线查看。单文件已打包 Three.js、OrbitControls、模型生成代码及必要贴图；不需要服务器。开启浏览器硬件加速后，可拖拽旋转、右键平移、滚轮缩放，触屏支持双指缩放和平移。

场地为 112×112 米，Y 轴向上，地面中心为原点，入口朝 +Z。A/B/C/D 四栋分别为 22/20/18/16 层，采用浅灰墙面、灰蓝玻璃、分层阳台、平屋顶、机电设备、门厅雨棚和深绿色庭院。院内包括六米内部车道、停车区、步行连接、门卫室、儿童滑梯与秋千、长椅、灌木和乔木。所有模型内容位于街坊边界内，最高设备约 71.75 米。

每栋住宅具有独立节点和 ID。查看器提供全景、立面、门厅、游乐区及屋顶镜头，也可通过 A/B/C/D 按钮单独取景。支持暂停、动态速度、风动、居民与车辆、夜景和三级画质。居民与车辆沿预设路径移动，自动门响应居民接近，秋千、风扇及树冠产生动画，道闸响应接近车辆。GLB 保存一个时间点的静态姿态；实时动画由 HTML 和 JavaScript 驱动。

本次顺序为 Three.js 粗建模 → 细化并检查 → 导出实际几何快照 → 本地 stdio MCP 调用 Blender → 新开可见 Blender 窗口并实际渲染。实际渲染使用 Blender 5.2.2 LTS / Cycles / OPTIX GPU，64 采样，1800×1200，包含全景、立面、入口、游乐区、屋顶、夜景六张图片。`outputs/blender-result.json` 与日志记录真实结果。

Blender 的 `.blend` 文件中包含独立楼栋、场地、景观、游乐与生活组件，以及多个相机。MCP 打开窗口时显示全景渲染图；在图像区域按 Home 适配画面，Shift+F5 可切换回三维视口继续查看模型。

交付内容：

- `林序住区.html`：离线互动查看器。
- `model.mjs`：动态模型工厂，宿主提供 THREE。
- `integration-example.mjs`：千人小镇挂载示例。
- `residential-manifest.json`：尺度、楼栋和入口数据。
- `linxu-residential.glb`：完整静态模型。
- `林序住区.blend`：可编辑 Blender 场景。
- `outputs/blender-*.png`：六张实际渲染图。
- `outputs/01-blockout.png`、`02-*.png`：粗模和精修记录。
- `outputs/verification.json`：22 项浏览器检查。
- `src/`、`tools/`：源码、检查与 Blender MCP 工具。

## 接入接口

```js
import {mountResidential} from './integration-example.mjs';
const residential=mountResidential({THREE,scene,x:blockX,z:blockZ,groundY:streetLevel,blockSize:112});
// 加入城市已有帧循环，单位为秒。
residential.update(deltaSeconds);
residential.setDynamicsEnabled(true);
residential.setActivity({wind:true,traffic:true});
residential.setTimeOfDay(1); // 0 日间，1 夜间；宿主负责环境灯光
residential.setQuality('high'); // high / medium / low
const buildingA=residential.groups.get('A');
const snapshot=residential.exportScene();
residential.dispose();
```

工厂不创建相机、光源、渲染器或帧循环。`root` 统一缩放，`manifest.buildings` 和 `entrances` 保持 112 米原生局部坐标；使用 `root.localToWorld()` 转换入口世界位置。展示背景和摄影光照属于查看器，不包含在工厂模型内。此交付提供接入接口，尚未替换城市中的具体街坊。

## 修改与复查

HTML 无需安装依赖。开发时可安装 package.json 中的 Three.js 0.180.0、esbuild 0.25.0 后运行 `npm run build`。本机也可复用已有依赖。浏览器检查需要 Playwright 与 Edge。

```powershell
npm run check
npm run build
python tools/verify.py
python tools/inspect_model.py
..\city-atlas\.venv\Scripts\python.exe tools/run_blender_mcp.py
# 保持 Blender 场景与渲染图窗口打开：
..\city-atlas\.venv\Scripts\python.exe tools/open_blender_mcp.py
```

MCP 服务器为 `tools/blender_mcp.py`，提供实际可见窗口渲染、进度读取和打开交付场景的工具。渲染使用新进程，不覆盖其他 Blender 窗口中的文件。Three.js 许可见 `THREE-LICENSE.txt`。
