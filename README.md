sd-webui-mprompt

用於sd-webui的關鍵字插件

打開 mprompt 插件後, 接受特定符號操作關鍵字,

prompt為任意關鍵字

prompt+ 等效於 {prompt}

prompt++ 等效於 (prompt)

prompt+++ 等效於 ((prompt))

prompt++++ 等效於 (((prompt)))

prompt- 無作用

prompt-- 等效於 [prompt]

prompt--- 等效於 [[prompt]]

prompt---- 等效於 [[[prompt]]]

prompt1/prompt2/prompt3(可選) 等效於 prompt1 AND prompt2 AND prompt3

prompt1//prompt2//prompt3(可選)//... 為 prompt1, prompt2, prompt3... 隨機選擇一個 prompt

tags.key文件 為自定義關鍵詞字典, 格式為: 原文#譯文#類型

紫色#purple#颜色

-- 關鍵詞輸入 "紫色" 會自動轉換為 "purple"

-- 關鍵詞輸入 "颜色" (輸入關鍵字為類型時) 會隨機在顏色類別中使用一個顏色

中翻英 T:prompt
T:你好嗎 等效於 翻譯:你好嗎(英文) 使用有道翻譯接口




