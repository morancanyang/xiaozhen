from pathlib import Path
import zipfile,json,hashlib
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
verification=json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf-8'))
assert verification['checks'] and all(item['passed'] for item in verification['checks'])
blender=json.loads((ROOT/'outputs/blender-result.json').read_text(encoding='utf-8'))
assert blender['status']=='complete'
assert Image.open(ROOT/'outputs/blender-hero-8k.png').size==(4320,7680)
records=f'''上海中心 · 实际交付与检查记录
日期：2026-11-01（Asia/Shanghai）

模型：112×112米地块；104×104米实际广场；默认展示高度96米；参考原建筑632米；约120°扭转。
单文件 HTML 可断网双击打开，依赖与资源内嵌。没有马路。未修改千人小镇现有城市。

检查轮次：
1. outputs/01-rough.png：使用粗模配置检查外轮廓、楼冠、裙房和边界。
2. outputs/02-*.png：增加双层幕墙、分格、窗灯、空中绿化、入口、行人与细叶。
3. 窗灯过白改为暖黄；统一实时天空和地面色彩空间；羽化云体边缘；检查 Blender 摄影背景。
4. outputs/final-*.png：复查五个视角和手机布局；修复导航遮挡控制按钮与手机面板高度。
5. 同源接入测试：工厂接收宿主 THREE，model 属于宿主 Group，没有导入相机或灯光，asset 模式没有独立画布，dispose 实际移除模型。

浏览器：{verification['browser']}，Windows，Microsoft Edge 无头浏览器。
通过检查：{len(verification['checks'])} 项。具体项和测量记录见 outputs/verification.json。
测量结果只适用于本次设备、窗口与无头浏览器，不承诺其他设备的相同帧率。

Blender：5.2.2 LTS；通过本项目 stdio MCP 实际启动后台进程；Cycles/OPTIX/GPU；48采样与降噪。
五张离线渲染全部实际输出。仰拍主图4320×7680，为原生8K长边，不是后期放大。
工程中的相机动画为96帧关键帧，尚未输出成Blender视频。
outputs/上海中心-实时巡游.webm 是8秒真实浏览器画布录像，1280×960，目标30fps。

明确限制：
本模型为程序化建筑演绎，不是测绘BIM。实时玻璃是物理材质与环境反射近似，云体遮挡采用近似；人物、植物、家具与室内是简化构造。没有建造整座真实陆家嘴，远景仅为可选氛围。
单文件与Blender使用同一几何和变换，离线材质与光照经过单独重建，效果存在差异。
GLB为静态快照；HTML动态由接口时间轴驱动，不冒称已烘焙成GLB动画。
'''
(ROOT/'交付与检查记录.txt').write_text(records,encoding='utf-8')
files=[ROOT/name for name in ['上海中心.html','上海中心.glb','上海中心.blend','接入演示.html','shanghai-tower-module.mjs','town-integration.example.mjs','README.md','交付与检查记录.txt','package.json','build.cjs','THREE-LICENSE.txt']]
files+=list((ROOT/'src').glob('*'))
files+=list((ROOT/'tools').glob('*.py'))+list((ROOT/'tools').glob('*.mjs'))+list((ROOT/'tools').glob('*.txt'))
for pattern in ['01-rough.png','02-*.png','final-*.png','blender-*.png','browser-4k.png','integration-demo.png','*.webm','verification.json','blender-result.json','mcp-result.json','scene.json','review.json']:
    files+=list((ROOT/'outputs').glob(pattern))
files=sorted(set(files))
manifest={str(file.relative_to(ROOT)).replace('\\','/'):{'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()} for file in files}
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(ROOT/'manifest.json')
archive=ROOT.parent/'上海中心-完整交付.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for file in files:z.write(file,'shanghai-tower/'+str(file.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'files':len(files),'checks':len(verification['checks'])},ensure_ascii=True))
