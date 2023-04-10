import modules.scripts as scripts
import sys
base_dir = scripts.basedir()
sys.path.append(base_dir)

import numpy as np
from tqdm import trange

import modules.scripts as scripts
import gradio as gr

from modules import processing, shared, sd_samplers, images, prompt_parser, script_callbacks
from modules.processing import Processed, process_images, StableDiffusionProcessing
from modules.sd_samplers import samplers
from modules.shared import opts, cmd_opts, state

from tagsGenerator import findTag, promptOutput

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
                runOn = gr.Checkbox(label='是否啟用 M-prompt', value=False)
                seeTags1 = gr.Checkbox(label='顯示輸入的tag(替換前)', value=False)
                seeTags2 = gr.Checkbox(label='顯示輸入的tag(替換後)', value=False)
                # 设置输入组件
                text = gr.Textbox(label="\n查詢關鍵字")
                # 设置按钮
                greet_btn = gr.Button("查詢")
                # 设置输出组件
                output = gr.Textbox(label="查詢結果")
                # 设置按钮点击事件
                greet_btn.click(fn=findTags, inputs=text, outputs=output)
        return [runOn, seeTags1, seeTags2]

    def process( self, p: StableDiffusionProcessing, runOn: bool, seeTags1: bool, seeTags2: bool):
        """
        This function is called before processing begins for AlwaysVisible scripts.
        You can modify the processing object (p) here, inject hooks, etc.
        args contains all values returned by components from ui()
        
        这个函数在AlwaysVisible脚本开始处理之前被调用。
        你可以在这里修改处理对象(p)，注入钩子等等。
        Args包含ui()中组件返回的所有值
        """
        if runOn:
            prompt1,prompt2 = promptOutput(p.prompt)
            neprompt1,neprompt2 = promptOutput(p.negative_prompt)
            p.prompt = prompt2
            p.negative_prompt = neprompt2
            if seeTags1:
                print(f'替換前-- [prompt] \n"{prompt1}" \n[negative_prompt] "{neprompt1}"\n')
            if seeTags2:
                print(f'替換後-- [prompt] \n"{prompt2}" \n[negative_prompt] "{neprompt2}"\n')
            