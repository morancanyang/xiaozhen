# 穹光体育中心 · DOME ARENA

双击 `穹光体育中心.html` 即可离线查看，无需服务器或网络。Three.js、控制器、材质、字体贴图和模型生成代码均已打包进这个 HTML。建议使用开启硬件加速的 Edge 或 Chrome。

## 场地与建筑

完整街坊为 **112 × 112 米**，主体为 78 × 66 米椭圆形综合体育馆，建筑顶点约 32.8 米，四座投光灯塔约 38 米。地面以 Y=0 为基准，前门朝 +Z，原点位于正方形街坊中心。地板向下延伸 0.4 米；飞鸟动画的预留高度为 41 米。所有内容均限制在街坊平面边界内。

银蓝金属分板穹顶、中央采光天窗、双弦拱形钢桁架、玻璃幕墙、三层外立面分格、3142 个蓝绿座椅、球场和篮架、悬挂信息屏、入口铜色雨棚、多级台阶、无障碍坡道、后勤设备及风扇、四座格构灯塔、广场水景、旗杆、乔木、长椅、排水构件与内部后勤车道组成完整院区。主体采用银蓝、深海蓝、青绿玻璃与香槟铜配色。

已提供人流行走、车辆循环、自动门响应、扶梯踏步、设备风扇、水景、旗帜和树冠风动、飞鸟、信息屏切换、流云反射及昼夜转换。车辆为演示循环路径；这些场景动画由 JavaScript 驱动。

## 操作

- 左键拖拽旋转，右键或 Shift＋左键平移，滚轮缩放；触屏支持单指旋转、双指缩放和平移。
- “全景 / 仰望 / 广场 / 钢构 / 屋顶 / 场馆”定位预设镜头。进入钢构或场馆视角会隐藏屋面；“显示完整屋面”可随时恢复。
- 空格暂停或继续动态，H 回到全景。可切换正交投影、画质、昼夜、风动、人流、自动巡游和时间流速。
- 点击建筑部位显示信息。“保存画面”导出 PNG；“导出模型”导出完整静态 GLB，即使当前隐藏屋面，也会包含完整屋面。

## 交付文件

| 文件 | 用途 |
| --- | --- |
| `穹光体育中心.html` | 可独立打开的单文件互动模型 |
| `arena-module.mjs` | 使用宿主 THREE 的动态模型工厂 |
| `integration-example.mjs` | 可直接导入的街坊挂载适配器，含可选投光灯 |
| `arena-manifest.json` | 原生尺度、入口、灯具和边界信息 |
| `dome-arena.glb` | 完整静态几何、PBR 材质与贴图 |
| `穹光体育中心.blend` | Blender 可编辑日景、夜景两个场景 |
| `outputs/blender-*.png` | 7 张实际 Blender 渲染图，1800 × 1200 |
| `outputs/01-graybox.png` | 首轮粗模记录 |
| `outputs/02-*.png` | 网页模型细化后的各视角截图 |
| `outputs/verification.json` | 浏览器交互与资源检查结果 |

## 接入千人小镇

推荐宿主继续使用自身的 Three.js、渲染器、相机、光照、环境贴图、后处理和帧循环。模型工厂不创建相机、光源、RAF 或全局背景；接入文件不携带展示台背景。现有城市道路由宿主管理，本模型只携带院区内部车道与广场。

```js
import {mountArena} from './integration-example.mjs';

const arenaBlock = mountArena({
  THREE, scene,
  center: {x: blockX, z: blockZ}, // 目标街坊中心
  groundY: streetLevel,
  blockSize: 112,               // 根据现有街坊内净尺寸缩放
  rotationY: 0,                 // 弧度；0 时入口朝 +Z
  quality: 'high',
  fixtureLights: true           // 可选真实投光灯，默认不增加阴影贴图
});

// 加入已有帧循环，传入秒数，建议每帧 dt <= 0.1。
arenaBlock.update(deltaSeconds);
// 从城市昼夜系统传入 0（日间）至 1（夜间）。
arenaBlock.setNight(nightAmount);
// 入口世界坐标，自动应用缩放、旋转和位移。
const mainEntrance = arenaBlock.entryWorld('public');
// 从城市移除并释放模型资源：
arenaBlock.dispose();
```

更底层的接口为：

```js
import {createArenaComplex} from './arena-module.mjs';
const arena = createArenaComplex({THREE, blockSize:112, quality:'high', embedded:true, seed:2026});
scene.add(arena.root);
arena.update(deltaSeconds);
arena.setQuality('high');          // high / medium / low
arena.setDynamicsEnabled(false);   // 暂停所有模型动画
arena.setActivity({people:true, traffic:true, wind:true});
arena.setRoofVisible(false);
arena.setTimeOfDay(1);             // 发光材质，场景灯光由宿主管理
const snapshot = arena.exportScene();
arena.dispose();
```

`arena.groups` 为包含 site、architecture、structure、roof、interior、landscape、lights、life 的 Map。可分别管理场地、建筑、结构、屋面、室内、景观、灯塔构件与动态角色。

清单中的入口、灯具、bounds 和 animatedBounds 使用 **112 米原生局部坐标**，不会随着 `blockSize` 改写数值；`root` 已统一缩放。转换到世界坐标时必须调用 `root.localToWorld()`；不要再次手动缩放后再调用该方法。`footprint`、`height` 和 `buildingHeight` 是按 blockSize 换算后的尺寸。导出的静态清单来自独立查看器；实际接入应以工厂返回的 `manifest` 为准。

`lights` 组只包含灯塔几何。`manifest.lightFixtures` 提供灯位与照射目标。示例适配器可以增加四盏宿主灯光；入口暖光、日光、天空反射、泛光和体积光由城市自身环境设置。推荐 THREE r180；本次使用 0.180.0 完成验证。

GLB 与 Blender 文件保存当前时间点的静态模型，JavaScript 程序动画保留在 HTML 和模块中。Blender 日景渲染中的钢构、室内视角隐藏屋面；重新打开 `.blend` 时默认恢复完整屋面，切换相应相机后可在 roof 组中手动控制显示。

## Blender MCP 实际渲染

流程为 Three.js 粗建模 → 材质和结构细化 → 离线浏览器检查 → 导出同一模型的几何快照 → 项目独立的 stdio MCP → Blender 后台导入和渲染。

`tools/blender_mcp.py` 是本项目专用 MCP 服务器，工具为 `blender_start_arena_render` 与 `blender_arena_status`。`tools/run_blender_mcp.py` 使用 Python MCP SDK 建立真实 MCP 会话，再启动本地 Blender；独立后台进程不会修改用户正在打开的 Blender 场景。可通过 `tools/inspect_arena.py` 更新几何快照后重渲染。

本次实际使用 **Blender 5.2.2 LTS / Cycles / OPTIX GPU / 64 采样 / AgX**。本机未安装可用 Octane，因此交付图片使用 Cycles，不包含 Octane 渲染结果。`outputs/blender-result.json` 与 `outputs/blender-render.log` 保存实际渲染信息。

## 本地重建与验证

交付 HTML 本身无需安装依赖。修改源码时，可在本目录安装 package.json 中的固定版本依赖后运行 `npm run build`；当前机器也能复用相邻 city-atlas 的 Three.js 和已有 esbuild。Python 工具需要 Playwright、Edge；Blender MCP 客户端另需 Python `mcp`。当前机器可使用 `../city-atlas/.venv/Scripts/python.exe` 运行 MCP 客户端。

```powershell
npm run check
npm run build
python tools/verify_arena.py
python tools/verify_integration.py
python tools/inspect_arena.py
..\city-atlas\.venv\Scripts\python.exe tools/run_blender_mcp.py
```

模型使用实例化批次和三级细节，可通过“流畅”模式降低开销。实际帧率取决于设备、分辨率、阴影和后处理设置；测试日志中的帧率是本机测试结果。

Three.js 许可见 `THREE-LICENSE.txt`。本次交付为独立体育馆模型与接入接口，尚未替换现有城市中的任何街坊。
