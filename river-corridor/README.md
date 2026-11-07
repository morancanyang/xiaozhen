# 青岚河 · 千人小镇中央水系

直接打开 `青岚河.html` 可离线查看互动模型，不需要网络或服务器。该文件已经打包 Three.js、控制器、模型生成代码、程序材质和贴图。需要开启浏览器硬件加速。

## 交付内容与尺度

河流占用原有 **64 × 600 米**预留带：X=-32～32、Z=-300～300，Y 轴向上。水面基准为 Y=-0.75 米，中心河床约低于水面 2～3 米，岸坡向两侧城市地面平缓抬升。地下基础延伸至 Y=-7.3 米，与现有城市底座连接。自然河道宽约 38.4～45.6 米，轻微摆动的中心线及宽度变化形成舒缓河湾。

场景包含连续河床、石滩、湿润岸线、碎石、砂砾材质、草叶、苔草、芦苇、乔木、灌木、漂木，以及六群共 72 条游鱼。几何与植被均在预留带内。完整场景的外包围范围及实际鱼群检查结果保存在 `outputs/verification.json`。

网页水体使用多层波纹、沿河道局部坐标流动的纹理、深度吸收、折射和真实平面反射。天空、岸树和城市建筑都会进入反射画面。阴影、光照和水色随宿主时段变化；鱼体、尾鳍与岸边植物具有独立的程序动画。

| 文件 | 用途 |
| --- | --- |
| `青岚河.html` | 独立离线互动查看器 |
| `river-model.mjs` | 接收宿主 THREE 的河流模型工厂 |
| `river-pass.mjs` | 反射、折射、深度缓冲与渲染状态管理 |
| `town-integration.mjs` | 当前千人小镇的安装适配器示例 |
| `river-manifest.json` | 米制范围、水位、组件和鱼群元数据 |
| `qinglan-river.glb` | 静态 PBR 模型 |
| `青岚河.blend` | 可编辑 Blender 场景，包含物理水体和五台相机 |
| `outputs/blender-*.png` | 五张实际 Cycles 渲染图，1800 × 1200 |
| `outputs/01-blockout.png` | 粗模记录 |
| `outputs/02-*.png` | 精修网页模型各视角记录 |
| `outputs/verification.json` | 34 项独立模型检查 |
| `outputs/city-integration/verification.json` | 26 项城市接入检查 |
| `outputs/blend-verification.json` | Blender 文件重新打开与物理水体检查 |

## 查看与控制

鼠标左键拖拽旋转、右键平移、滚轮缩放；触屏支持单指旋转、双指缩放与平移。查看器提供全景、河湾、岸线、游鱼和沿河五个视角，可调整水流速度、画质、风动、鱼群显示和夜景，并导出 PNG 或静态 GLB。

默认显示完整效果，低画质减少石块、草丛和鱼只数量，并降低反射缓冲分辨率。鱼群拥有分组路线、尺寸与颜色差异、身体及尾鳍摆动。水下可见度随水深与反射角度变化；低角度观察时，天空反射会自然遮蔽部分水下细节。

## 接入 API

```js
import {createRiver} from './river-model.mjs';
import {createRiverPass} from './river-pass.mjs';

const river=createRiver({THREE,quality:'high',seed:1102});
const riverPass=createRiverPass({THREE,river});
scene.add(river.root);

// 每帧更新后、宿主最终渲染前调用；deltaSeconds 使用秒。
river.update(deltaSeconds);
riverPass.beforeRender(renderer,scene,camera,{
  sunDirection:sun.position,
  sunColor:sun.color
});
renderer.render(scene,camera); // 也可继续使用宿主已有 composer

river.setFlowSpeed(1);           // 0～3 倍，独立于城市整体时间倍率
river.setFishVisible(true);
river.setWindEnabled(true);
river.setDynamicsEnabled(true); // false 时冻结模型动态
river.setTimeOfDay(0);           // 0 日间，1 夜间；灯光由宿主管理
river.setQuality('medium');      // high / medium / low
const snapshot=river.exportScene();
const staticClone=river.makeExportClone();

// 移除时释放各自拥有的资源。
riverPass.dispose();
river.dispose();
```

工厂不创建相机、灯光、渲染器或帧循环。反射适配器会临时隐藏水面，生成折射颜色与深度缓冲，再使用镜像相机及裁剪平面生成反射；结束后恢复宿主的渲染目标、裁剪、阴影更新和 XR 状态。反射的取样频率及分辨率随画质改变。集成使用 Three.js 0.180.0 完成验证。

`river.groups` 包含 terrain、water、stones、grass、trees、reeds、fish、details。`terrainHeight(x,z)`、`center(z)`、`halfWidth(z)` 可查询原生米制河床高度与河道形态。`waterUniforms` 为实际网页水体着色器参数；通过 `setTimeOfDay`、`setFlowSpeed` 等接口控制日常状态。

如果在其他城市使用，需要先为完整河槽移除遮挡的土层和地面。本项目在 `city-atlas/dist/city.js` 中将中央 64×600 米范围与既有车库开口一起进行底板分割，随后由 `river-site.js` 安装连续河床与基础。这一步保证水面下方不会出现旧地面穿插。默认坐标就是项目世界坐标，不需再次移动或缩放。

## 千人小镇中的行为

中央预留带已转换为青岚河，原有 16 个街坊及 49 栋建筑保留。医院、云际中心、陶里汇、上海中心、大学和穹光体育馆继续存在。

右侧新增“青岚河 · 沿岸”和“观察游鱼”定位按钮、鱼群显示和水流速度控制。全局暂停、动态倍率、风动、画质、昼夜与河流同步。现有自由视角可以沿水岸查看，入口仍为顶部“自由视角”。河流作为景观模块注册，不增加建筑数量。

城市 JSON 导出包含 `qinglan-river` 模块的世界坐标几何快照。整城 GLB 导出会将网页专用水体着色器替换成可交换的静态 PBR 水材质，保留河床、岸景和鱼群。GLB 和 Blender 文件保存一个时间点的静态姿态，实时波纹、鱼体变形、风动及缓冲反射由 JavaScript 模块驱动。

## Blender MCP 渲染

制作过程为粗模 → Three.js 材质和生态细化 → 网页多视角检查及修正 → 同一几何快照导出 → 本地 stdio MCP → Blender 实际导入、渲染及文件重开检查。

`tools/blender_mcp.py` 提供 `blender_start_river_render` 和 `blender_river_status`；`tools/run_blender_mcp.py` 使用 Python MCP SDK 建立会话并调用它们。后台 Blender 使用独立进程，不修改用户正在编辑的场景。

实际渲染为 **Blender 5.2.2 LTS / Cycles / OPTIX GPU / 64 采样 / AgX / 1800×1200**。物理水体根据同一河道轮廓封闭为吸收体，使用 IOR=1.333、体积吸收、细波法线和实际微小几何波动。五个视角为 Overview、Bend、Bank、Fish、Along。真实渲染信息保存在 `outputs/blender-result.json`。

## 修改、重建和复查

HTML 无需安装依赖。开发时可安装 package.json 的固定依赖后运行 `npm run build`；本机也能复用相邻 city-atlas 的 Three.js 与已有 esbuild。Python 检查工具使用 Playwright 和 Edge，MCP 工具另需 Python `mcp`。

```powershell
npm run check
npm run build
python tools/inspect_river.py
python tools/verify_river.py
..\city-atlas\.venv\Scripts\python.exe tools/run_blender_mcp.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b --factory-startup --python-exit-code 1 --python tools/verify_blend.py
```

城市测试脚本为 `city-atlas/tools/verify_river_integration.py`，需配合本地 5173 端口网站运行。测试覆盖预留范围、地下开挖、住宅记录、既有地标、水流和鱼群联动、画质、昼夜、GLB 与 JSON 导出、手机及自由视角。

实时反射会增加场景采样开销；实际帧率取决于硬件、分辨率和城市场景复杂度，测试日志中的帧率只代表本机。Three.js 许可见 `THREE-LICENSE.txt`。
