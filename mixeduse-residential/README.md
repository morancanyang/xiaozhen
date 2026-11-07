# 棕屿里 · 住宅与沿街商业

双击 `棕屿里.html` 离线查看，无需服务器。所有运行代码、Three.js、控制器、GLB 导出器、程序材质与纹理内嵌于同一个 HTML。

112 × 112 米地块，一栋三单元板式高层，22 层住宅加首层商业，含设备机房总高约 75.91 米；六间独立商铺。浅米白外墙、浅棕真石漆、竖向飘窗、封闭阳台、门厅、实体坡道、屋顶设备及少量绿化完整建模。

默认纯白背景和正交相机，可切换透视。支持左键旋转、右键平移、滚轮/触屏缩放，立面、商铺与屋顶视角，昼夜、风力、速度、暂停、商铺门演示，以及三档画质和完整 GLB 导出。`?coarse=1` 为体量阶段。

## 接入千人小镇

`mixeduse-module.mjs` 导出 createMixedUseResidential({THREE,footprint=112,quality='high',seed=1105})。单位米、Y 向上、地块中心为原点、连接面为 Y=0，正面 +Z。模型支持 root、metadata、buildings、update(delta,state)、setQuality、setTimeOfDay、getBounds、exportScene、exportGLB({GLTFExporter})、dispose。

宿主提供同一个 THREE 并复用既有渲染器、环境反射、相机和动画循环。delta 已由宿主施加速度倍率时，不要重复乘倍率。state 接受 paused、wind、windStrength、nightFactor、doors。示例见 integration-example.mjs。dispose 仅释放本模块资源。

本次交付独立模型，未替换城市地块。GLB 和 Blender 为静态几何/灯光，程序风动、渐变灯光和门动画在 HTML 与模块内运行。

## 源码与真实渲染

src 为源码；安装 package.json 中依赖后运行 npm run build 重建单文件 HTML。tools/verify_model.py 实测离线、几何、法线、交互、动态、移动端与导出。

tools/run_blender_mcp.py 通过真实 MCP stdio 会话打开独立的本机 Blender 窗口，导入 outputs/scene.json 的同源几何、UV、实例颜色和内嵌纹理，使用 Cycles 实际渲染。总览为 7680×4320 正交图，另有正立面、商铺、门厅与黄昏图。实际设备、采样及尺寸见 outputs/blender-result.json。完成后 MCP 会话保留至用户关闭 Blender 窗口。


验证结果：29 项浏览器检查通过，记录在 outputs/verification.json。实际 8K 总览已检查为 7680×4320、正交相机、纯白背景像素 RGB(255,255,255)。完整交付包由 tools/package_delivery.py 校验渲染结果、模型对象数量、文件校验值及 ZIP 完整性后生成。
