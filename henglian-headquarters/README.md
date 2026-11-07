# 衡联总部 · HENGLIAN CAMPUS

当前为第二版精修，重点重做楼梯、入口台阶、树木和草坪。原版已保存在本机 backups/v1。

32株乔木使用渐细树干、分级枝条、独立折面叶片与叶脉纹理；合计约9.8万片树叶，配有27组灌木。草坪使用13.2万簇、79.2万片弯曲草叶，根部与叶尖具有颜色变化，风动与细节分级保留。精细模式总量约708万三角面。

主辅楼分别新增48跑、32跑连续疏散楼梯。踏步、踢面、楼板开洞、休息平台、防滑嵌条与平台栏杆均为几何；入口有三阶150毫米踏步和1:12坡道，并补齐底部支承。点击「楼梯」可独立查看，也可选择main-stairs / annex-stairs导出。

Three.js经过粗模、几何精修、近景复查；Blender增加石材倒角、叶片透光、草叶顶点色与近景景深。修改证据见 outputs/refinement-report.json。

双击 **衡联总部.html** 即可离线查看。Three.js、控制器、样式、模型和程序纹理全部内嵌，不依赖CDN、远程字体或后端。浏览器需要启用WebGL。

## 建筑尺寸

112 × 112米标准正方形地块，米制，Y向上，地面中心为原点，+Z为主入口。

| 构件 | 中心坐标 X/Z | 层数 | 主体占地 | 含屋顶设备高度 |
| --- | --- | --- | --- | --- |
| 主楼 main | -23 / -6 | 24 | 28 × 30米 | 100米 |
| 辅楼 annex | 24 / 3 | 16 | 24 × 26米 | 68米 |
| 连廊 bridge | 1.5 / 3 | 第10层 | 净跨21米，宽6米 | 结构底36.8米，顶41.2米 |

首层层高4.8米，标准层4米。连廊行走面为37.07米，与两楼第10层楼板面对应。连廊两端幕墙留洞，地板连续，核心筒避开人物路线。

模型包含分格幕墙、压条、立柱、背衬玻璃、开启扇细部、局部窗帘、独立楼板、核心筒、部分楼层办公桌椅和会议区；入口雨棚、感应门、门卫室、标识墙；屋顶设备间、机组、风机、管道、排水与防水接缝；连廊斜撑、端部节点、承座和螺栓。景观包含草坪、乔木、绿篱、长椅、排水格栅、自行车架和浅色透水服务环路。

## 查看器

- 左键拖动旋转、右键平移、滚轮缩放，触摸支持旋转和双指操作。
- 自由视角：WASD移动、Q/E升降、Shift加速；点击自由视角按钮后直接操作。
- 总览、正立面、俯视、仰视、入口、庭院、屋顶、连廊及主楼/辅楼视角；正交/透视切换。
- 可选择并隔离主楼、辅楼、连廊及分组构件；可导出整体或单组GLB，保存PNG截图。
- 晨光、白昼、黄昏、夜景、白底环境；全局暂停、速度调整，植物与云层、员工、飞鸟、风机与电梯指示、连廊通行分别控制。

22名轻量人物，其中8名走连廊；感应门随人员接近开合；树冠、草叶和窗帘轻微摆动；飞鸟移动振翅；屋顶风机旋转，电梯指示随时间移动。所有动态均由模型update驱动。

采用实例化与细节分级；medium减少微小五金和草叶，low进一步减少细部、枝叶与人物。查看器最多6个实际点光源。玻璃实时反射使用低分辨率天空探针，不重复渲染整套建筑；拖动降低像素倍率，停稳恢复。静态导出临时恢复完整细节，随后恢复查看状态。

## 千人小镇接入

本次是独立模块，尚未指定或替换BLK。使用同项目的Three.js r180验证通过。

```js
import {mountCorporateHeadquarters,attachHeadquartersLights} from './integration-example.mjs';
const campus=mountCorporateHeadquarters({
  THREE,scene,x:blockCenterX,z:blockCenterZ,groundY:0.1,
  blockSize:112,rotationY:0,quality:'medium'
});
// 在项目已有动画循环中调用，dt为秒。
campus.update(dt);
campus.setActivity({people:true,bridge:true,wind:true,birds:true,mechanical:true});
// 可选，真实灯光受预算限制。
const lighting=attachHeadquartersLights({THREE,scene,model:campus,budget:4});
lighting.setNight(1);lighting.sync();
// 卸载：lighting.dispose();campus.dispose();
```

直接工厂：`createCorporateHeadquarters({THREE,blockSize:112,quality:'high',coarse:false})`。

返回root、groups、buildings、main、annex、bridge、manifest、getManifest、update、setQuality、setTimeOfDay、setDynamicsEnabled、setActivity、exportScene、dispose。主辅楼独立原点位于各自地面中心，连廊坐标基于院区原点；主辅楼下分facade、roof、entrance、interior、stairs。

工厂不创建renderer、camera、灯光和RAF。宿主负责天空、相机、渲染器、动画循环和外围市政道路；模块内使用浅色石材与透水铺装。blockSize通过root.scale=blockSize/112统一缩放。manifest中的建筑、灯具、入口和nativeBounds维持原生米制坐标，footprint标记请求尺寸。世界位置通过root.localToWorld获取。exportScene快照矩阵为世界坐标。

## Blender与文件

通过项目本地FastMCP stdio服务启动真实Blender 5.2 GUI，将Three.js导出的实际几何转换为可编辑网格，坐标转换为(x,-z,y)，纹理打包到.blend。场景按主楼、辅楼、连廊、景观和构件材质合批；相机、灯光、背景单独收纳。

实际使用 **Cycles GPU / OptiX**，不是Octane。包含192采样的7680 × 4320主图、十二个日间视角、夜景与白底图；台阶、楼梯、树木、草坪近景为2560 × 1600、128采样。主辅楼及连廊有独立GLB，程序动画保留在HTML/model.mjs中；GLB和Blender为导出时静态姿态，未烘焙人物动画。局部办公室用于建筑可视化；植物为程序生成的实际枝叶几何，楼梯为连续实体踏步。

src/model.js与model.mjs是模型源码；src/ecology.js负责植物和地表，src/stairs.js负责楼梯与坡道。单独部署model.mjs时同时复制根目录的ecology.js、stairs.js；src/app.js是查看器；build.cjs打包离线HTML。安装package.json中的依赖后执行`node build.cjs`。当前电脑也可复用已有依赖。添加`?coarse`查看粗模。

tools/inspect_model.py保存粗模/精模截图、几何快照、GLB和尺寸检查；tools/verify.py检查离线交互、独立导出、200秒动态路径与实际帧率；tools/verify_integration.py验证项目Three.js版本兼容；tools/verify_blender.py复核独立Blender工程。

Blender MCP客户端：tools/run_blender_mcp.py。默认本机Blender路径可通过HEADQUARTERS_BLENDER_EXE覆盖，客户端需Python mcp SDK。渲染、性能与验证报告保存在outputs中；性能数字仅代表报告中的本机浏览器与视口。
