# 云际中心 · SKYLINE ONE

112 × 112 米正方形街坊、224 米总高、55 层的独立 Three.js 建筑模型。塔楼 52 层，裙房 3 层。模型包含三段退台、玻璃幕墙、铜色框架、入口广场、屋顶花园、机电层、停机坪、车库坡道与配套设施。

## 打开

直接双击 `云际中心.html`，使用开启硬件加速的现代浏览器打开。Three.js、OrbitControls、导出器、后期效果与所有模型资源均已内嵌，断网可运行，无需本地服务器。

左键旋转，右键或 Shift＋左键平移，滚轮缩放；触屏单指旋转、双指平移缩放。空格暂停动态，H 回到全景。顶部视角可观察广场、车库、退台和停机坪，点击建筑可查看信息。右侧提供时段、画质、速度及动态开关。

初始为最高画质。动态包括天空云层与环境反射更新、风动植物和旗帜、飞鸟、水景、人群、车辆停靠及跟随、车库车辆、自动门和抬杆、机电风扇、直升机起降与灯光。直升机约 100 秒一个循环；可提高时间流速或关闭起降演示。

## 文件

- `云际中心.html`：离线单文件交互页面。
- `skyline-module.mjs`：无需导入 Three.js 的独立模型工厂，由宿主注入同一份 THREE。
- `skyline-manifest.json`：尺度、坐标、出入口和地下开洞范围。
- `town-integration.example.mjs`：千人小镇接入示例。
- `skyline-one.glb`：当前静态模型，可用于后续三维编辑；实时动画保留在 HTML 和模型工厂中。
- `云际中心.blend`：由本地 Blender MCP 实际生成的工程，包含日景、夜景及可编辑镜头关键帧。
- `outputs/blender-*.png`：七张 1800 × 1200、Cycles / OPTIX GPU、64 采样实际渲染图。
- `outputs/final-*.png`：浏览器中的实际截图，含手机布局。
- `outputs/01-graybox.png`：粗模阶段截图；`?coarse` 可查看粗模。
- `outputs/verification.json`：38 项交互、模型和导出检查记录。

## 接入千人小镇

模型尚未安装到现有城市中的某个街坊。指定街坊后，由宿主清除该地块原建筑及景观，再安装整个模型。

```js
import {createSkylineTower} from './skyline-module.mjs';

const tower=createSkylineTower({
  THREE, blockSize:112, quality:'high', embedded:true, seed:1101
});
tower.root.position.set(blockCenterX,groundY,blockCenterZ);
cityRoot.add(tower.root);

// 在宿主自己的帧循环中执行，不启动第二个 RAF。
tower.setDynamicsEnabled(!paused);
tower.setActivity({traffic:true,wind:true,flight:true});
tower.setTimeOfDay('morning'); // day / evening / night，或 0—1 夜景强度
tower.update(deltaSeconds*speed);

// 移除时释放工厂拥有的所有资源。
tower.dispose();
```

模型工厂不创建相机、渲染器、光源、天空、环境贴图或全局雾效。接入后应使用城市原有环境、天空与后期。玻璃通过宿主的 `scene.environment` 反射天空；独立页面会定时更新程序化云层的 PMREM 环境。

`tower.groups` 包含 tower、podium、roof、landscape、site、life。可按节点进行选择与管理。`tower.exportScene()` 保存当前可见几何、材质和实例矩阵，`snapshotSpace` 为 `world`。

### 坐标和道路

单位米，Y 向上，+Z 为主入口；原点位于街坊地面中心。默认边界 X/Z 均为 [-56,56]。约 224 米为静态建筑高度；直升机飞行包络最高约 251 米。

`manifest` 中的 bounds、excavations、entrances、buildings 坐标采用原始 112 米模型的局部米制坐标。`blockSize` 不等于 112 时，`root.scale` 统一缩放；通过 `root.localToWorld()` 转为城市世界坐标。`manifest.height` 和 footprint 已体现整体缩放。

车库需要宿主对地板、底板和铺路面同步开洞：局部 X ∈ [-47,-35]，Z ∈ [-39,-12]，坑底 Y≈-4.5。独立页面的展示背景已切开，接入时须对实际城市底板处理。出入口应与宿主道路坡接，避免覆盖公共道路或形成高度台阶。

112 米场地包含内部车行环路，公用城市道路仍由宿主管理。人车路线和直升机均为建筑展示动画。

## 建模与渲染记录

先完成米制粗模，再完善分层立面、窗框、结构斜撑、室内层次、退台栏杆、种植池、入口雨棚、机电百叶、风扇和检修设施。检查过程中修正了屋顶边缘比例、地块边界、夜景窗灯、入口玻璃以及地平线背景。

重复建筑部件采用 InstancedMesh。最高画质显示细部，均衡与流畅档逐级减少装饰几何、植被细节及人群。独立页面采用 4096 像素阴影、抗锯齿、HDR 环境反射、深度裁切的体积雾积分、泛光与 ACES 色调映射。玻璃、金属、石材等采用 PBR 参数；人物和车辆为适合整体场景的简化模型。

本机通过 localhost:9876 上运行的 Blender MCP 导入 Three.js 的实际几何快照，再由 MCP 启动隐藏的后台 Blender / Cycles 任务。Blender 版本为 5.2.2，使用 OPTIX GPU。日夜场景和七张渲染图均已实际输出。网页风动、水面着色器与实时演员动画不自动转成 Blender 动画；工程保留静态模型及 144 帧可编辑镜头运动。

## 重建和验证

源码位于 `src/`。已提供的 HTML 无需安装依赖。修改源码后，在安装 Node.js 的环境执行 `npm install`、`npm run check`、`npm run build`。生成文件为 `云际中心.html` 和 `skyline-module.mjs`。

浏览器检查需要 Python Playwright 和本机 Microsoft Edge：

```powershell
python tools/verify_tower.py
```

Blender 工具：`tools/mcp_client.py` 发送代码至已有的本地 MCP；`tools/blender_import.py` 导入 `outputs/skyline-scene.json`；`tools/start_render_mcp.py` 启动 `tools/render_blender.py`。导入会创建独立场景，不覆盖用户原有场景。渲染文件和日志位于 outputs。

Three.js 0.180.0 的 MIT 许可见 `THREE-LICENSE.txt`，HTML 内也保留依赖许可。
