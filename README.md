# 千人小镇 · Qianren City Atelier

基于 Three.js 的可交互模块化三维城市项目。本仓库保存城市运行源码、独立建筑模型源码、接入模块、构建脚本、验证脚本及 Blender MCP 渲染工具。

在线演示：https://qianren-town-atlas-1101.kelly-cooper-4963.chatgpt.site/

## 快速运行城市

安装 Node.js 22 或更新版本，在仓库根目录运行：

```sh
npm start
```

浏览器打开 http://127.0.0.1:5173 。城市运行所需 Three.js 和插件模块已随 `city-atlas/dist/vendor/` 保存，本地预览无需 CDN，也无需先安装 npm 依赖。

```sh
npm run check
```

该命令执行城市 JavaScript 语法检查与运行时模块引用检查。

## 源码结构

- `city-atlas/dist/main.js`：场景、相机、交互、光照、动画与模型装配。
- `city-atlas/dist/city.js`：地块、道路、原生住宅、交通与城市基础生成。
- `city-atlas/dist/*-model.js`：建筑和景观模型工厂。
- `city-atlas/dist/*-site.js`：地块位置、城市接入及模块登记。
- `city-atlas/dist/render-budget.js`：渲染负载管理。
- `city-atlas/dist/vendor/`：Three.js 及其插件，保留第三方许可文件。
- `city-atlas/tools/`：验证与模型交换脚本。
- 各独立模型目录的 `src/`、`build.cjs`、`tools/` 和 `*.mjs`：建模、查看器、离线构建、渲染与接入接口。
- `SOURCE_MANIFEST.json`：此次整理的源文件清单与 SHA-256。

模型目录包括医院、商业综合体、上海中心、云际中心、大学教学楼、体育馆、运动场、游乐园、河道、森林公园，以及林序、浅序、暖庭、棕屿里、澄序住宅和写字楼、总部项目。

目录中同时保留已接入模型与独立交付模型。当前城市实际加载的模块和地块以 `city-atlas/dist/main.js` 及相应 `*-site.js` 为准，各模型目录中的 README 可能包含历史接入记录。

## 重建独立 HTML

在根目录安装共享构建依赖后，运行相应项目的构建脚本，例如：

```sh
npm install
npm --prefix mixeduse-residential run build
```

多数项目会生成内嵌 Three.js、模型与材质资源的单文件 HTML。模型生成函数接受宿主的 THREE 实例，城市接入时复用宿主渲染器、相机和动画循环。

## 验证与 Blender

浏览器验证工具使用 Python、Playwright 与本机 Edge/Chromium。历史验证脚本可能需要先生成其使用的几何快照、基线或临时预览文件；这些运行产物不包含在本源码仓库。

Blender 工具需要本机 Blender、Python MCP SDK 和相应模型的 `outputs/scene.json`。可执行文件位置、Python 环境和浏览器路径请按自己的电脑调整。浏览器中的实时风动、角色或设施动画不等同于 GLB/Blender 中的静态模型快照。

## 此次上传范围

包含关键源码与可直接运行的城市网页。未包含 `node_modules`、Python 虚拟环境、缓存、Git 历史、登录凭据、`.env`、Sites 托管配置、渲染日志、截图、ZIP/TAR 交付包、生成的独立 HTML、GLB、Blender 工程及 4K/8K 成图。大文件可另行使用 GitHub Releases 或其他存储保存。

这份源码副本独立于原有城市部署仓库，不影响已有网站发布。
