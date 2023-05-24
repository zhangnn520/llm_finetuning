# @Time    : 2023/4/2 22:49
# @Author  : tk
# @FileName: infer_ptuning
import os

import torch
from deep_training.data_helper import ModelArguments, TrainingArguments, DataArguments
from transformers import HfArgumentParser,AutoConfig,PreTrainedTokenizer

from data_utils import train_info_args, NN_DataHelper
from models import MyTransformer, Generate,LoraArguments,PromptArguments

if __name__ == '__main__':
    train_info_args['seed'] = None
    parser = HfArgumentParser((ModelArguments, TrainingArguments, DataArguments, LoraArguments,PromptArguments))
    model_args, training_args, data_args, _,_ = parser.parse_dict(train_info_args)



    dataHelper = NN_DataHelper(model_args, training_args, data_args)
    tokenizer, _, _, _ = dataHelper.load_tokenizer_and_config(config_kwargs={"torch_dtype": torch.float16})

    ckpt_dir = './best_ckpt'
    config = AutoConfig.from_pretrained(ckpt_dir)
    prompt_args = PromptArguments.from_pretrained(ckpt_dir)

    assert prompt_args.inference_mode == True

    pl_model = MyTransformer(config=config, model_args=model_args, training_args=training_args,prompt_args=prompt_args)
    # 加载sft权重
    pl_model.load_sft_weight(ckpt_dir)

    pl_model.eval().half().cuda()

    model = pl_model.get_llm_model()

    #基础模型精度
    model.base_model_torch_dtype = torch.half

    text_list = ["写一个诗歌，关于冬天",
                 "晚上睡不着应该怎么办"]
    for input in text_list:
        response, history = Generate.chat(model, query=input, tokenizer=tokenizer, max_length=512,
                                          eos_token_id=config.eos_token_id,
                                          do_sample=False, top_p=0.7, temperature=0.95, )
        print('input', input)
        print('output', response)