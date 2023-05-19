# -*- coding: utf-8 -*-
# cython: language_level=3
# 作者: pia1024

import os
from random import random, shuffle, choice, choices, sample, randint
from IPython.display import clear_output, display
from PIL import Image, PngImagePlugin

DType,CnDict,EnDict,CnKeys = [],{},{},[]
taggChinese = True #是否開啟中文關鍵字轉換

print('tagsGenerator version: 230507')

'''
23/03/08
Z: 新增雙斜槓處理隨機參數, 例如:"參數A//參數B", 將隨機輸出"參數A"或"參數B"
23/03/10
Z: 雙斜槓與單斜槓混合使用處理
23/03/11
findTag: 關鍵詞搜索現在支持英文搜索
23/03/13
translate: 修改返回值為 (譯文,是否為新的詞), 重新寫過整個邏輯
23/03/16
mixPromptFromFiles: 修改關鍵詞分割條件 遇到類似"1girl"時, 不分割
23/03/19
mixPromptFromFiles: 修復關鍵詞長度增加的問題, 對重複關鍵字進行合併讓特性更平均
23/03/22
mixPromptFromFiles: 添加randomMode選擇, 0為平均模式, 1為隨機模式
                    修復平均模式小問題
promptOutput: 添加排除替換關鍵字參數 
23/04/30
openPoseImageResize: 調整cnet引導圖的大小以適應圖片比例
23/05/07
readPromptFromImage: 更新webUI的參數讀取邏輯, 已解決讀取不完全的問題
replaceTags: 新增替換關鍵詞函數
'''


web2PaddleDict={'Steps:':'num_inference_steps',
 'Sampler:':'sampler',
 'CFG scale:':'guidance_scale',
 'Strength:':'strength',
 'Seed:':'seed',
 'Size:':'size',
 'Model hash:':'model_hash <NoUse>',
 'Model:':'model <NoUse>',
 'Hires upscaler:':'superres_model_name <NoUse>',
 'init_image:':'init_image <NoUse>'}

Paddle2PaddleDict={'parameters:':'prompt',
 'Negative prompt:':'negative_prompt',
 'Steps:':'num_inference_steps',
 'Sampler:':'sampler',
 'CFG scale:':'guidance_scale',
 'Strength:':'strength',
 'Seed:':'seed',
 'width:':'width',
 'height:':'height',              
 'max_embeddings_multiples:':'max_embeddings_multiples',
 'model_name:':'model_name <NoUse>',
 'superres_model_name:':'superres_model_name <NoUse>',
 'init_image:':'init_image <NoUse>',
 }

Dream2PaddleDict={
    's ':'num_inference_steps',
    'A ':'sampler',
    'C ':'guidance_scale',
    'S ':'seed',
    'W ':'width',
    'H ':'height',
}




def UI_img():
    import ipywidgets as widgets
    from ui.utils import imageBox, infoBox, initImageBox
    imageBox_ = widgets.HBox([imageBox,initImageBox])
    display(imageBox_,infoBox)

def UI_info():
    from ui.utils import imageBox, agenTagBox, agenNpTagBox, infoBox
    display(agenTagBox,agenNpTagBox)

def num2str(num, digit=4):
    '''
    功能說明: 將數字轉成文字,若位數不足則補上0,預設輸出為4位
    num: 任意數字
    digit: 補零的位數
    '''
    s = str(num)
    while len(s) < digit:
        s = '0'+ s
    return s


def readFile(file, mode='r', encoding="utf-8"):
    '''
    功能說明: 讀取文件到變量
    '''
    with open(file, mode, encoding=encoding) as f:
        value = f.read()
    return value

def readFileBit(file,mode='rb'):
    '''
    功能說明: 讀取文件到變量
    '''
    with open(file, mode) as f:
        value = f.read()
    return value

def writeFile(file, value, mode='a', encoding="utf-8"):
    '''
    功能說明: 寫入變量到文件
    '''
    with open(file, mode, encoding=encoding) as f:
        f.write(value)
    return 1

def readFile2List(file, mode='r', encoding="utf-8"): 
    '''
    功能說明: 讀取文件到列表 
    需求模組: readfile
    '''
    value = readFile(file, mode, encoding=encoding)
    value = value.splitlines()
    return value

def getFileLink(dir="",start=1,end=1,debug=0,filter="",filterMode=1):
    '''
    功能說明: 獲取當前的子文件路徑到列表[0] 子文件名到列表[1]
    dir: 將獲取的路徑文件夾,支持相對路徑與絕對路徑
    start: 起始搜索的文件夾層數, 1表示根目錄開始, 0表示搜索全部
    end: 結束搜索的文件夾層數, 如果層數很多可以設置大一點,如果不想獲取子目錄就跟start設相同值
    filter: 過濾文件,如果只想獲取特殊格式文件可以使用,例如 filter='.jpg,.png' ,表示只獲取包含.jpg與.png字串的文件
    filterMode: 過濾模式, 1|關鍵字全符合 2|關鍵字部分符合
    return: 返回兩個列表,列表[0]為絕對路徑, 列表[1]為相對路徑
    By Bruce Yen
    '''
    
    #os.sep #路徑分隔符

    if dir=="" or dir == None: dir=os.getcwd()
    if end < start: end = start
    if start==0: start, end = 1, 200
    filelinks,filenames = [],[]
    dirlevel = len(dir.split(os.sep)) #獲取當前目錄層級
    for root, dirs, files in os.walk(dir,topdown=True):
        for name in files:
            filelevel = len(os.path.join(root, name).split(os.sep)) #獲取子目錄層級
            if filelevel>=dirlevel+start and filelevel<=dirlevel+end: #比較篩選目錄層級
                if debug==1: print(name,"\t:",os.path.join(root, name))
                filenames.append(name)
                filelinks.append(os.path.join(root, name))
                
    if not filter == "":
        newfilelinks, newfilenames = [], []
        if ',' in filter: # 如果發現','就切割成表
            filters = filter.split(',')
        elif ';' in filter: # 如果發現';'就切割成表
            filters = filter.split(';')
        else:
            filters = [filter]
            
        
        newfilelinks,newfilenames = [],[]
        
        if filterMode==1: #mode1 關鍵字全符合時放入
            for filter in filters: #遍歷所有關鍵字
                for filelink in filelinks: #遍歷所有文件路徑
                    if filter.lower() in filelink.lower(): #如果文件路徑含有關鍵字
                        newfilelinks.append(filelink)
                filelinks = newfilelinks
                newfilelinks = []
                        
                for filename in filenames: #遍歷所有文件路徑
                    if filter.lower() in filename.lower(): #如果文件路徑含有關鍵字
                        newfilenames.append(filename)
                filenames = newfilenames
                newfilenames = []
                        
            
        
        if filterMode==3: #mode3 關鍵字全符合時放入??
            for filter in filters:
                if debug == 1: print(filter)
                for filelink in filelinks:
                    if filter.lower() in filelink.lower(): #如果文件名包含有過濾詞
                        newfilelinks.append(filelink)

                for filename in filenames:
                    if filter.lower() in filename.lower():
                        newfilenames.append(filename)
                        newfilenames
            filelinks,filenames = newfilelinks,newfilenames
                
        if filterMode==2: #mode2 關鍵字部分符合時放入
            for filter in filters:
                for filelink in filelinks:
                    if filter.lower() in filelink.lower():
                        newfilelinks.append(filelink)
                for filename in filenames:
                    if filter.lower() in filename.lower():
                        newfilenames.append(filename)
            filelinks, filenames = newfilelinks, newfilenames
        
    return filelinks,filenames

def readPromptFileFromCivitai(file): #讀取civitai.com複製的txt描述詞
    '''
    讀取civitai.com複製的txt描述詞
    '''
    text = readFile(file)
    prompt, negative_prompt, info = '','',''
    np = 0
    for i,x in enumerate(text.split('\n')):
        if 'Negative prompt:' in x:
            np = 1
            negative_prompt = x.replace('Negative prompt: ','')
        if 'Size:' in x:
            np = 2
            
        if np==0:
            prompt += x
        elif np==1:
            negative_prompt += x
        elif np==2:
            info += x
            
    promptDict = {'prompt':prompt,'negative_prompt':negative_prompt,'info':info,'promptFile':os.path.basename(file)}
        
    return promptDict

def readPromptFile2Dict(file):
    '''
    讀取Paddle的txt描述詞
    '''
    promptDict = {'prompt':'','negative_prompt':'','promptFile':os.path.basename(file)}
    data = readFile2List(file)
    for line in data:
        if 'Prompt: ' in line: 
            promptDict.update({'prompt':line.replace('Prompt: ','')})
        if 'prompt: ' in line:
            if not 'num_images_per_prompt: ' in line and not 'Negative prompt: ' in line and not 'negative_prompt: ' in line: 
                promptDict.update({'prompt':line.replace('prompt: ','')})
        if 'Negative prompt: ' in line: 
            promptDict.update({'negative_prompt':line.replace('Negative prompt: ','')})
        if 'negative_prompt: ' in line: 
            promptDict.update({'negative_prompt':line.replace('negative_prompt: ','')})
        if 'Steps: ' in line: 
            promptDict.update({'steps':line.replace('Steps: ','')})
        if 'num_inference_steps: ' in line: 
            promptDict.update({'steps':line.replace('num_inference_steps: ','')})
        if 'Sampler: ' in line: 
            promptDict.update({'sampler':line.replace('Sampler: ','')})
        if 'sampler: ' in line: 
            promptDict.update({'sampler':line.replace('sampler: ','')})
        if 'CFG scale: ' in line: 
            promptDict.update({'CFG':line.replace('CFG scale: ','')})
        if 'guidance_scale: ' in line: 
            promptDict.update({'CFG':line.replace('guidance_scale: ','')})
        if 'Seed: ' in line: 
            promptDict.update({'seed':line.replace('Seed: ','')})
        if 'seed: ' in line: 
            promptDict.update({'seed':line.replace('seed: ','')})
        if 'width: ' in line: 
            promptDict.update({'width':line.replace('width: ','')})
        if 'height: ' in line: 
            promptDict.update({'height':line.replace('height: ','')})
        if 'max_embeddings_multiples: ' in line: 
            promptDict.update({'max_embeddings_multiples':line.replace('max_embeddings_multiples: ','')})
        if 'model_name: ' in line: 
            promptDict.update({'model_name':line.replace('model_name: ','')})
    return promptDict

def readPromptFromImage(imgPath,debug=None):
    '''
    從圖片讀取描述詞
    '''
    if debug is None: debug=False
    
    promptDict = {'prompt':'','negative_prompt':'','promptFile':os.path.basename(imgPath)}

    image = Image.open(imgPath)
    info = image.info
    if debug: print(f'{imgPath}')
    if debug>1: print(info)
    
    def errorLoad(errorOutput=0):
        # print(info)
        
        if errorOutput==0:
            prompt = ''
            negative_prompt = ''
            print(f'< 不支援的格式 > 避免運行中止, 輸出空白參數值 "{imgPath}"')
            
        elif errorOutput==1:
            prompt = 'cat'
            negative_prompt = ''
            print(f'< 不支援的格式 > 避免運行中止, 輸出"cat"作為參數值 "{imgPath}"')

        elif errorOutput==2:
            prompt = 'A huge red cat with little people and little houses standing next to it, yawning with its mouth wide open. In the background was a town of elves and stars everywhere'
            negative_prompt = 'test'
            print(f'< 不支援的格式 > 避免運行中止, 輸出測試用的參數值 "{imgPath}"')

        promptDict.update({'prompt':prompt,'negative_prompt':negative_prompt})
        return promptDict
    
    if 'Software' in info:
        if debug: print(f'< 飛槳格式圖片 >' )
        infoLi = info['parameters'].split('\n') 
        for i,x in enumerate(infoLi):
#             print(f'<{i}> {x}')

            if i==0:
                promptDict['prompt'] = x

            for key in Paddle2PaddleDict:
                if key in x:
                    promptDict[Paddle2PaddleDict[key]] = x.replace(key,'').strip()

    elif 'exif' in info:
        if debug: print('< 未知格式圖片 (exif) >')
        if b'UNICODE' in info['exif']:
            bText = info['exif'].split(b'UNICODE')[1].replace(b'\x00',b'')
            text = bText.decode('utf-8')
            textLi = text.split('\n')
            for i,x in enumerate(textLi):
                if i==0:
                    promptDict['prompt'] = x

                elif i==1:
                    promptDict['negative_prompt'] = x.replace('Negative prompt:','').strip()

                elif i>=2:
                    xli = [ p.strip() for p in x.split(',') if p.strip()!='' ]
                    for key in web2PaddleDict:
                        for p in xli:
                            if key in p:
                                promptDict[web2PaddleDict[key]] = p.replace(key,'').strip()
            if 'size' in promptDict:
                    promptDict['width'], promptDict['height'] = promptDict['size'].split('x')[:2]
                    del promptDict['size']
        else:
            errorLoad()
        
    elif 'Dream' in info and 'sd-metadata' in info:
        if debug: print('< 未知格式圖片 (Dream) >')

        import ast
        Dream = ast.literal_eval(f"{info}")
        if debug: print('Dream:',type(Dream),Dream.keys())
        if '[' in Dream['Dream'] and ']' in Dream['Dream']:
            promptDict['prompt'] = Dream['Dream'].split('"')[1].replace(']','').split('[')[0].strip()
            promptDict['negative_prompt'] = Dream['Dream'].split('"')[1].replace(']','').split('[')[1].strip()
        else:
            promptDict['prompt'] = Dream['Dream'].split('"')[1].strip()
            
        ss = [ x.strip() for x in Dream['Dream'].split('"')[2].strip().split('-') if x!='']

        for x in ss:
            for key in Dream2PaddleDict:
                if key in x:
                    promptDict.update({Dream2PaddleDict[key]:x.replace(key,'')})
            
    elif not 'Software' in info and not 'exif' in info and 'parameters' in info:
        if debug: print('< webUI格式圖片 >')
        infoLi = info['parameters'].split('\n') 
        isNP,isSet = False, False
        for i,x in enumerate(infoLi):
            # print(f'<{i}> {x}\n')
            
            if 'Negative prompt' in x:
                isNP = True
            
            if 'Steps' in x:
                isSet = True
                
            if not isNP:
                promptDict['prompt'] += x.replace('\n','').strip()
            
            if isNP and not isSet:
                promptDict['negative_prompt'] += x.replace('Negative prompt:','').replace('\n','').strip()
                
            if isSet:
                xli = [ p.strip() for p in x.split(',') if p.strip()!='' ]
                for key in web2PaddleDict:
                    for p in xli:
                        if key in p:
                            promptDict[web2PaddleDict[key]] = p.replace(key,'').strip()
                            
        if 'size' in promptDict:
                promptDict['width'], promptDict['height'] = promptDict['size'].split('x')[:2]
                del promptDict['size']
                
    else:
        errorLoad()
        
    return promptDict
    

# def readPromptFromImage(imgPath,debug=None): #(部分圖片參數載入失敗, 先停用)
#     from ui.png_info_helper import deserialize_from_image, deserialize_from_filename
#     promptDict = deserialize_from_image(imgPath)[0]
#     promptDict.update({'promptFile':os.path.basename(imgPath)}) #寫入參數文件訊息

#     if debug is None: debug=False
    
#     if debug>1:
#         for key in ['prompt','negative_prompt']:
#             if key in promptDict: 
#                 print(f"{key}: {promptDict[key]}")
#     if debug:
#         for key in ['num_inference_steps','sampler',
#                     'guidance_scale','seed','width','height',
#                     'superres_model_name','superres_model_name <NoUse>',
#                     'model_name','model','model_hash','init_image',
#                     'model_name <NoUse>','model <NoUse>',
#                     'model_hash <NoUse>','init_image <NoUse>']:
#             if key in promptDict: 
#                 print(f"{key}: {promptDict[key]}")
#     return promptDict

def randomLoadAgnModTagsKey():
    '''
    隨機讀取mod.key的描述詞
    '''
    dateLi = readFile2List('mod.key')
    shuffle(dateLi) #打亂順序
    data = choice(dateLi)
    while data=='' or data[0]=='#':
        data = choice(dateLi)
    if '#' in data:
        if len(data.split('#'))==4:
            title,prompt,np_prompt,keyType = data.split('#')

        elif len(data.split('#'))==3:
            title,prompt,keyType = data.split('#')
            np_prompt = '' #讀取預設的negative_prompt

        print('ModTagsTitle:',title)
        return(prompt,np_prompt)
    else:
        prompt = data
        np_prompt = ''
        return prompt, np_prompt

def LoadPromptFile(file,debug=0):
    '''
    讀取描述詞文件(.txt,.jpg,.png)
    file: 描述詞文件來源路徑
    '''
    pfile = file
    fileName,fileExt = os.path.splitext(pfile)
    if fileExt.lower()=='.txt':
        text = readFile(pfile).split('\n')[0]
        if 'prompt:' in text.lower():
            if debug>0: print('飛槳參數文件:',os.path.basename(pfile))
            promptDict = readPromptFile2Dict(pfile)
            prompt, np_prompt = promptDict['prompt'], promptDict['negative_prompt']
        else:
            if debug>0: print('Civitai參數文件:',os.path.basename(pfile))
            promptDict = readPromptFileFromCivitai(pfile)
            prompt, np_prompt = promptDict['prompt'], promptDict['negative_prompt']
            
    elif fileExt.lower()=='.png' or fileExt.lower()=='.jpg' or fileExt.lower()=='.jpeg':
        if debug>0: print('含參數圖片:',os.path.basename(pfile))
        promptDict = readPromptFromImage(pfile)
        prompt, np_prompt = promptDict['prompt'], promptDict['negative_prompt']
        
    else:
        raise IOError(f'尚不支援讀取該格式: {fileExt[1:]}')
        
    return prompt, np_prompt, promptDict

def randomLoadPromptFile(dirPath='txt'):
    '''
    隨機讀取描述詞文件(.txt,.jpg,.png)
    dirPath: 來源路徑(描述詞文件夾), 預設為"txt"
    '''
    import os
    filesLi = getFileLink(dirPath,1,1,filter='txt,png,jpg', filterMode=2)[0]
    shuffle(filesLi) #打亂順序
    pfile = choice(filesLi)
    fileName,fileExt = os.path.splitext(pfile)
    prompt, np_prompt, promptDict = LoadPromptFile(pfile)
        
    return prompt, np_prompt, promptDict

def randomLoadCNetImagePath(imagePath='cnet_openpose_img'):
    import os
    filesLi = getFileLink(imagePath,1,1,filter='png')[0]
    shuffle(filesLi) #打亂順序
    cNetImagePath = choice(filesLi)
    return cNetImagePath
        
def sequentLoadPromptFile(dirPath='txt'): #順序讀取tag文件
    '''
    順序讀取描述詞文件(.txt,.jpg,.png)
    dirPath: 來源路徑(描述詞文件夾), 預設為"txt"
    '''
    import os
    glob = globals()

    def readPromptFile2List(): #重新讀取順序清單
        glob['promptFileList'] = getFileLink(dirPath,1,1,filter='txt,png,jpg', filterMode=2)[0]
        glob['promptFileList'] = list(set(glob['promptFileList']))
        glob['promptFileList'].sort()
        print('載入清單完成')


    try:
        print('順序清單內文件數量:',len(glob['promptFileList']))
    except KeyError:
        readPromptFile2List() #重新讀取順序清單

    k = 0
    while 1: #處理不存在文件
        k+=1
        if len(glob['promptFileList'])==0: #順序清單空了的時候
            readPromptFile2List() #重新讀取順序清單

        pfile = glob['promptFileList'].pop(0)
        if os.path.exists(pfile): #檢查文件是否存在
            break

        if k>1000:
            raise IndexError('順序清單內無有效路徑')

    prompt, np_prompt, promptDict = LoadPromptFile(pfile)
        
    return prompt, np_prompt, promptDict
    
def mixPromptFromFiles(promptDirPath='txt',n=3,randomMode=0,debug=0): #讀取並混合參數
    '''
    讀取並混合描述詞(.txt,.jpg,.png)
    promptDirPath: 來源路徑(描述詞文件夾), 預設為"txt"
    n: 用來混合的描述詞文件數量
    randomMode: 0:打亂後平均使用關鍵詞(捨棄的關鍵詞少, 風格變異小) 1:打亂後隨機使用關鍵詞(捨棄的關鍵詞變多, 風格變異更大)
    '''
    def splitTags(text):
        textLi = [x.strip() for x in text.split(',') if x != '']
        return textLi
    
    def splitTagsLen(text):
        textLi = [x.strip() for x in text.split(',') if x != '']
        textLen = len(textLi)
        return textLen
    
    #分析關鍵詞結構
    def analyseTags(promptLi): #分析關鍵詞結構
        xliType = []
        mainPrompt = [] #主關鍵詞
        subPrompt_front = [] #主關鍵詞前面的關鍵詞(比重大)
        subPrompt_behind = [] #主關鍵詞後的關鍵詞(比重小)
        q=1 #用來區分當前是在主關鍵詞之前還是之後
        typeli = [0,1,2] 
        for i,x in enumerate(splitTags(prompt)):
            for key in ['girl','woman','man','boy']:
                if key in x and not '1'+x in x and not '2'+x in x and not '3'+x in x and not '4'+x in x:
                    xliType+=[typeli[0]]
                    if typeli[0]==0: mainPrompt += [x]
                    if typeli[0]==2: subPrompt_behind += [x]
                    typeli[0] = 2
                    q=2
                    break
                else:
                    xliType+=[typeli[q]]
                    if q==1: subPrompt_front += [x]
                    if q==2: subPrompt_behind += [x]
                    break
                    
        if not 0 in xliType:
            xliType = [ 2 if x==1 else x for x in xliType]
            subPrompt_behind = subPrompt_front.copy()
            subPrompt_front = []
            
        #去重並計算與主關鍵詞的差集
        subPrompt_front = list(set(subPrompt_front).difference(set(mainPrompt)))
        subPrompt_behind = list(set(subPrompt_behind).difference(set(mainPrompt)))
                    
        if debug>1: print('關鍵詞總數:',len(xliType))
        if debug>1: print('關鍵詞類型:',xliType)
        if debug>1: print('主關鍵詞:',len(mainPrompt),mainPrompt)
        if debug>1: print('子關鍵詞(前):',len(subPrompt_front),subPrompt_front)
        if debug>1: print('子關鍵詞(後):',len(subPrompt_behind),subPrompt_behind)
        return xliType,mainPrompt,subPrompt_front,subPrompt_behind
    
    from random import choice, shuffle
    n=n #組合數量, 設置用多少組關鍵詞組合
    filesLi = []
    tempDict = {Paddle2PaddleDict[x]:[] for x in Paddle2PaddleDict}
    tempDict.update({'promptFile':'mixMode'})
    # tempDict #空白字典用來暫存參數
    files = getFileLink(promptDirPath,filter='.png,.jpg,.txt',filterMode=2)[0]
    if len(files)==0: raise IOError(f'請檢查參數文件是否存在!! 路徑: {promptDirPath}')
    elif len(files)<n: n = len(files) #如果參數文件
    while len(filesLi)<n:
        f = choice(files)
        if not f in filesLi: filesLi += [f]
    if debug>1: print(f'使用的圖片清單: {filesLi}') #使用的圖片清單

    for x in range(n):
        info = LoadPromptFile(filesLi[x])[2] #讀取文件返回參數字典
        if debug>1: print(f'圖片關鍵詞數量: < {splitTagsLen(info["prompt"])} > ,{filesLi[x]}')
        for key in Paddle2PaddleDict: #參數字典key Paddle2PaddleDict[key]
            if Paddle2PaddleDict[key] in info: #合併所有圖的'prompt'跟'negative_prompt'參數
                if Paddle2PaddleDict[key] in ['prompt','negative_prompt']:
    #                 print(Paddle2PaddleDict[key],':', info[Paddle2PaddleDict[key]])
                    tempDict[Paddle2PaddleDict[key]] += [info[Paddle2PaddleDict[key]]]
                elif x==0: #用第一張圖的其他參數
    #                 print(Paddle2PaddleDict[key],':', info[Paddle2PaddleDict[key]])
                    tempDict[Paddle2PaddleDict[key]] = info[Paddle2PaddleDict[key]]


    #隨機選擇一張圖的逆關鍵字
    tempDict['negative_prompt'] = choice(tempDict['negative_prompt'])
    if debug>0: tempDict['negative_prompt']

    #處理正關鍵詞
    prompt = choice(tempDict['prompt']) #正關鍵詞
    promptLen = splitTagsLen(prompt) #正關鍵詞數量
    if debug>0: print(f'主關鍵詞數量: < {promptLen} >, {prompt}\n')

    xliType,mainPrompt,subPrompt_front,subPrompt_behind = analyseTags(splitTags(prompt))
    main_xliType = xliType.copy()
    if debug>0: print(f'主關鍵詞類型: {main_xliType}\n')

    
    mainPrompt_, subPrompt_front_, subPrompt_behind_ = [],[],[] 
    for prompt in tempDict['prompt']:
        xliType,mainPrompt,subPrompt_front,subPrompt_behind = analyseTags(splitTags(prompt))
        mainPrompt_+=mainPrompt
        subPrompt_front_+=subPrompt_front
        subPrompt_behind_+=subPrompt_behind
        
    mainPrompt, subPrompt_front, subPrompt_behind = mainPrompt_.copy(), subPrompt_front_.copy(), subPrompt_behind_.copy()
    del mainPrompt_, subPrompt_front_, subPrompt_behind_
        
    if debug>0: print('mainPrompt:',len(mainPrompt),mainPrompt,'\n')
    if debug>0: print('subPrompt_front:',len(subPrompt_front),subPrompt_front,'\n')
    if debug>0: print('subPrompt_behind:',len(subPrompt_behind),subPrompt_behind,'\n')
        
    #複製一份
    mainPrompt_ = mainPrompt.copy()
    subPrompt_front_ = subPrompt_front.copy()
    subPrompt_behind_ = subPrompt_behind.copy()

    prompt = []
    for x in main_xliType:
        if x==0:
            shuffle(mainPrompt_) #打亂次序
            if randomMode==0:
                try:
                    prompt += [mainPrompt_.pop()]
                except:
                    mainPrompt_ = mainPrompt.copy()
                    shuffle(mainPrompt_)
                    prompt += [mainPrompt_.pop()]
            elif randomMode==1:
                prompt += [choice(mainPrompt_)]
                
        if x==1: 
            shuffle(subPrompt_front_) #打亂次序
            if randomMode==0:
                try:
                    prompt += [subPrompt_front_.pop()]
                except:
                    subPrompt_front_ = subPrompt_front.copy()
                    shuffle(subPrompt_front_)
                    prompt += [subPrompt_front_.pop()]
            elif randomMode==1:
                prompt += [choice(subPrompt_front_)]
                    
        if x==2:
            shuffle(subPrompt_behind_) #打亂次序
            if randomMode==0:        
                try:
                    prompt += [subPrompt_behind_.pop()]
                except:
                    subPrompt_behind_ = subPrompt_behind.copy()
                    shuffle(subPrompt_behind_)
                    prompt += [subPrompt_behind_.pop()]
            elif randomMode==1:
                prompt += [choice(subPrompt_behind_)]
                
    tempDict['prompt'] = ', '.join(prompt)
    promptDict = {x:tempDict[x] for x in tempDict if tempDict[x]!=[]} #清理空白參數
    return promptDict

def PIL2bytes(im):
    '''
    PIL转二进制
    :param im: PIL图像，PIL.Image
    :return: bytes图像
    '''
    from io import BytesIO
    bytesIO = BytesIO()
    try:
        im.save(bytesIO, format='JPEG')
    except:
        im.save(bytesIO, format='PNG')
    return bytesIO.getvalue()  # 转二进制

# def displayImage(img, resize_ratio=1.0):
#     from PIL import Image
#     from tagsGenerator import PIL2bytes
#     image = img
#     size_w, size_h = image.size #獲取圖像大小
#     image_re = image.resize((int(size_w*resize_ratio), int(size_h*resize_ratio)),Image.BILINEAR)
#     imageBox.value = PIL2bytes(image_re)

def loadTagsText(tagsText):
    tagsLi = tagsText.split('\n')
#     tagsLi = tagsLi[::-1] #倒序讓靠上的數據不被下方數據覆蓋
    tagsDict = {}
    for tags in tagsLi:
        tag = tags.split('#')
        tag = [x.strip() for x in tag] #去除數據前後無意義空格
        if tag[0]!='':
            if len(tag)==2:
                tagsDict.update({tag[0]+'#未定義':tag[1]})
            elif len(tag)==3:
                if tag[2]!='':
                    tagsDict.update({tag[0]+'#'+tag[2]:tag[1]})
                else:
                    tagsDict.update({tag[0]+'#未定義':tag[1]})
    return tagsDict

def loadTagsFile(tagsFile):
    tagsText = readFile(tagsFile)
    tagsDict = loadTagsText(tagsText)
    return tagsDict

def toTypeDict(TagsDict):
#     global DType,CnDict,EnDict
    CnDict={}
    DType_= [type_ for key_,type_ in [key.split('#') for key in list(TagsDict.keys())]]
    DType=list(set(DType_))
    DType.sort(key=DType_.index)
    return(DType)

def toCnDict(TagsDict):
#     global DType,CnDict,EnDict
    CnDict={}
    keys = [x[0] for x in list(TagsDict.items())]
    vals = [x[1] for x in list(TagsDict.items())]   

    for i,key in enumerate(keys):
        CnDict.update({key:vals[i]})
    return(CnDict)

def toEnDict(TagsDict):
#     global DType,CnDict,EnDict
    EnDict={}
    keys = [x[1] for x in list(TagsDict.items())]
    vals = [x[0] for x in list(TagsDict.items())]

    for i,key in enumerate(keys):
        if not key in EnDict: EnDict.update({key:vals[i]})
    return(EnDict)
    
def toCnKey(TagsDict):
#     debug=1
    # 獲取所有中文名稱的列表用於快速檢驗否有存在於字典中
    cnKeys_ = CnDict.keys()
    cnKeys_ = [key.split('#')[0] for key in cnKeys_]
    cnKeys=list(set(cnKeys_))
    cnKeys.sort(key=cnKeys_.index)
    return cnKeys

def updateTagsDict(): #更新關鍵字字典
    '''更新關鍵字字典 DType,CnDict,EnDict'''
    global DType,CnDict,EnDict,CnKeys
    DType = toTypeDict(TagsDict)
    CnDict = toCnDict(TagsDict)
    EnDict=toEnDict(TagsDict)
    CnKeys = toCnKey(TagsDict)
    print('字典類別:',len(DType))
    print('中轉英字典:',len(CnDict))
    print('英轉中字典:',len(EnDict))
    # print(DType)
    # print(CnDict.keys())
    # print(EnDict.keys())


###################### 讀取關鍵字字典 #############################
if os.path.exists('tags.key'):
    #讀取關鍵字字典
    TagsDict=loadTagsFile('tags.key')
    updateTagsDict()
elif os.path.exists('extensions/sd-webui-mprompt/tags.key'):
    #讀取關鍵字字典
    TagsDict=loadTagsFile('extensions/sd-webui-mprompt/tags.key')
    updateTagsDict()
else:
    print('未找到關鍵字字典 tags.key')
    TagsDict=loadTagsText("空白#None#NoType")
    updateTagsDict()
###################################################################


def findTag(tagText,tagType=None,exclude=None,debug=0): 
    '''
    查找關鍵字
    tagText: 要查找的關鍵字
    tagType: 篩選類別
    exclude: 排除字符
    '''
    tagLi = []
    for tag in tagText.split(','): #搜索中文
        for key in TagsDict:
            key_,type_ = key.split('#')
            if tagType: keyCopy = tag in key_ and type_==tagType 
            else: keyCopy = tag in key_
            if keyCopy:
                tagLi.append([key,TagsDict[key]])
                if not exclude:
                    if debug: print('[添加]',key,TagsDict[key])
                        
    for tag in tagText.split(','): #搜索英文
        for key in TagsDict:
            if tag in TagsDict[key]:
                key_,type_ = key.split('#')
                if tagType: 
                    keyCopy = tag in TagsDict[key] and type_==tagType 
                else: 
                    keyCopy = tag in TagsDict[key]
                if keyCopy:
                    tagLi.append([key,TagsDict[key]])
                    if not exclude:
                        if debug: print('[添加]',key,TagsDict[key])
            
    if exclude:
        tagLi, tagLi_ = [], tagLi
        for key,value in tagLi_:
            keyCopy = 1 #是否複製開關
            for exkey in exclude.split(','):
                if exkey in key: 
                    keyCopy = 0 #如果字符中含有排除字符就不複製
                    if debug>1: print('[排除]',key,value)
            if keyCopy:
                if debug: print('[添加]',key,TagsDict[key])
                tagLi.append([key,value]) #複製
    return(tagLi)
    
def getTag(tag,debug=None):
    if '#' in tag:
        tag,type = tag.split('#')
        keys = findTag(tag,type)
        for key,value in keys:
            if debug: print(key)
            if key.split('#')[0]==tag:
                key_,type_ = key.split('#')
                return key, key_, type_
    else:
        keys = findTag(tag)
        for key,value in keys:
            if debug: print(key)
            if key.split('#')[0]==tag:
                key_,type_ = key.split('#')
                return key, key_, type_
                
def checkKey(key):
    if key in CnKeys:
        return 1
    else:
        return 0

def checkType(type):
    if type in DType:
        return 1
    else:
        return 0
    
def checkKeyAndType(text,debug=1):
    key = checkKey(text)
    type = checkType(text)
    if debug: 
        string = ''
        if key: string+= '存在Key中, '
        else: string+= '不存在Key中, '
        if type: string+= '存在Type中'
        else: string+= '不存在Type中'
        print(f'"{text}" {string}')
    if key or type:
        return 1
    else:
        return 0
        
def tagC2E(text,debug=0): #關鍵字中轉英
    # debug=1
    
    #[Type]
    if checkType(text):
        if debug: print(f'{text} 類型為[Type]')
        ckey,eKey = choice(findTag('',text))
        if debug: print(f'{ckey}:\t{eKey}')
        return (ckey,eKey)
        
    #[Key]
    if checkKey(text):
        if debug: print(f'{text} 類型為[Key]')
        if debug: print(f'{getTag(text)[0]}:\t{CnDict[getTag(text)[0]]}')
        return getTag(text)[0],CnDict[getTag(text)[0]]

    #[元素][Key]
    elements = findTag('','元素')+findTag('','顏色')
    for element in elements:
        element = element[0].split('#')[0] #獲取所有元素列表
        if text[:len(element)] == element:
            element = text[:len(element)] #關鍵詞包含元素
            key = text[len(element):] #去掉元素後的關鍵詞
            if checkKey(key):
                if debug: print(f'{text} 類型為[元素][Key]')
                if debug: print(f'{getTag(element)[1]}{getTag(key)[1]}:\t{CnDict[getTag(element)[0]]} {CnDict[getTag(key)[0]]} ({getTag(element)[2]},{getTag(key)[2]})')
                return getTag(element)[1]+getTag(key)[1],f'{CnDict[getTag(element)[0]]}_{CnDict[getTag(key)[0]]}'
        
    #[元素][Type]
    elements = findTag('','元素')+findTag('','顏色')
    for element in elements:
        element = element[0].split('#')[0] #獲取所有元素列表
        if text[:len(element)] == element:
            element = text[:len(element)] #關鍵詞包含元素
            key = text[len(element):] #去掉元素後的關鍵詞
            if checkType(key):
                if debug: print(f'{text} 類型為[元素][Type]')
                ckey,eKey = choice(findTag('',key))
                return getTag(element)[1]+getTag(ckey)[1],f'{CnDict[getTag(element)[0]]}_{CnDict[getTag(ckey)[0]]}'
    
    #[元素Type][Type]
    if '元素' in text: 
        type_ = '元素'
        elements = findTag('','元素')
    if '顏色' in text: 
        type_ = '顏色'
        elements = findTag('','顏色')
    element = choice(elements)[0] #獲取隨機元素
    key =  text.replace('元素','').replace('顏色','') #記下去掉元素後的關鍵詞
    if checkType(key):
        if debug: print(f'{text} 類型為[{type_}Type][Type]')
        ckey,eKey = choice(findTag('',key))
        return getTag(element)[1]+getTag(ckey)[1],f'{CnDict[getTag(element)[0]]}_{CnDict[getTag(ckey)[0]]}'

    #[元素Type][Key]
    if checkKey(key):
        if debug: print(f'{text} 類型為[[Type][Key]')
        newEKey = '' 
        for k in CnDict[getTag(key)[0]].split(','):
            k = k.strip()
            newEKey += f'{CnDict[getTag(element)[0]]}_{k}, '
        newEKey = newEKey[:-2]
        return getTag(element)[1]+getTag(key)[1],newEKey

    else:
        if debug: print(f'{text} 不存在僅返回輸入值')
        return text,text #只返回翻譯結果
        
def rmComma(text): #移除逗號
    if text!='':
        if text.strip()[-1]==',':
            return text.strip()[:-1]
        else:
            return text.strip()
    else:
        return ''

def clearUpTags(text): #最終輸出前清理空白關鍵字
    tagLi = text.split(',')
    tagLi = [x.strip() for x in tagLi if x.strip().replace('+','').replace('-','').replace('/','').replace('(','').replace(')','').replace('{','').replace('}','').replace('[','').replace(']','')!='']
    prompt = ', '.join(tagLi)
    return prompt
    
def C(input): #返回不帶類型的中文關鍵字 "水手服#套裝" > "水手服"
    return input.split('#')[0]

def K(key,debug=0): #解析關鍵字權重與配置
    # debug=1
    txt = key.strip()
    wight=1 #權重
    LV=0
    LV_Neg=0
    notInput=False
    
    #處理'+'符號
    LV = txt.count('+')
    txt = txt.replace('+','')
    text = txt
    
    #處理'$'符號
    if txt.count(':0')==1 and txt.count(':0.')==0: #兼容前一版本語法
        txt = txt.replace(':0','$$')
    
    if '$$' in txt:
        txt = txt.replace('$$','',1)
        if randint(1,10000)%2:
            notInput = True
    
    if '$' in txt:
        for x in range(0,10):
            for y in range(0,10):
                if f"${x}{y}" in txt:
                    LV = randint(x,y)
                    txt = txt.replace(f'${x}{y}','')
                    break
            if f"${x}" in txt:
                LV = randint(0,x)
                txt = txt.replace(f'${x}','')
                break
        if '$' in txt:
            LV = randint(0,5)
            txt = txt.replace(f'$','')

    #處理'()'符號
    while 1:
        if '(' in txt and not ')' in txt:
            txt = txt.replace('(','',1)
        elif ')' in txt and not '(' in txt:
            txt = txt.replace(')','',1)
        if ')' in txt and '(' in txt:
            break
        if not ')' in txt and not '(' in txt:
            break
    
    if ')' in txt and '(' in txt:
        f = txt.count('(')
        s = txt.count(')')
        minFs = min(f,s)
        LV += minFs+1
        txt = txt.replace('(','',minFs).replace(')','',minFs)
            
            
    #處理'-'符號, '-'當只使用一個時不處理, 僅當成連接符號
    if '--' in txt:
        LV_Neg = txt.count('-')
        txt = txt.replace('-','')        
    
    #處理'T:'符號
    if 'T:' in txt: #翻譯
        text = txt = txt.replace('T:','').strip()
        txt = translate(txt)[0]
        print(f'翻譯參數: {text} > {txt}')
        text= "翻譯: "+text
        # 不使用 tagC2E(txt) 來獲取 text
        text = C(text)+'+'*LV+'-'*LV_Neg
        return key,text,txt,wight,LV,LV_Neg,notInput

    #處理':'符號
    if txt.count(':')==1:
        txt,wight = txt.split(':')
    
    #處理';'符號 (忽略該tag)
    if txt.count(';')==1:
        txt = ''
        notInput = True

    text, txt = tagC2E(txt)
    text = C(text)+'+'*LV+'-'*LV_Neg
    return key,text,txt,wight,LV,LV_Neg,notInput


def T(input):
    a,b = input
    #print(b)
    output = [x.strip() for x in b.split(',') if x.strip()!=""]
    return(output)

def X(input):
    tagSet = []
    tagText, tagValue = [],[]
    for x in input:
        tagSet += tagC2E(x)

    for i,x in enumerate(tagSet):
        if not i%2:
            tagText += [x.split('#')[0]]
        else:
            tagValue += [x]

    tagText, tagValue
    return ','.join(tagText),','.join(tagValue)

def oneKeyConvert(key,debug=0):
    # debug=1
    #單關鍵字的輸出跟括號處理
    if debug: print(f'oneKeyConvert輸入: {key}')
    key,text,txt,wight,LV,LV_Neg,notInput = K(key)
    if debug: print(f'key: {key} \ntext: {text} \ntag: {txt}\nwight:{wight}, LV:{LV}, LV_Neg:{LV_Neg}, notInput:{notInput}')
    outPrompt = ''
    if notInput:
        text, outPrompt = '', ''
    else:
        #將參數轉換回WebUI參數語法
        if wight!=1: text = f'{text}:{wight}'
        for txt in txt.split(','):
            LVli = [["",""],["{","}"],["("*(LV-1),")"*(LV-1)],["["*(LV_Neg-1),"]"*(LV_Neg-1)]]    
            if LV<2 and LV_Neg==0:
                outPrompt += f'{LVli[LV][0]}{txt}'
                if wight!=1: outPrompt += f':{wight}'
                outPrompt += f'{LVli[LV][1]}, '
            elif LV==0 and LV_Neg>=2:
                outPrompt += f'{LVli[3][0]}{txt}'
                if wight!=1: outPrompt += f':{wight}'
                outPrompt += f'{LVli[3][1]}, '
            elif LV>=2 and LV_Neg==0:
                outPrompt += f'{LVli[2][0]}{txt}'
                if wight!=1: outPrompt += f':{wight}'
                outPrompt += f'{LVli[2][1]}, '
    if debug: print('==================== 輸出 ========================')
    return rmComma(text), rmComma(outPrompt)
    
def F(Tag_split, debug=None): #處理":"參數
    if 'lora:' in Tag_split:
        text, outPrompt = Tag_split, Tag_split
        print(f'Lora參數: {Tag_split}')
        return text, outPrompt

    else:
        txtSplit = Tag_split.split(':')
        try:
            int(txtSplit[2][1])
            I=2
        except:
            I=3

        try:
            if I==3: 
                txt1,wight,txt2 = txtSplit
            elif I==2: 
                txt1,txt2,wight = txtSplit
            text1, outPrompt1 = oneKeyConvert(txt1)
            text2, outPrompt2 = oneKeyConvert(txt2)
            text = rmComma(txt1)+':'+rmComma(txt2)+':'+wight
            outPrompt = rmComma(outPrompt1)+':'+rmComma(outPrompt2)+':'+wight
            if debug: print(f'處理分號:{text, outPrompt}')
            return text, outPrompt
        except:
            print(f'異常參數: {txtSplit}, 忽略轉換該參數!!')
            text, outPrompt = Tag_split, Tag_split
            return text, outPrompt


def Z(Tag_split, debug=0): #處理"/"與"//"參數 單斜槓轉換為 "參數 AND 參數" 雙斜槓轉換為 "隨機參數"
    import random
    text, outPrompt = '', ''
    textLi, outPromptLi = [],[]
    
    def doubleSlash(Tag_split): #處理雙斜槓
        newTags=''
        txtSplitFirst = Tag_split.split('//')
        txtSplitSecond = random.choice(txtSplitFirst)
        newTags = txtSplitSecond
        # if debug: print(f'處理雙斜槓: {txtSplit}, 輸出:{txtSplit2}')
        return newTags
        
    def singleSlash(Tag_split): #處理單斜槓
        newTags=''
        txtSplit = Tag_split.split('/')
        for tag in txtSplit:
            newTags+= tag+','
        # if debug: print(f'處理單斜槓:{Tags, txtSplit, newTags}')
        return newTags
    
    txtSplit = doubleSlash(Tag_split)
    txtSplit = singleSlash(txtSplit)
    for tag in txtSplit.split(','):
        txt,tag = oneKeyConvert(tag)
        if tag!="": 
            outPromptLi += [tag]
            textLi += [txt]
    outPrompt = ' AND '.join(outPromptLi)+', '
    text = '/'.join(textLi)+', '
            
    return text, outPrompt
    
def promptOutput(input, replaceList=None, debug=None):
#     debug=1
    '''
    replaceList: 傳入字典(替換跟排除)或列表(排除)格式, 替換關鍵詞或排除關鍵詞
    '''
    
    promptText = ''
    promptOutput = ''
    tagsLi=[]
    tags = input
    if replaceList==None: replaceList={}
    for oneTag in tags.split(','): #輸入關鍵詞分割為單個關鍵詞
        tagsLi += [oneTag.strip()]
    if debug: print('##Tags:',tagsLi,'\n')
    
    ssLi=[]
    for tag in tagsLi: #單個關鍵詞分割為列表
        temp=[]
        for ss in tag.split(' '):
            if not ss in replaceList:
                temp += [ss]
            else:
                if type(replaceList) is dict:
                    temp += [replaceList[ss]]
                    if debug: print(f'替換關鍵詞: "{ss}" 為 "{replaceList[ss]}"')
                elif type(replaceList) is list:
                    if debug: print(f'排除關鍵詞: "{ss}"')
        if temp!=[]: 
            ssLi+=[temp]
    if debug: print('##Tag_split:',ssLi,'\n')
    
    ssLi_Text=[]
    ssLi_Tags=[]
    for Tag in ssLi:
        if len(Tag)==1:
            if '/' in Tag[0]: #< 第一層 >
#                 if debug: print('斜槓處理: ',Tag[0])
                text, outPrompt = Z(Tag[0],debug)
                ssLi_Text += [text]
                ssLi_Tags += [outPrompt]
            
            elif ':' in Tag[0] and Tag[0].count(':')>1:
#                 if debug: print('雙分號處理: ',Tag[0])
                text, outPrompt = F(Tag[0],debug)
                ssLi_Text += [text]
                ssLi_Tags += [outPrompt]
                
            else:
#                 if debug: print('普通處理: ',Tag[0])
                text, outPrompt = oneKeyConvert(Tag[0])
                ssLi_Text += [text]
                ssLi_Tags += [outPrompt]
                
        else:
            text,outPrompt = [],[]
            for Tag_split in Tag:  #< 第二層 >
                if '/' in Tag_split:
#                     if debug: print('斜槓處理: ',Tag_split)
                    text_, outPrompt_ = Z(Tag_split,debug)
                    text += [rmComma(text_)]
                    outPrompt += [rmComma(outPrompt_)]
                
                elif ':' in Tag_split and Tag_split.count(':')>1:
#                     if debug: print('雙分號處理: ',Tag_split)
                    text_, outPrompt_ = F(Tag_split,debug)
                    text += [rmComma(text_)]
                    outPrompt += [rmComma(outPrompt_)]
                    
                else:
#                     if debug: print('普通處理: ',Tag_split)
                    text_, outPrompt_ = oneKeyConvert(Tag_split)
                    text += [rmComma(text_)]
                    outPrompt += [rmComma(outPrompt_)]
            ssLi_Text += [text]
            ssLi_Tags += [outPrompt]

    if debug: print('ssLi_Text',ssLi_Text,'\n')
    if debug: print('ssLi_Tags',ssLi_Tags,'\n')
    
    for x in ssLi_Text:
        if type(x) is list:
            promptText += ' '.join(x)+', '
        else:
            promptText += x+', '
    
    for x in ssLi_Tags:
        if type(x) is list:
            promptOutput += '_'.join(x)+', '
        else:
            promptOutput += x+', '
            
    promptText = clearUpTags(rmComma(promptText))
    promptOutput = clearUpTags(rmComma(promptOutput))

    return promptText, promptOutput


######################################## 舊版函數未修正適應新函數 ###########################################
def customDictGroup(string,dtType=''): #自訂義字典類
    dictTemp={}
    string = arrange(string)
    strLi = string.split(',')
    strLen = len(strLi)
    for x in strLi:
        dictTemp.update({x:[x,dtType]})
    #print('輸入關鍵數目:',len(dictTemp))
    return dictTemp

def addCustomDictGroup(string,dtType=''): #添加自訂義字典類至字典中
    '''添加自訂義字典類至字典中'''
    TagsDict.update(customDictGroup(string,dtType=dtType))
    toTypeDict(TagsDict) #只更新字典類型,不更新原始字典,不然使用中文後原始關鍵字會被覆蓋

def customDict(key,velue,dtType=''): #自訂義字典
    dictTemp={}
    key = arrange(key)
    velue = arrange(velue)
    dictTemp.update({velue:[key,dtType]})
    #print('輸入關鍵數目:',len(dictTemp))
    return dictTemp

def addCustomDict(key,velue,dtType=''): #添加自訂義字典至關鍵字中
    '''添加自訂義關鍵詞至關鍵字字典'''
    TagsDict.update(customDict(key,velue,dtType=dtType))
    updateTagsDict()
    
def filterDict(fstrs='',dTypes=''): #過濾關鍵字字典
    '''過濾關鍵字字典'''
    listTemp=[]
    if dTypes=='':
        for key,value in TagsDict.items():
            for fstr in fstrs.split(','):
                for dtype in dTypes.split(','):
                    if fstr in value[0]:
#                         print(value,value[1])
                        listTemp += [value[0]]
    else:
        for key,value in TagsDict.items():
            for fstr in fstrs.split(','):
                for dtype in dTypes.split(','):
                    if fstr in value[0] and value[1]==dtype :
#                         print(value,value[1])
                        listTemp += [value[0]]
    string = ','.join(listTemp)+','
    if string==',': string=''
#     print(string,end='')
    return string
    
def showAllType():
    '''列出所有類別'''
    print(DType)


def showAllTags():
    '''列出所有類別與其關鍵詞'''
    print(f'')
    for Type  in DType:
        print(f'< {Type} >')
        print(allPrompt(TagsDict,onlykey=Type))
        print(f'')

def dirZip(dirPathsList=None,zipName=None,debug=0):
    '''
    壓縮文件夾至壓縮包
    '''
    import os,zipfile
    sep = os.sep #獲取系統分隔符
    if type(dirPathsList)==str: dirPathsList=[dirPathsList]
    if zipName==None: zipName = dirPathsList[0].split(sep)[-1]+'.zip'
#     print(zipName,dirPathsList)
    count,count_=0,0
    path = os.path.split(dirPathsList[0])[0]
    with zipfile.ZipFile(path+sep+zipName,'w',zipfile.ZIP_DEFLATED) as myzip:
        for root in dirPathsList:
            print(f'壓縮文件夾 "{root}" 至 "{zipName}"')
            rootDirName = root.split(sep)[-1]+sep
            for dirpath, dirnames, filenames in os.walk(root):
                fpath = dirpath.replace(root,'') #这一句很重要，不replace的话，就从根目录开始复制
                fpath = fpath and fpath + sep or ''#这句话理解我也点郁闷，实现当前文件夹以及包含的所有文件的压缩
                for i,filename in enumerate(filenames):
#                     print(os.path.join(dirpath, filename),rootDirName+fpath+filename)
                    myzip.write(os.path.join(dirpath, filename),rootDirName+fpath+filename)
                    count_=i+1
                count+=count_
    print(f'  -- 總共添加{count}個文件至壓縮檔 "{path+sep+zipName}"')
    if debug: myzip.printdir()

# def readConfigFile(file="config.py"):
#     import ast
#     info = readFile(file)
#     setDict = ast.literal_eval(info)
#     return(setDict)

def readConfigFile(file="config.py",debug=0):
    import ast,random
    info = readFile(file)
    spInfo = info.split('\n')
    spInfo = [x.split('#')[0].strip() for x in spInfo if x.split('#')[0].strip()!='']
    spInfo = spInfo[1:-1]
    setDict = {}
    for x in spInfo:
        dictTemp = ast.literal_eval(f'{{{x}}}')
        dictKeyTemp = list(dictTemp.keys())[0]
        if dictKeyTemp in setDict:
            for key in ['prompt','add_prompt','prompt_add','negative_prompt','add_negative_prompt','negative_prompt_add']:
                if dictKeyTemp==key:
                    if type(dictTemp[dictKeyTemp]) is list:
                        dictTemp[dictKeyTemp] = random.choice(dictTemp[dictKeyTemp])
                        if debug: print('[隨機獲取]',end='')
                    if debug: print('[合併]',dictKeyTemp,':',dictTemp[dictKeyTemp])
                    new_setDictKey = setDict[dictKeyTemp]+', '+dictTemp[dictKeyTemp]
                    setDict[dictKeyTemp] = new_setDictKey
                    break
            else:
                if debug: print('[替換]',dictKeyTemp,':',dictTemp[dictKeyTemp])
                setDict.update(dictTemp)

        else:
            for key in ['prompt','add_prompt','prompt_add','negative_prompt','add_negative_prompt','negative_prompt_add']:
                if dictKeyTemp==key:
                    if type(dictTemp[dictKeyTemp]) is list:
                        dictTemp[dictKeyTemp] = random.choice(dictTemp[dictKeyTemp])
                        if debug: print('[隨機獲取]',end='')

            if debug: print('[新增]',dictKeyTemp,':',dictTemp[dictKeyTemp])
            setDict.update(dictTemp)
    return(setDict)
    
def getLoraModel(path,min_=None,max_=None,mode='random'):
    # 獲取路徑下lora模型的路徑,並隨機返回
    # mode: 'random' 返回符合條件的隨機一組模型路徑
    #       'list' 返回整個符合條件的模型路徑列表
    import os,random
    if os.path.exists(os.path.join(path,'paddle_lora_weights.pdparams')): #如果路徑目錄下找到paddle_lora_weights.pdparams就直接使用
        return path
    elif os.path.isfile(path) and os.path.exists(path):  #如果路徑本身就是模型就直接使用
        path = path.replace(f'{os.sep}paddle_lora_weights.pdparams','')
        return path
        
    if not min_ is None and not max_ is None and not min_<=max_: #最大值最小值異常處理
        minStep, maxStep = max_, min_
    else:
        minStep, maxStep = min_, max_
        
    dirList,stepList = [],[]
    for root,dirs,files in os.walk(os.path.abspath(path)):
        for dir in dirs:
    #         print(os.path.join(root,dir)) #获取目录的路径
            if os.path.exists(os.path.join(root,dir,'paddle_lora_weights.pdparams')):
                try:
                    int(dir.replace('checkpoint-',''))
                    dirList += [(os.path.join(root,dir),int(dir.replace('checkpoint-','')))]
                    stepList += [int(dir.replace('checkpoint-',''))]
                except ValueError:
                    pass
                
    if minStep is None: minStep = min(stepList)
    if maxStep is None: maxStep = max(stepList)

    minLi,maxLi = [],[]
    for i,dirPath in enumerate(dirList):
        if dirPath[1]>=minStep:
            minLi += [dirList[i]]
        if dirPath[1]<=maxStep:
            maxLi += [dirList[i]]

    newLi = list(set(minLi).intersection(maxLi)) #求併集
    newLi = [os.path.relpath(x[0]) for x in newLi] #轉相對路徑
    if len(newLi)==0:
        raise OSError(f'未找到符合條件的模型路徑, 請檢查模型路徑 {path}')
    if mode=="random":
        random.shuffle(newLi)
        return random.choice(newLi)
    elif mode=="list":
        newLi.sort()
        return newLi
    else:
        return random.choice(newLi)

def getLoraModel_(path,min_=None,max_=None,mode=None):
    # 獲取路徑下lora模型的路徑,並隨機返回
    # mode: 'random' 返回符合條件的隨機一組模型路徑
    #       'list' 返回整個符合條件的模型路徑列表
    import os,random
    
    fileList = []
    for root,dirs,files in os.walk(os.path.abspath(path)):
        for file_ in files:
            fPath = os.path.join(root,file_)
            if os.path.splitext(fPath)[1]=='.safetensors' or os.path.splitext(fPath)[1]=='.pdparams':
                if os.path.exists(fPath):
                    fileList += [fPath]
    # print(fileList)
    return random.choice(fileList)

def translate(word, Type="AUTO", dictFile='translate.txt', debug=None): #有道翻譯API
    if debug is None: debug=0
    
    def getDictKey(value,d): #用字典值找鍵
        return [k for k, v in d.items() if v == value][0]
    
    def checkAsciiAll(string): #檢查是否為全單字節字符, 含中文即輸出為False
        import re
        p = re.compile('[^\x00-\xff]')
        for x in string:
            if ''.join(p.findall(x))!='':
                return False
        return True
    
    def readTranslatDict(dictFile='translate.txt'): #從文件中讀取字典
        import os
        translatDict = {}
        translatLi = []
        if os.path.exists(dictFile):
            translatLi = readFile2List(dictFile)
        for text in translatLi:
            try:
                x,y = text.split('\t\t')
                translatDict[x.strip()]=y.strip()
            except:
                pass
        return translatDict
        
    def youdaoAPI(word,Type="AUTO"): # 有道词典 api
        import requests
        import json

        url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule&smartresult=ugc&sessionFrom=null'
        # 传输的参数，其中 i 为需要翻译的内容

        key = {
            'type': f"{Type}",
            'i': word,
            "doctype": "json",
            "version": "2.1",
            "keyfrom": "fanyi.web",
            "ue": "UTF-8",
            "action": "FY_BY_CLICKBUTTON",
            "typoResult": "true"
        }

        # key 这个字典为发送给有道词典服务器的内容
        response = requests.post(url, data=key)
        # 判断服务器是否相应成功
        if response.status_code == 200:
            # 然后相应的结果,轉換成字串翻譯
            list_trans = response.text
            result = json.loads(list_trans)
            result_ = result['translateResult'][0][0]['tgt']
            Type = result['type']
        else:
            print("有道词典调用失败")
            # 相应失败就返回空
            return None

        return result_, Type
    
    #讀取翻譯紀錄,節省已查過的字串請求次數
    translatDict = readTranslatDict(dictFile) #從文件中讀取字典

    #配置 youdaoAPI
    typeDict = {
        "AUTO":"AUTO", #自動
        "E2C":"EN2ZH_CN", #英翻中
        "EN2ZH_CN":"EN2ZH_CN", #英翻中
        "C2E":"ZH_CN2EN", #中翻英
        "ZH_CN2EN":"ZH_CN2EN", #中翻英
    }

    Type = typeDict[Type.upper()]
    if Type=="AUTO":
        if checkAsciiAll(word):
            Type="EN2ZH_CN"
        else:
            Type="ZH_CN2EN"
    
    try:
        newKey = False
        if Type=="EN2ZH_CN":
            if translatDict[word]:
                if debug>0: print(f'翻譯: {word} > {translatDict[word]}')
                return translatDict[word], newKey
        elif Type=="ZH_CN2EN":
            key = getDictKey(word,translatDict)
            if debug>0: print(f'翻譯: {word} > {key}')
            return key, newKey

    except (KeyError,IndexError):
        newKey = True
        
        if debug>0: print('字典中無此翻譯!! 將由線上獲取該翻譯')
        translat, Type = youdaoAPI(word) #調用API翻譯關鍵字   
        if debug>0: print(f'儲存翻譯: {word} >> {translat}')
        if Type=="EN2ZH_CN":
            writeFile(dictFile,f'{word}\t\t{translat}\n',mode='a')
        elif Type=="ZH_CN2EN":
            writeFile(dictFile,f'{translat}\t\t{word}\n',mode='a')
        else:
#             print(f'[DEBUG] Type: {Type}, {word} {translat}') #無法識別語言
            writeFile(dictFile,f'{word}\t\t{translat}\n',mode='a')
            
        translatDict = readTranslatDict(dictFile) #從文件中讀取字典
        
        if Type=="EN2ZH_CN":
            if translatDict[word]:
                if debug>0: print(f'翻譯: {word} >> {translatDict[word]}')
                return translatDict[word], newKey
        elif Type=="ZH_CN2EN":
            key = getDictKey(word,translatDict)
            if debug>0: print(f'翻譯: {word} >> {key}')
            return key, newKey
        else:
            if debug>0: print(f'翻譯: {word} >> {translatDict[word]}')
            return translatDict[word], newKey

def translateBack(word): #有道翻譯API
    
    #讀取翻譯紀錄,節省已查過的字串請求次數
    dictFile = 'translate.txt'
    translatDict = {}
    translatLi = []
    if os.path.exists(dictFile):
        translatLi = readFile2List(dictFile)
    for text in translatLi:
        x,y = text.split('\t\t')
        translatDict[x.strip()]=y.strip()
        
    text_ = ''
    for ppp in word.split(','):
        ppp = ppp.strip()
        key,text,txt,wight,LV,LV_Neg,notInput = K(ppp)
#         print(txt)
        LVli = [["",""],["{","}"],["("*(LV-1),")"*(LV-1)],["["*(LV_Neg-1),"]"*(LV_Neg-1)]]
        for key_ in translatDict:
            noTranslat = True
            try:
                if translatDict[key_]==txt:
                    text_+=f'T:{key_}'
                    text_+=', '
                    noTranslat = False
                    break
            except:
                pass
        if noTranslat:
            text_+=f'{key}'
            text_+=', '
    print(text_)


def openPoseImageResize(openPoseImagePath,resize=(512,512),mode=None,ratio=1.0):
    '''
    resize: 輸出引導圖的尺寸, 建議與文生圖大小一致
    mode: 原始引導圖放置於輸出引導圖的甚麼位置, 輸入接受1-9 ,分別是左上1, 中上2, 右上3, 左中4, 中5, 右中6, 左下7, 中下8, 右下9, 預設為8
    ratio: 原始引導圖的縮放比例, 越小引導圖生成的人物越小
    '''
    from myfn2.readImage import readImage
    from myfn2.genBaseImage import genBaseImage
    from myfn2.imgResize import imgResize
    import os
    openPoseImage = readImage(openPoseImagePath) #原始openPose參照圖
#     imshow(openPoseImage)
    img = genBaseImage(resize,RGB=[0,0,0]) #底圖
#     imshow(img)

    openPoseMax = max(openPoseImage.size) #疊加圖的最大邊
    imgMin = min(img.size) #底圖的最小邊
    
    #疊加圖需要縮放到底圖最小邊
    r = float(imgMin)/float(openPoseMax)*float(ratio)
    openPoseImageXsize, openPoseImageYsize = openPoseImage.size
    openPoseImageXsize, openPoseImageYsize = int(openPoseImageXsize*r), int(openPoseImageYsize*r)
    new_openPoseImage = imgResize(openPoseImage,(openPoseImageXsize, openPoseImageYsize))
#     imshow(new_openPoseImage)
    
    #計算放置點
    
    XMoveMax = img.size[0] - new_openPoseImage.size[0] #X軸最大可移動範圍
    YMoveMax = img.size[1] - new_openPoseImage.size[1] #Y軸最大可移動範圍
#     print(new_openPoseImage.size,img.size)
#     print(XMoveMax,YMoveMax)
    LU=(0,0) #左上
    LM=(0,YMoveMax//2) #左中
    LD=(0,YMoveMax)#左下
    MU=(XMoveMax//2,0)#中上
    MM=(XMoveMax//2,YMoveMax//2)#置中
    MD=(XMoveMax//2,YMoveMax)#中下 (預設)
    RU=(XMoveMax,0) #右上
    RM=(XMoveMax,YMoveMax//2) #右中
    RD=(XMoveMax,YMoveMax) #右下
    if mode==1: MV=LU
    elif mode==2: MV=MU
    elif mode==3: MV=RU
    elif mode==4: MV=LM
    elif mode==5: MV=MM
    elif mode==6: MV=RM
    elif mode==7: MV=LD
    elif mode==8: MV=MD
    elif mode==9: MV=RD
    else: MV=MD
    
    #合併兩張圖
    img_copy = img.copy()
    img_copy.paste(new_openPoseImage,MV)
    # imshow(img_copy)
#     return img_copy
    img_copy.save(os.path.abspath('temp.png'))
    return os.path.abspath('temp.png')
    
def replaceTags(text:str,replaceDict, debug=1): #替換關鍵詞
    '''
    替換關鍵詞
    text: 要替換的字串
    replaceDict: 替換關鍵詞使用的字典或字串('A|A1, B|B1')
    '''
    def str2Dict(text): #替換關鍵詞 (字串轉字典)
        list_ = [x.strip() for x in text.split(',')]
        dict_ = {x.split('|')[0].strip():x.split('|')[1].strip() for x in list_}
        return dict_
    
    if type(replaceDict) is not dict: replaceDict = str2Dict(replaceDict) 
        
    for key in replaceDict:
        if key in text:
            if debug: print(f'替換關鍵詞 "{key}" > "{replaceDict[key]}"')
            text = text.replace(key,replaceDict[key])
    return text

if __name__ == "__main__": #不是被調用狀況下, 將執行此命令用於顯示此函數的使用方式
	pass
