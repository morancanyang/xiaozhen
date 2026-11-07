# 霁衡中心 · JIHENG ONE

112 × 112 米标准街区上的银蓝色收分地标写字楼。建筑总高 184 米，4 层石材商业裙楼和 42 层办公空间，顶部为机电设备层。暂未绑定千人小镇的具体 BLK。

## 直接使用

双击 `霁衡中心.html`，使用支持 WebGL2 的 Edge 或 Chrome 打开。Three.js、控件、程序化材质与模型均内嵌在该文件中，不需要联网或启动服务器。

- 左键拖拽旋转，右键拖拽平移，滚轮缩放；触屏支持单指旋转、双指平移与缩放。
- 顶部提供总览、正立面、俯视、仰视、入口、退台和屋顶视角。可切换正交、透视。
- 开启“自由视角”后，在画面上点击，再使用 WASD 移动、Q/E 升降、Shift 加速。
- 右侧可单独观察、导出九类构件，调整晨光、白昼、黄昏、夜景与白底环境。
- 行人、车辆、风动和机电可独立控制，支持暂停和速度调整。画质分为完整、均衡和流畅三个级别。
- “导出完整模型”生成 GLB；“保存当前画面”生成当前视口 PNG。

## 模型构成

主体三段分别为 48×42、40×36、32×30 米，每段 14 层，办公层高 3.7 米。商业裙楼主体为 72×64 米；挑檐在地块内部。建筑高度含设备层和避雷设施。

模型包含约一万一个可导出构件实例：分层幕墙、铝框、背衬板、部分可透视办公室、退台花池与座椅、屋顶百叶、六台冷却设备和风扇、检修通道、避雷针、入口雨棚、自动门、两部裙楼观光电梯、广场拼缝、盲道、停车位、充电设施、排水口、路灯、门卫室及下沉车库坡道。树冠和道路均限制在标准地块范围内。

生活动态包括 22 名行人、2 辆循环行驶车辆、4 辆停放车辆、自动门感应、道闸、鸟群、树冠风动、电梯停层和机电风扇。车辆采用预设路线、接近道闸减速等待、斑马线附近周期让行；这是建筑演示级交通动画。观光电梯服务于裙楼展示，并非超高层完整电梯系统。部分办公室设置家具，其余区域采用背景内衬，未制作整栋可漫游室内。

`JH-01` 为建筑根组，下面有 lower、middle、upper、podium、roof 和 terraces 六个可编辑建筑部分；site、landscape 和 life 为地面与日常部分。网页中使用实例化减少绘制开销；GLB 保留实例与分组。Blender 工程将实例转成按构件类别、材质组织的真实网格，便于进一步编辑。

## 千人小镇接口

`model.mjs` 不导入第二份 Three.js，不创建相机、灯光、渲染器或 requestAnimationFrame。宿主传入自己的 THREE 命名空间。默认模型中心在原点，Y 向上，+Z 为主入口方向，地块边界为 X/Z ±56 米；地面标高为 0，坡道最低为 -2.8 米。

```js
import {mountLandmarkOffice, attachLandmarkLights} from './integration-example.mjs';

const office = mountLandmarkOffice({
  THREE, scene,
  x: block.x, z: block.z,
  groundY: 0.34, blockSize: 112,
  rotationY: 0, quality: 'high'
});
const lighting = attachLandmarkLights({THREE, scene, model: office});

// 由宿主现有动画循环调用；dt 单位为秒。
office.update(dt);
office.setActivity({wind: true, people: true, vehicles: true, mechanical: true});
office.setDynamicsEnabled(true);
lighting.setNight(0); // 0～1，同步窗灯、标识和 16 盏实际点光源。
// 改动模型位置、旋转或缩放后：
lighting.sync();

// 移除地块时：
lighting.dispose();
office.dispose();
```

工厂为 `createLandmarkOffice({THREE, blockSize:112, quality:'high', coarse:false})`，返回 root、groups、buildings、manifest、update、setTimeOfDay、setQuality、setDynamicsEnabled、setActivity、getManifest、exportScene 和 dispose。blockSize 通过整体等比缩放适配；manifest 的构造尺寸与高度记录原始米制尺寸，实际缩放量见 root.scale。

`exportScene({partId})` 返回当前可见细节的世界坐标几何快照，包含几何、法线、UV、材质和实例矩阵。HTML 的完整导出会临时恢复所有构件及最高细节，完成后保留之前的观察状态。GLB 与 Blender 是静态姿态；接入城市后，完整动态由 `model.mjs` 驱动。背景、摄影灯、天空和展示地平面均不进入模型接口或 GLB。

已使用千人小镇实际的 Three.js 0.180.0 命名空间通过接入检查；独立展示文件内嵌 Three.js 0.187.0。原生工厂可用于宿主已经实例化的 Three.js，无须引入本页面的渲染系统。浅层位移与城市光照均交由宿主统一管理，地块外接路面由城市的地块适配器处理。

## Blender 与图片

通过项目内真实 MCP stdio 服务启动本机 Blender 5.2.2 LTS，导入 Three.js 的 `outputs/office-scene.json`，使用 Cycles / OptiX GPU 进行实际渲染。坐标转换为 Three.js `(x,y,z)` → Blender `(x,-z,y)`，单位为米；模型与摄影布景分开存放。

- `霁衡中心.blend`：可编辑工程，纹理已打包，包含七个观察相机与纯白摄影配置。
- `outputs/霁衡中心-8K.png`：7680×4320 正交主图，96 采样及降噪。
- `outputs/blender-white.png`：纯白摄影预览。
- `outputs/blender-overview.png` 等：晨光鸟瞰、立面、俯视、仰视、入口、退台、屋顶和夜景，1800×1200。

实际使用 Cycles，未使用 Octane 插件。模型用于建筑可视化和千人小镇的微缩展示，后续可继续增补室内与施工级构造。

## 源码与复现

`src/model.js` 是可读建模源码，`src/app.js` 为交互展示，`src/shell.html`、`src/style.css` 为界面；`model.mjs` 与模型源码一致。查询参数 `?coarse` 可查看粗建模体量。

在本项目目录运行 `npm install`、`npm run build` 可重新生成 HTML。构建脚本也兼容当前本机已有的依赖目录。单文件成品的使用不需要安装依赖。

`tools/inspect_model.py` 采集 Three.js 粗模、精模与几何快照；`tools/verify.py` 验证离线交互及 300 秒动态路线；`tools/verify_integration.py` 验证宿主接入与资源释放；`tools/verify_blender.py` 验证工程、比例、纹理及 8K 图片。检查报告位于 outputs。

本机 MCP 桥接为 `tools/blender_mcp.py` 和 `tools/studio_mcp.py`，客户端分别为 `tools/run_blender_mcp.py` 与 `tools/run_studio_mcp.py`。使用本机已安装 mcp Python SDK 的解释器运行。桥接只启动自己的独立 Blender 进程，不更改用户其他 Blender 工程。
