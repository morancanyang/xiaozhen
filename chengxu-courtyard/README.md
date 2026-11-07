# 澄序住区 · 四栋现代住宅院区

双击 **澄序住区.html** 即可离线查看。全部脚本、Three.js、控制器和程序纹理已内嵌，无 CDN、远程字体、后端或联网依赖。浏览器需要启用 WebGL。

## 模型尺寸与组成

- 标准正方形地块：112 × 112 米；米制，Y 向上，地面中心为原点，+Z 为主入口方向。
- A / B / C / D：20 / 22 / 22 / 24 层；最高点 65.6 / 71.8 / 71.8 / 78 米。
- 四栋塔楼中心为 X/Z ±26 米；建筑主体 22 × 20 米。首层层高 4.2 米，标准层 3.1 米。
- 蓝灰窗格、浅灰白墙体、少量米色墙板、凹进窗框、阳台、门厅雨棚、信报箱和门禁。
- 平屋顶、女儿墙、设备间、风机、机组百叶、管线、防水接缝与排水口。
- 深绿草坪、十字步道、浅色透水服务环路、树木、灌木、长椅、儿童角、廊架、自行车架和门卫室。
- **模块内没有沥青路面、道路车道线或城市外部道路。** 6 米宽服务环路使用浅色承重透水铺装；外围道路由千人小镇管理。

## 查看与导出

左键拖动旋转；右键拖动平移；滚轮缩放；双指缩放/平移。双击定位。自由视角下 WASD 平移、Q/E 升降、Shift 加速。

支持总览、立面、俯视、仰视、入口、庭院、屋顶及 A—D 单栋视角；正交/透视切换；单栋及构件隔离、GLB 导出、PNG 截图。晨光/白昼/黄昏/夜景/白底五种环境。居民、飞鸟、植物与云层、风机可分别开关；支持暂停和速度调整。

GLB 为当前静态姿态，保留独立建筑和构件层级。程序动画保留在 model.mjs / HTML 中。Blender 文件保留可编辑的构件网格与材质，按构件和材质合批，未烘焙程序动画。行人采用轻量人物，植被采用程序几何。

## 接入千人小镇

本次交付为独立模块，尚未替换现有 BLK。

```js
import {mountResidentialCourtyard,attachCourtyardLights} from './integration-example.mjs';
const housing=mountResidentialCourtyard({
  THREE,scene,x:blockCenterX,z:blockCenterZ,groundY:0.1,
  blockSize:112,rotationY:0,quality:'medium'
});
// 使用项目已有 RAF，每帧调用；dt 单位为秒。
housing.update(dt);
// 可选：限制真实点光源数量；纯模型工厂本身不添加灯光。
const fixtures=attachCourtyardLights({THREE,scene,model:housing,budget:4});
fixtures.setNight(1);fixtures.sync();
// 卸载时：fixtures.dispose(); housing.dispose();
```

原始工厂：`createResidentialCourtyard({THREE,blockSize:112,quality:'high',coarse:false})`。

返回 `root / groups / buildings / manifest / getManifest() / update(dt) / setQuality() / setTimeOfDay() / setDynamicsEnabled() / setActivity() / exportScene() / dispose()`。`buildings` 为 A—D Map；每栋下分 facade、roof、entrance。`setActivity({wind,people,birds,mechanical})` 独立控制动态。

工厂不创建 renderer、camera、灯光或 RAF。所有坐标和 manifest 建筑数据以原生 112 米模型为基准，`root.scale=blockSize/112`；footprint 标记请求尺寸，nativeBounds 保持原生尺寸。实际世界坐标通过 root.localToWorld() 获得。`exportScene()` 快照矩阵为世界坐标；适配器在整体旋转、缩放和平移后仍可同步灯具。

完整细节使用实例化；medium 隐藏微小五金并减少草叶；low 进一步减少细部与居民。夜景查看器最多启用 6 个点光源；天空反射仅更新低分辨率天空，不重复绘制院区；玻璃不触发昂贵的全场景透射过程。高精度 GLB 导出会临时恢复全部细节并恢复原状态。

## Blender 与渲染

通过项目本地 FastMCP stdio 服务调用本机 Blender 5.2。`tools/blender_import.py` 将 Three.js 实际几何快照转换为米制可编辑场景，坐标转换为 (x,-z,y)，材质纹理打包到 .blend 内。

使用 **Cycles + OptiX** 物理渲染；实际引擎和 GPU 状态记录在 outputs/blender-result.json。未使用 Octane。包含 7680 × 4320 主图和多角度 1800 × 1200 渲染。展示背景、相机和灯光单独收纳，不随 GLB/模型工厂移植。

tools/run_blender_mcp.py 为真实 MCP 客户端，tools/blender_mcp.py 提供可复用的启动、状态和打开文件工具。运行需 Python mcp SDK 与本机 Blender；默认路径可用环境变量 COURTYARD_BLENDER_EXE 覆盖。

## 源码与复查

src/model.js：程序模型；src/app.js：交互；src/style.css / shell.html：界面；build.cjs：打包离线 HTML。

`npm install` 后 `node build.cjs` 重建。构建也兼容此电脑已有的 Three.js/esbuild 依赖路径。`?coarse` 查看粗模。tools/inspect_model.py 保存粗模/精模视图、实际快照与 GLB；tools/verify.py 检查离线交互、200 秒动态路径、独立导出和拖动帧率；tools/verify_integration.py 使用千人小镇的 Three.js r180 复查接入。

渲染、截图和验证报告均在 outputs/。帧率为本机指定浏览器与视口的实测值，不能视为其他设备的保证。
