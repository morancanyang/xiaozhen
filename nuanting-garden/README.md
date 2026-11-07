# 暖庭花园 · NUANTING GARDEN

为千人小镇单个112×112米正方形街坊制作的花园洋房模块。单文件 `暖庭花园.html` 已内嵌Three.js、控制器、模型代码和程序纹理，可以双击离线打开。

## 场地与建筑

模型使用米，Y轴向上，原点在场地地面中心，主入口朝+Z。原生底座X/Z边界为-56至56米。四栋暖黄色花园洋房以两行两列布置，建筑中心位于X/Z约±25米，基础体量约26×16米，分别为4、5、5、6层，含坡屋顶高度约16—23米。

建筑分别保留A、B、C、D稳定编号与独立节点，包含真石漆外墙、深色坡屋顶、瓦片层次、檐口、窗框窗台、飘窗、阳台栏杆、局部露台、入户门厅与屋面排水构件。组团包含中央花园、步道、草坪、树木灌木、休憩和儿童活动设施、内部环路、停车位及入口设施。

## 查看与动态

左键拖动旋转、右键拖动平移、滚轮缩放；触屏单指旋转、双指缩放和平移。查看器提供总览、俯视、入口、中央花园、屋顶和楼栋视角，可选择和观察独立建筑。

默认开启自然风动、16名居民和2辆低速车辆动态；界面提供统一暂停、速度、独立开关、三档质量以及午后、黄昏、夜景时段。窗内与庭院灯的亮度随时段变化，夜景使用实际场景灯光。车辆使用相同环路速度以保持间距，并在道闸前预留1.2秒等待。高画质含12,000片独立草叶。运动为程序化居住区展示动画，不是交通或人群物理仿真。

可保存当前画面PNG或导出静态GLB。GLB与Blender工程保存导出时的几何姿态，运行中的居民、车辆与风动由模型更新函数驱动，不能通过静态GLB自动恢复。

## 接入千人小镇

当前交付独立模型和接口，尚未指定或替换千人小镇的某个BLK地块。将 `model.mjs` 和 `integration-example.mjs` 放入宿主静态模块目录，使用宿主同一份THREE实例（本交付使用Three.js 0.180.0）。模型的程序纹理需要浏览器Canvas环境。

```js
import {mountGardenHousing,attachGardenLights} from './integration-example.mjs';

const garden=mountGardenHousing({
  THREE,scene,
  x:parcel.centerX,z:parcel.centerZ,
  groundY:0,blockSize:parcel.size,
  rotationY:0,quality:'medium'
});
const lights=attachGardenLights({THREE,scene,model:garden});

// 合入宿主已有的帧循环。
function updateCity(deltaSeconds){garden.update(deltaSeconds);}
garden.setActivity({wind:true,people:true,vehicles:true});
lights.setNight(1);

// 卸载：lights.dispose(); garden.dispose();
```

`mountGardenHousing` 不创建额外画布、相机或动画循环。模型工厂不添加灯光；`attachGardenLights` 为宿主可选的实际点光源适配器。改变模型位置、旋转或缩放后调用 `lights.sync()` 更新灯位。宿主负责天空、环境贴图、太阳、雾和后期效果。

统一缩放通过 `blockSize/112` 实现。清单内楼栋、入口、原生边界和灯位坐标使用原生112米模型坐标；适配器会将灯位转换到宿主世界坐标，并调整照射距离与强度。

工厂 `createGardenHousing({THREE,blockSize,quality,coarse})` 返回：`root`、`groups`、`buildings`、`manifest`、`update(deltaSeconds)`、`setQuality(level)`、`setTimeOfDay(value)`、`setDynamicsEnabled(enabled)`、`setActivity({wind,people,vehicles})`、`exportScene()`、`dispose()`，以及运行状态。

`manifest` 提供建筑编号与尺寸、入口、原生边界和灯位。`exportScene()` 输出当前可见模型的世界空间几何快照，按所有者区分楼栋与公共环境。

## 实际Blender渲染

本地MCP服务 `tools/blender_mcp.py` 导入 `outputs/garden-scene.json` 中的实际Three.js几何和材质，正确转换Y向上坐标为Blender坐标。`暖庭花园.blend` 保留A—D四栋独立建筑父级及对应原点，重复构件按所有者与材质合并以控制文件大小。纹理打包到blend。

`Garden housing model only` 集合包含可接入城市的模型；背景、相机、阳光与体积介质在独立 `Presentation - not part of city module` 集合。工程默认保存午后总览，夜景由脚本设置后恢复。

`outputs/blender-*.png` 对应总览、俯视、立面、入口、花园、屋顶和夜景，实际引擎与参数见 `outputs/blender-result.json`。渲染使用Cycles、可用GPU、降噪、64采样与1800×1200分辨率。

复现渲染：安装MCP Python SDK后，用对应Python运行 `tools/run_blender_mcp.py`。本机可使用 `../city-atlas/.venv/Scripts/python.exe`。服务打开独立可见Blender窗口，并保持MCP会话直到窗口关闭。Blender路径默认 `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`，其他位置可通过 `GARDEN_BLENDER_EXE` 环境变量指定。

## 源码与验证

`src/model.js` 为模型与动画源码，`src/app.js` 为查看器，`src/shell.html` 和 `src/style.css` 为页面。安装package.json依赖后执行 `npm run build`；单HTML交付物无需安装依赖。

36项网页检查报告在 `outputs/verification.json`，9项宿主适配器检查在 `outputs/integration-verification.json`，8项Blender保存工程检查在 `outputs/blender-verification.json`。源码、单HTML、静态GLB、可编辑blend、截图和实际渲染一起收录到 `暖庭花园-完整交付.zip`。

Three.js采用MIT协议，见 `THREE-LICENSE.txt`。
