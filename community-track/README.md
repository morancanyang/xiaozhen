# 青禾运动场

为千人小镇单个 112 × 112 米正方形街坊制作的 Three.js 社区运动场。双击 `青禾运动场.html` 即可离线查看，HTML 已内嵌 Three.js、控制器、模型及程序纹理，无需服务器或网络。

## 尺寸与布局

- 单位米，Y 轴向上，地面中心为原点，正面入口朝 +Z。底座范围 X/Z 为 -56 至 56，底座最低处 Y=-0.4。
- 四条 1.1 米宽跑道：直段 52 米、内缘半径 23 米。第一道距内缘 0.3 米的测量线全长约 250.398 米；跑道外缘总长 106.8 米、总宽 54.8 米。
- 足球场 68 × 42 米，球门 5 × 2 米；按社区场地尺寸绘制边线、中圈、禁区、球门区、罚球点、罚球弧和角球弧。
- 本场为适配街坊的社区运动场，不是 400 米标准田径场或国际比赛规格足球场。调整 `blockSize` 会同比缩放所有构件，清单内跑道、球场、入口和灯位坐标仍为原生 112 米模型坐标。
- 西侧四排看台共 104 个座位；东侧替补席、雨棚、计分牌；四座 14 米灯塔；另有树木、围栏、排水沟、入口标识及垃圾箱。

## 查看与动态

鼠标左键拖动旋转，右键拖动平移，滚轮缩放；触屏单指旋转，双指缩放和平移。提供总览、俯视、跑道、球门、看台及场内六个视角。

16 名跑者分别沿四条封闭分道运动，手臂和腿部摆动；8 名球员步行动作配合足球循环轨迹。球赛为展示动画，没有实现球员控球、碰撞或真实比赛规则。草叶、树冠和旗帜有风动；计分牌轮换显示；天空云层缓慢移动。可暂停、调速、分别开关跑者/足球/风动，并切换三档细节与日夜场景。夜景含四盏实际 Three.js 聚光灯。

高细节模式含 22,000 片独立草叶，低档降为 2,000 片。橡胶跑道、铺装、草坪使用程序纹理及 PBR 材质；有完整几何球网。性能取决于设备；城市大场景建议使用 medium 或 low。

右上角可保存当前画面 PNG 或导出静态 GLB。静态 GLB 和 Blender 文件保存的是导出时姿态，实时跑步、足球及风动由 `model.mjs` 中的更新函数驱动。

## 接入千人小镇

当前交付独立运动场与接口，尚未修改千人小镇街坊配置。将 `model.mjs` 和 `integration-example.mjs` 放入宿主静态模块目录，在宿主已有 Three.js 中使用同一份 THREE 实例（本交付验证版本为 0.180.0）。创建模型需浏览器 DOM/Canvas 环境。

```js
import {mountSportsField,attachSportsFloodlights} from './integration-example.mjs';

const sports=mountSportsField({
  THREE, scene,
  x: parcel.centerX, z: parcel.centerZ,
  groundY: 0, blockSize: parcel.size,
  rotationY: 0, quality: 'medium'
});
const lighting=attachSportsFloodlights({THREE,scene,model:sports});

// 合入宿主已有的帧循环，不额外创建 requestAnimationFrame。
function updateCity(deltaSeconds){
  sports.update(deltaSeconds);
}
lighting.setNight(true);
// 卸载时：lighting.dispose(); sports.dispose();
```

`mountSportsField` 不添加相机、画布、页面控件或动画循环。模型工厂本身不添加场景灯光；可选 `attachSportsFloodlights` 由宿主调用，灯位按模型的尺寸、位置和旋转转换。灯光适配器在挂载时计算世界坐标，之后移动模型时需重建适配器。

接口：`root`、`groups`、`manifest`、`update(deltaSeconds)`、`setQuality('high'|'medium'|'low')`、`setTimeOfDay('day'|'night')`、`setDynamicsEnabled(boolean)`、`setActivity({wind,runners,football})`、`exportScene()`、`dispose()`。`setTimeOfDay` 调整模型灯具发光，宿主负责环境、太阳和聚光灯。`exportScene` 输出当前可见模型的世界空间快照。

`groups` 为 Map，包含 site、track、pitch、goals、stands、landscape、equipment、life 八个语义分组。`sports-manifest.json` 提供占地、入口、尺寸与灯位。`qinghe-sports-field.glb` 为通用静态模型。

## Blender 实际渲染

`青禾运动场.blend` 由本地 MCP 服务 `tools/blender_mcp.py` 导入 Three.js 实际几何快照生成，使用本机 Blender 5.2.2 LTS / Cycles GPU / 64 采样 / 降噪 / 1800 × 1200 渲染。`outputs/blender-*.png` 包含总览、俯视、跑道、球门、看台和夜景六张图。渲染使用 Cycles，不使用 Octane。

Blender 模型集合 `Sports field model only` 可单独移植；展示背景、相机、太阳和体积介质位于独立 `Presentation - not part of city module` 集合。纹理已打包到 blend。默认保存白天总览相机；夜场光照由渲染脚本创建和恢复。Blender 中人群按材质和分组批量合并，保留八个语义父级，精细编辑可从源代码重新生成。

复现：先导出 `outputs/sports-scene.json`，用含 `mcp` SDK 的 Python 执行 `tools/run_blender_mcp.py`。服务会打开独立可见 Blender 窗口并连续渲染；不会修改已有 Blender 场景。Python 路径与 Blender 路径按本机环境修改。

## 源码与验证

`src/model.js` 为建模及动态源码；`src/app.js` 为查看器；`src/shell.html` 和 `src/style.css` 为页面。安装 package.json 依赖后运行 `npm run build` 和 `npm run check`。单 HTML 产物可直接打开，无需安装依赖。

`tools/inspect_model.py` 保存粗模、精模多角度截图与建模快照；`tools/verify.py` 用 Playwright/Edge 离线验证交互、几何边界、动画、分道轨迹、质量档、导出及移动布局。`outputs/verification.json` 保存 30 项通过结果；`outputs/blender-result.json` 保存实际渲染信息。`tools/verify_blender.py` 检查已保存 blend 的组件、尺寸、纹理和相机。

Three.js 采用 MIT 协议，见 `THREE-LICENSE.txt`。
