# 原生可编辑组装接口

deck_spec.json 使用 UTF-8，相对路径相对于该文件；所有几何和 font_size 均为 96 DPI 像素。字号换算为 pt=px×0.75。先确定画布与文字矩形，再生成相应留白背景。

```json
{
  "title": "示例",
  "canvas": {"width": 1280, "height": 720},
  "font": "Microsoft YaHei",
  "style": {"name": "清爽专业风", "palette": ["#FFFFFF", "#163D3A"]},
  "backend": "built-in image tool",
  "sample_slide": 1,
  "assets": [
    {"id":"photo","path":"assets/photo.jpg","role":"原图","required":false,"unused_reason":"本页主题不涉及该内容"}
  ],
  "slides": [{
    "number":1,
    "scene_brief":"右侧简洁材料示意；左侧留白",
    "background":"origin_image/slide_01.png",
    "texts":[
      {"name":"标题","text":"可编辑标题","box":[60,40,1100,70],"font_size":44,"bold":true,"color":"#163D3A"},
      {"name":"正文","text":"第一行\n第二行","box":[60,160,550,160],"font_size":28}
    ],
    "images":[],
    "tables":[],
    "notes":"可直接使用的讲稿",
    "sources":["来源链接或归属说明"]
  }]
}
```

## 对象

- texts：name、text、box必填。可选 font、font_size、bold、italic、color、align(left/center/right)、vertical_align(top/middle/bottom)、margin（默认0）。换行使用真正的 JSON 换行转义，不使用字面量反斜线+n。对象名在每页唯一。
- images：asset_id引用assets中的id；或path直接指定。box必填。fit为contain（默认，保留整图比例）或cover（允许裁切）；crop为四个0–1比例[left,top,right,bottom]，表示先从原图四边裁去多少。不得裁掉关键证据。图片保留原始字节。
- tables：name、box、data（非空矩形二维字符串数组）；可选font_size、header_rows、column_widths（相对比例）、header_fill、header_color、cell_fill。数字字符串保持原值。native表格不是模型绘制的替代底图。
- assets：所有用户素材在此登记。unused_reason只用于未引用的可选素材；required=true未使用时拒绝最终组装。不要为凑数量使用无关素材。
- notes与sources：讲稿与来源写入对应页备注，source标注不自动进入可见页脚。
- 可选background_generation_method：记录样页后端、工具、模式、提示词和实际输出；prepare脚本会携带到任务，原始资产不经过模型重画。

背景文件必须存在并有真实的任务来源记录；测试夹具不作为生产图片来源。样页可单独导出；最终发布前用户应已确认样页。
