# 浅序住区 · 独立板式住宅模型

双击 `浅序住区.html` 即可离线打开。Three.js、OrbitControls、GLTFExporter、模型代码及程序材质均内嵌在同一个 HTML 内。无须安装 Node 或启动服务器。浏览器需要支持 WebGL。

模型以米为单位，Y 轴向上，原点位于 112 × 112 米地块的中心连接面。三栋板式住宅平行排列，16 / 18 / 20 层；每栋包含三个单元。采用浅米白外墙、浅灰分隔、封闭阳台、玻璃窗、入口雨棚、缓坡及屋顶设备。庭院配置连续人行步道和克制的绿化。

鼠标左键旋转、右键平移、滚轮缩放；触屏支持旋转与双指操作。页面提供小区总览、立面、入口、屋顶观察，晨光/日间/黄昏/夜景，暂停、风力、速度及三档画质。GLB 按完整几何导出，不包含预览场景中的相机、天空和摄影地面。GLB 保留静态外观；程序风动、窗帘和照明变化在 HTML 及模型模块中运行。

## 城市接入

`residential-block.mjs` 导出 `createResidentialBlock({THREE, footprint=112, quality='high', seed=1104})`。宿主传入正在使用的 THREE，不创建额外渲染器、相机或动画循环。参见 `integration-example.mjs`。

实例提供 root、update(delta,state)、setQuality、setTimeOfDay、getBounds、exportScene、makeExportClone、exportGLB({GLTFExporter}) 和 dispose。动画 delta 使用宿主已经应用速度倍率后的值。宿主应提供 wind、windStrength、paused、nightFactor。原点 Y=0 为地块连接面，千人小镇可通过 groundY=0.34 对齐原有铺装。单独楼栋分组可用于选择和后续更换。

本次仅交付独立模型与接入接口，未替换千人小镇的任何 BLK 地块。

## 工程与验证

`src/` 为可编辑源码；`npm install` 后运行 `npm run build` 可重建离线 HTML。`?coarse=1` 显示体量阶段，最终版本默认显示精修模型。`tools/verify_model.py` 验证实际几何、离线浏览、交互、动态、导出和移动端，并保存截图及 Blender 所需的同源几何快照。

Blender 由 `tools/` 内的本地 MCP stdio 工作流驱动，读取同一 Three.js 快照建立可编辑场景。Cycles 生成的实际图片、渲染设置与状态保存在 `outputs/`，最终 `.blend` 文件保存在本目录。具体执行命令见 `tools/BLENDER_WORKFLOW.md`。


最终交付验证：42 项检查通过。Blender 5.2.2 LTS 使用 Cycles、RTX 5060 Laptop GPU、64 samples 实际渲染，包含 3840×2880 总览和 2560×1920 立面、入口、黄昏图。9 处入口坡道为封闭实体，与平台完整连接并接地。完整源码、几何快照、渲染结果与模型文件见本目录；`residential-manifest.json` 记录接口、尺寸和交付文件校验值。
