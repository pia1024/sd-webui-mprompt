sd-webui-mprompt

用於sd-webui的關鍵字插件

打開 mprompt 插件後, 接受特定符號操作關鍵字,

prompt為任意關鍵字\n
prompt+ 等效於 {prompt}\n
prompt++ 等效於 (prompt)\n
prompt+++ 等效於 ((prompt))\n
prompt++++ 等效於 (((prompt)))\n

prompt- 無作用\n
prompt-- 等效於 [prompt]\n
prompt--- 等效於 [[prompt]]\n
prompt---- 等效於 [[[prompt]]]\n

prompt1/prompt2/prompt3(可選) 等效於 prompt1 AND prompt2 AND prompt3\n
prompt1//prompt2//prompt3(可選)//... 為 prompt1, prompt2, prompt3... 隨機選擇一個 prompt\n

tags.key文件 為自定義關鍵詞字典 格式為: 原文#譯文#類型\n
紫色#purple#颜色  -- 關鍵詞輸入 "紫色" 會自動轉換為 "purple"\n
                 -- 關鍵詞輸入 "颜色" (輸入關鍵字為類型時) 會隨機在顏色類別中使用一個顏色\n

中翻英 T:prompt\n
T:你好嗎 等效於 翻譯:你好嗎(英文) 使用有道翻譯接口\n




