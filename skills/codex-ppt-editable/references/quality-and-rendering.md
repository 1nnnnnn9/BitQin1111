# 检查与预览

1. assemble_editable_ppt.py默认使用已记录的背景，并生成构建清单。validate_pptx.py验证原生文字、对象名称、页尺寸、备注和素材。
2. 先采用宿主实际提供的PPTX渲染/导出能力。不要要求安装或分发私有的Codex运行时。渲染得到的图片只用于预览，不替代可编辑PPTX。
3. 本机有LibreOffice和Poppler时，可运行 render_preview.py --pptx deck.pptx --output previews。没有这些工具时脚本明确报告缺失，不假称已视觉验证。Windows PowerPoint用户也可直接导出页面；使用宿主授权的应用操作工具或人工操作。
4. 模板必须查看代表性页面之后才能提取风格。PPTX/POTX不能仅靠文字/XML判断视觉。
5. 每页检查新增文字能单独选中，底图没有重复文字；缩放、替换素材不会破坏比例；表格单元格保留值；讲稿备注对应页。
6. 修改一个正文和一个图示标签，导出或重新渲染检查，不只验证字数。最终文字恢复后重新构建。
7. 布局自动检查覆盖越界与明显几何错误，不能证明排版完美。字体依赖使用者系统；不要擅自替换用户要求的品牌字体或打包无许可字体。
8. 保留PPTX、预览、底图与生成记录。原始图表在PPT媒体包中应与源文件字节一致，先裁切后计算展示比例。不要把截图里的坐标轴标注宣传成可单独编辑。

## 全稿与中后段检查

先看全稿缩略图，再逐页查看完整预览。结合 visual_plan 检查主图是否真正解释内容、箭头方向与节点是否正确、空间关系是否清楚、数据比例是否一致；关注中后段是否变成连续大表格。详细计算与附录允许表格，不设置固定图解比例。

style_fidelity 检查所选 codex-ppt 风格或模板的视觉语言：叠字后是否保持完整构图、清晰层次、足够的有效配图与适合内容的版式变化。留空文字不应把页面变成稀疏框图。若有用户提供的图片版参考，查看代表页进行视觉对照；只比较视觉表达，不混用其旧数据或正文。

新项目最终交付前执行：

```sh
python scripts/review_deck.py prepare --spec deck_spec.json --pptx deck.pptx --previews previews/slide-1.png previews/slide-2.png --output visual_review.json
```

--previews 必须列出所有页面，按规格顺序。脚本只从渲染预览制作缩略图，不绘制生产底图。查看输出的 montage 与每页预览后，在 visual_review.json 的 whole_deck 和各页 checks 中填写实际结论，并写 observation。无相关数据／来源时在观察中说明不适用及原因，再将该项记为通过；不能无观察批量批准。失败项先修复、重新渲染，再生成新检查记录。

```sh
python scripts/validate_pptx.py --spec deck_spec.json --pptx deck.pptx --final --visual-review visual_review.json --report final-check.json
```

最终检查验证全页对象、观察记录与文件哈希。更换 PPTX、规格或预览后旧记录失效。它不自动判定图像美观、流程正确或图像无字；执行代理须真实看图，不能用测试夹具或脚本预填通过。
