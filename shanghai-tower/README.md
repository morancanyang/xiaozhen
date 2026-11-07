# 上海中心 · 云端之上

一个独立、可离线打开的 Three.js 建筑模型。当前千人小镇没有被本项目修改或自动移植。

## 打开模型

双击 **上海中心.html**。Three.js、控制器、几何、材质、天空和界面全部内嵌，运行无需网络、安装或外部资源。

- 左键旋转；右键或 Shift + 左键平移；滚轮缩放。
- 触屏使用单指旋转、双指缩放和平移。
- 五个视角：完整总览、云端仰望、幕墙细节、入口广场、螺旋楼冠。
- 空格暂停，H 恢复总览。用户拖动会停止自动巡游。
- 支持日光、日落、蓝调、夜色、时间流逝、动态速度、云雾、窗灯、行人和风动开关。
- 支持三档画质、边界显示、可选陆家嘴/黄浦江远景、PNG 和 GLB 导出。
- 使用与接入面板可选择当前画布、4K 或 8K 截图。导出前会检查 GPU 最大纹理尺寸；浏览器 8K 导出仍受设备资源限制。

## 尺寸

- 原建筑参考高度：632 米。
- 默认微缩展示高度：96 米；元数据中明确区分二者。
- 地块：112 × 112 米；实际广场范围 104 × 104 米，四周留出 4 米。
- Y 轴向上；X/Z 平面为地面。原点为广场地面完成面的中心，薄铺装下部低于原点约 0.18 米。
- 主塔连续扭转约 120°，逐渐收分；内层塔体与外层圆角三角形玻璃外皮分离；楼冠采用通透的不对称收束。
- 场地只有步行广场、景观和入口，没有机动车道路、停车场或车道标线。

模型是基于公开建筑形态的程序化演绎，并非测绘 BIM、施工模型或完整实物复刻。建筑外形参考：

- https://www.gensler.com/projects/shanghai-tower
- https://www.gensler.com/uploads/document/242/file/Shanghai_Tower_Facade_Design_Process_11_10_2011.pdf

## 可编辑文件

- `上海中心.html`：离线交互主文件，约 0.8 MB。
- `上海中心.glb`：建筑、广场和选定时刻人物的静态快照。
- `上海中心.blend`：同一几何导入 Blender 后的可编辑工程，含 Cycles 材质、摄影灯光、体积薄云和 96 帧相机关键帧。
- `shanghai-tower-module.mjs`：接入工厂，无外部 import，通过参数接收宿主 THREE。
- `town-integration.example.mjs`：千人小镇接入适配示例，不自动执行移植。
- `接入演示.html`：真正运行同源 iframe 接口的独立宿主演示，需要 HTTP 同源访问。
- `src/`：模型、展示、界面与演示源码。
- `outputs/`：渲染、实际截图、验证结果、交换数据与实时巡游视频。

## 千人小镇接入

推荐直接使用 ES 模块：

```js
import { createShanghaiTower } from './shanghai-tower-module.mjs';

const landmark = createShanghaiTower({
  THREE,                     // 传入千人小镇正在使用的 THREE
  footprint: 112,
  displayHeight: 96,
  seed: 632,
  quality: 'high',
  includeLandscape: true
});

landmark.model.position.set(blockCenterX, groundY, blockCenterZ);
cityRoot.add(landmark.model);

// 放入宿主已有的动画循环，不另建 requestAnimationFrame。
landmark.update(paused ? 0 : dt, {
  time: hostSimulationTime,
  paused,
  nightFactor: 0.8,            // 0 日间；1 夜间
  lights: true,
  people: true,
  wind: true,
  cameraDistance
});

landmark.setQuality('medium');
const bounds = landmark.getBounds(); // 当前世界坐标包围盒
// 删除时：landmark.dispose();
```

支持 `high` / `medium` / `low`。低画质关闭内部细部，宿主传入 cameraDistance 时，内部细部还会按距离隐藏。这是简化的细部分级，不是全场景自动性能预测。

工厂返回 `model`、`metadata`、`update`、`setQuality`、`getBounds`、`dispose`，另开放 parts 与 materials 供后续制作使用。工厂本身不创建 renderer、camera、页面 UI、灯光或独立时间循环。

另一种方式是同源加载单文件 HTML 的 `?mode=asset` 模式。该模式只公开 `window.QianrenLandmarks.createShanghaiTower`，不创建画布和展示程序。宿主可以通过隐藏 iframe 的 contentWindow 获取工厂，再传入自己的 THREE。接入演示已实际验证返回的 model 是宿主 THREE.Group 的实例。

两个 HTML 必须处于同一个 HTTP 源。不要把跨源 iframe 或 file:// 页面互访当作可行接入方案；不能通过 postMessage 直接传输 Object3D。

本地演示：在此目录执行 `node tools/preview.mjs`，访问 `http://127.0.0.1:5299/接入演示.html`。服务器仅供开发验证，单文件模型本身不需要服务器。

由宿主决定要替换哪个街坊、清理哪些旧几何、设置哪个地面高度。接入模块不自行删除城市内容，也不携带展示天空、远景、摄影灯光或云层。

## 动态与渲染边界

模型自带行人步行动画、接近入口时的门扇变化、植物风动和缓慢窗灯色温变化。天空密度采样、楼冠局部云体采样、飞鸟、远景和自动摄影运镜属于独立展示环境。

实时玻璃使用物理材质与环境反射近似，并非逐窗实时光线追踪。楼冠云体通过密度积分实现，实时遮挡是近似处理。人物、树叶和家具为程序化简化几何，局部室内表现不等同于完整精装室内。陆家嘴远景是简化氛围轮廓，并非另一个精确城区模型。

GLB 保存静态几何与材质，未烘焙程序动画或摄影环境。Blender 工程包含相机关键帧，但没有烘焙 HTML 全部动态。`outputs/上海中心-实时巡游.webm` 为实际录制的 8 秒 WebGL 画布视频，1280 × 960、目标 30 fps；它不是 Blender 离线视频。

## Blender MCP

使用项目局部 stdio MCP 桥接实际调用 Blender 5.2.2，在后台工厂启动中重建同一几何。未修改全局 MCP 配置或用户正在打开的场景。

工具为 `blender_inspect`、`blender_render_landmark`、`blender_render_status`。源数据为 `outputs/scene.json`，包含几何、实例变换、材质与嵌入标识贴图。

本次渲染为 Cycles / OPTIX / NVIDIA GeForce RTX 5060 Laptop GPU，48 采样与降噪。实际生成：

- 完整总览：1800 × 1350。
- 幕墙近景：1600 × 1400。
- 入口广场：1800 × 1200。
- 楼冠：1600 × 1400。
- 8K 低角度仰拍：4320 × 7680，原生像素渲染，未将小图放大。

Blender 对外层玻璃增加物理厚度与透射，补充石材微表面和真实体积薄云；实时与离线渲染效果会有差别。摄影地面采用远距离渐变衔接天空，是展示布景的一部分，不属于接入模型。

重建方法：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tools/requirements.txt
.\.venv\Scripts\python.exe tools/run_mcp.py
```

默认寻找 `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`，可通过 CITY_BLENDER_EXE 指定其他安装路径。MCP 客户端应保持运行直至任务结束。

## 构建和验证

`npm install` 后执行 `npm run build`。构建器也可以读取本工作区已经安装的 Three.js 和 esbuild；复制到另一台电脑时请正常安装 package.json 的依赖。

运行成品 HTML 不需要 npm。

`tools/review.py` 留存粗建模及多个精修视角，并从同一场景导出交换数据。`tools/verify.py` 检查断网、尺寸、交互、动态、昼夜、GLB、原生 4K 截图、手机布局、同源工厂和释放。先启动 `node tools/preview.mjs` 再运行验证脚本。验证依赖 Microsoft Edge 与 Python Playwright。

实际结果记录在 `outputs/verification.json`；MCP 与离线渲染记录分别在 `outputs/mcp-result.json` 和 `outputs/blender-result.json`。性能数据只代表本机无头浏览器测试，不保证其他设备达到同样帧率。
