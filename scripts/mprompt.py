import modules.scripts as scripts
import sys
base_dir = scripts.basedir()
sys.path.append(base_dir)

import numpy as np
import random
from tqdm import trange

import modules.scripts as scripts
import gradio as gr

from modules import processing, shared, sd_samplers, images, prompt_parser, script_callbacks
from modules.processing import Processed, process_images, StableDiffusionProcessing
from modules.sd_samplers import samplers
from modules.shared import opts, cmd_opts, state

from tagsGenerator import findTag, promptOutput, randomLoadPromptFile, mixPromptFromFiles, replaceTags

class M_promptScript(scripts.Script):
    
    def __init__(self) -> None:
        super().__init__()
        
    def title(self):
        return 'M-prompt'

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img): 
        
        # 输入文本处理程序
        def findTags(text): #查詢Tags
            def tag2Text(TagsLi):
                outputText=''
                for item in TagsLi:
                    # print(item)
                    outputText+=f'{item[0]} : {item[1]}\n'
                return str(outputText)
            return tag2Text(findTag(text))
            
        with gr.Accordion('M-prompt', open=False, elem_id='M_prompt'):
            with gr.Blocks() as demo:
                runOn = gr.Checkbox(label='是否開啟 M-prompt', value=False)

                with gr.Accordion('隨機獲取圖片參數', open=True):
                    readImageTagsOn = gr.Radio(choices=['不使用','獲取單圖片參數','獲取混合圖片參數'], value=0, type="index", label='隨機獲取圖片參數:')
                    #混合圖片數量(僅獲取混合圖片參數時使用)
                    mixImageNum = gr.Slider(label="混合圖片數量:", interactive=True, minimum=1, maximum=10, step=1, value=3)
                
                with gr.Accordion('替換關鍵詞', open=True):
                    #替換關鍵詞
                    replaceTagsInput = gr.Textbox(label="替換關鍵詞輸入框:",value='')
                

                with gr.Accordion('查詢關鍵字', open=False):
                    # 设置输入组件
                    text = gr.Textbox(label="\n查詢關鍵字:")
                    # 设置按钮
                    greet_btn = gr.Button("查詢:")
                    # 设置输出组件
                    output = gr.Textbox(label="查詢結果:")
                    # 设置按钮点击事件
                    greet_btn.click(fn=findTags, inputs=text, outputs=output)

        return [runOn, readImageTagsOn, mixImageNum, replaceTagsInput]

    def process( self, p: StableDiffusionProcessing, runOn: bool, readImageTagsOn: int, mixImageNum: int, replaceTagsInput:str):
        """
        This function is called before processing begins for AlwaysVisible scripts.
        You can modify the processing object (p) here, inject hooks, etc.
        args contains all values returned by components from ui()
        
        这个函数在AlwaysVisible脚本开始处理之前被调用。
        你可以在这里修改处理对象(p)，注入钩子等等。
        Args包含ui()中组件返回的所有值
        """
        if runOn: # 開啟 M-prompt
            print('[DEBUG] readImageTagsOn:',readImageTagsOn)
            # print('p:',dir(p))
            p_prompt = p.prompt.strip()
            p_negative_prompt = p.negative_prompt.strip()
            print('[DEBUG] p_prompt',p_prompt)
            print('[DEBUG] p_negative_prompt',p_negative_prompt)
            
            if len(p.prompt.strip())>0:
                if p.prompt.strip()[-1]==',':
                    p_prompt = p.prompt.strip()
                else:
                    p_prompt = p.prompt.strip()+', '
                    
            if len(p.negative_prompt.strip())>0:
                if p.negative_prompt.strip()[-1]==',':
                    p_negative_prompt = p.negative_prompt.strip()
                else:
                    p_negative_prompt = p.negative_prompt.strip()+', '

            if readImageTagsOn==1:
                print('單一圖片模式:')
                prompt, np_prompt, promptDict = randomLoadPromptFile()
                p_prompt += promptDict['prompt']
                p_negative_prompt += promptDict['negative_prompt']
                p.prompt, p.negative_prompt = promptOutput(p_prompt)[1], promptOutput(p_negative_prompt)[1]
                # if seeTags1 or seeTags2:
                print(f"[prompt] \n{p.prompt} \n\n[negative_prompt] \n{p.negative_prompt}\n")
                
            elif readImageTagsOn==2:
                randomN = int(3+random.random()*3)
                print(f'混合圖片模式({mixImageNum}): ')
                promptDict = mixPromptFromFiles(promptDirPath='txt',n=mixImageNum)
                p_prompt += promptDict['prompt']
                p_negative_prompt += promptDict['negative_prompt']
                p.prompt, p.negative_prompt = promptOutput(p_prompt)[1], promptOutput(p_negative_prompt)[1]
                # if seeTags1 or seeTags2:
                print(f"[prompt] \n{p.prompt} \n\n[negative_prompt] \n{p.negative_prompt}\n")
                
            else:
                prompt1, prompt2 = promptOutput(p.prompt)
                neprompt1, neprompt2 = promptOutput(p.negative_prompt)
                p.prompt = prompt2
                p.negative_prompt = neprompt2
                # if seeTags1:
                print(f'替換前-- \n[prompt] \n{prompt1} \n\n[negative_prompt] \n{neprompt1}\n')
                # if seeTags2:
                print(f'替換後-- \n[prompt] \n{prompt2} \n\n[negative_prompt] \n{neprompt2}\n')
            
            
            if len(replaceTagsInput)>0: #替換關鍵詞不為空
                p.prompt = replaceTags(p.prompt, replaceTagsInput)
                p.negative_prompt = replaceTags(p.negative_prompt, replaceTagsInput)
            
            # print(p.prompt)
            # print(p.negative_prompt)
            # print(p.all_prompts)
            # print(p.all_negative_prompts)
            
            p.all_prompts = [p.prompt]
            p.all_negative_prompts = [p.negative_prompt]
            
        else:
            pass

            
            