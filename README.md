< sd-webui-mprompt > 

用於sd-webui的關鍵字插件

當打開 mprompt 插件開關後, 接受特定符號操作(+,-,$,/)關鍵字, 

prompt為任意關鍵字

"+" 符號

prompt+ 等效於 {prompt}

prompt++ 等效於 (prompt)

prompt+++ 等效於 ((prompt))

prompt++++ 等效於 (((prompt)))


"-" 符號

prompt- 無作用

prompt-- 等效於 [prompt]

prompt--- 等效於 [[prompt]]

prompt---- 等效於 [[[prompt]]]


"$" 符號

prompt$ 為 {prompt} ~ ((((prompt)))) 隨機強度 (prompt+ ~ prompt+++++)

prompt$2 為 prompt ~ (prompt) 隨機強度 (prompt ~ prompt++)

prompt$23 為 (prompt) ~ ((prompt)) 隨機強度 (prompt++ ~ prompt+++)

prompt$$ 為 prompt隨機使用該關鍵字,(使用與不使用隨機出現)

prompt$$$35 為 隨機使用該關鍵字 ((prompt)) ~ ((((prompt)))) 隨機強度 (prompt+++ ~ prompt+++++)


"/" 符號

prompt1/prompt2/prompt3(可選) 等效於 prompt1 AND prompt2 AND prompt3

prompt1//prompt2//prompt3(可選)//... 為 prompt1, prompt2, prompt3... 隨機選擇一個 prompt



tags.key文件 為自定義關鍵詞字典, 格式為: 原文#譯文#類型

紫色#purple#颜色

-- 關鍵詞輸入 "紫色" 會自動轉換為 "purple"

-- 關鍵詞輸入 "颜色" (輸入關鍵字為類型時) 會隨機在顏色類別中使用一個顏色



"T:prompt" 中翻英
T:你好嗎 等效於 翻譯:你好嗎(英文) 使用有道翻譯接口


注意!!
當關鍵字間有空格最好替換成下畫線"_", 否則處理時會被當成兩組關鍵字分開處理
promptA_promptB 視為一組關鍵字, promptA promptB 視為兩組關鍵字
