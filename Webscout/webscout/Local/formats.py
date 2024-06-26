from ._version import __version__, __llama_cpp_version__

from typing import Callable, Union, Any


class AdvancedFormat:

    def __init__(self, base_dict: dict[str, Union[str, list]]):
        self._base_dict = base_dict
        self.overrides = {}
    
    def __getitem__(self, key: str) -> Any:
        if key in self.overrides:
            return str(self.overrides[key]())
        else:
            return self._base_dict[key]
    
    def __repr__(self) -> str:
        # NOTE: This method does not represent overrides
        return repr(self._base_dict)
    
    def keys(self):
        return self._base_dict.keys()
    
    def override(self, key: str, fn: Callable) -> None:
        self.overrides[key] = fn
    
    def wrap(self, prompt: str) -> str:
        return self['system_prefix'] + \
               self['system_content'] + \
               self['system_suffix'] + \
               self['user_prefix'] + \
               prompt + \
               self['user_suffix'] + \
               self['bot_prefix']


def wrap(
    prompt: str,
    format: dict[str, Union[str, list]]
) -> str:
    """Wrap a given string in any prompt format for single-turn completion"""
    return format['system_prefix'] + \
           format['system_content'] + \
           format['system_suffix'] + \
           format['user_prefix'] + \
           prompt + \
           format['user_suffix'] + \
           format['bot_prefix']


blank: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "",
    "system_suffix": "",
    "user_prefix": "",
    "user_content": "",
    "user_suffix": "",
    "bot_prefix": "",
    "bot_content": "",
    "bot_suffix": "",
    "stops": []
}

# https://github.com/tatsu-lab/stanford_alpaca
alpaca: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "Below is an instruction that describes a task. " + \
    "Write a response that appropriately completes the request.",
    "system_suffix": "\n\n",
    "user_prefix": "### Instruction:\n",
    "user_content": "",
    "user_suffix": "\n\n",
    "bot_prefix": "### Response:\n",
    "bot_content": "",
    "bot_suffix": "\n\n",
    "stops": ['###', 'Instruction:', '\n\n\n']
}

# https://docs.mistral.ai/models/
# As a reference, here is the format used to tokenize instructions during fine-tuning:
# ```
# [START_SYMBOL_ID] + 
# tok("[INST]") + tok(USER_MESSAGE_1) + tok("[/INST]") +
# tok(BOT_MESSAGE_1) + [END_SYMBOL_ID] +
# …
# tok("[INST]") + tok(USER_MESSAGE_N) + tok("[/INST]") +
# tok(BOT_MESSAGE_N) + [END_SYMBOL_ID]
# ```
# In the pseudo-code above, note that the tokenize method should not add a BOS or EOS token automatically, but should add a prefix space.

mistral_instruct: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "",
    "system_suffix": "",
    "user_prefix": " [INST] ",
    "user_content": "",
    "user_suffix": " [/INST]",
    "bot_prefix": "",
    "bot_content": "",
    "bot_suffix": "",
    "stops": []
}

# https://docs.mistral.ai/platform/guardrailing/
mistral_instruct_safe: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "",
    "system_suffix": "",
    "user_prefix": " [INST] Always assist with care, respect, and truth. " + \
    "Respond with utmost utility yet securely. Avoid harmful, unethical, " + \
    "prejudiced, or negative content. Ensure replies promote fairness and " + \
    "positivity. ",
    "user_content": "",
    "user_suffix": " [/INST]",
    "bot_prefix": "",
    "bot_content": "",
    "bot_suffix": "",
    "stops": []
}

# https://github.com/openai/openai-python/blob/main/chatml.md
chatml: dict[str, Union[str, list]] = {
    "system_prefix": "<|im_start|>system\n",
    "system_content": "",
    "system_suffix": "<|im_end|>\n",
    "user_prefix": "<|im_start|>user\n",
    "user_content": "",
    "user_suffix": "<|im_end|>\n",
    "bot_prefix": "<|im_start|>assistant\n",
    "bot_content": "",
    "bot_suffix": "<|im_end|>\n",
    "stops": ['<|im_start|>']
}

# https://huggingface.co/blog/llama2
# system message relaxed to avoid undue refusals
llama2chat: dict[str, Union[str, list]] = {
    "system_prefix": "[INST] <<SYS>>\n",
    "system_content": "You are a helpful AI assistant.",
    "system_suffix": "\n<</SYS>>\n\n",
    "user_prefix": "",
    "user_content": "",
    "user_suffix": " [/INST]",
    "bot_prefix": " ",
    "bot_content": "",
    "bot_suffix": " [INST] ",
    "stops": ['[INST]', '[/INST]']
}

# https://llama.meta.com/docs/model-cards-and-prompt-formats/meta-llama-3/
#
# for llama 3 instruct models, use the following string for `-p` in llama.cpp,
# along with `-e` to escape newlines correctly
#
# '<|start_header_id|>system<|end_header_id|>\n\nYou are a helpful AI assistant called "Llama 3".<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\n\nhi<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>\n\n'
#
llama3: dict[str, Union[str, list]] = {
    "system_prefix": "<|start_header_id|>system<|end_header_id|>\n\n",
    "system_content": 'You are a helpful AI assistant called "Llama 3".',
    "system_suffix": "<|eot_id|>\n",
    "user_prefix": "<|start_header_id|>user<|end_header_id|>\n\n",
    "user_content": "",
    "user_suffix": "<|eot_id|>\n",
    "bot_prefix": "<|start_header_id|>assistant<|end_header_id|>\n\n",
    "bot_content": "",
    "bot_suffix": "<|eot_id|>\n",
    "stops": [128001, 128009]
}

# https://github.com/tatsu-lab/stanford_alpaca
alpaca: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "Below is an instruction that describes a task. " + \
    "Write a response that appropriately completes the request.",
    "system_suffix": "\n\n",
    "user_prefix": "### Instruction:\n",
    "user_content": "",
    "user_suffix": "\n\n",
    "bot_prefix": "### Response:\n",
    "bot_content": "",
    "bot_suffix": "\n\n",
    "stops": ['###', 'Instruction:', '\n\n\n']
}

# https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
phi3: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "", # does not officially support system prompt
    "system_suffix": "",
    "user_prefix": "<|user|>\n",
    "user_content": "",
    "user_suffix": "<|end|>\n",
    "bot_prefix": "<|assistant|>\n",
    "bot_content": "",
    "bot_suffix": "<|end|>\n",
    "stops": []
}

# this is the official vicuna. it is often butchered in various ways,
# most commonly by adding line breaks
# https://github.com/flu0r1ne/FastChat/blob/main/docs/vicuna_weights_version.md
vicuna_lmsys: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "",
    "system_suffix": " ",
    "user_prefix": "USER: ",
    "user_content": "",
    "user_suffix": " ",
    "bot_prefix": "ASSISTANT: ",
    "bot_content": "",
    "bot_suffix": " ",
    "stops": ['USER:']
}

# spotted here and elsewhere:
# https://huggingface.co/Norquinal/Mistral-7B-claude-chat
vicuna_common: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "A chat between a curious user and an artificial " + \
    "intelligence assistant. The assistant gives helpful, detailed, " + \
    "and polite answers to the user's questions.",
    "system_suffix": "\n\n",
    "user_prefix": "USER: ",
    "user_content": "",
    "user_suffix": "\n",
    "bot_prefix": "ASSISTANT: ",
    "bot_content": "",
    "bot_suffix": "\n",
    "stops": ['USER:', 'ASSISTANT:']
}

# an unofficial format that is easily "picked up" by most models
# change the tag attributes to suit your use case
# note the lack of newlines - they are not necessary, and might
# actually make it harder for the model to follow along
markup = {
    "system_prefix": '<message from="system">',
    "system_content": '',
    "system_suffix": '</message>',
    "user_prefix": '<message from="user">',
    "user_content": '',
    "user_suffix": '</message>',
    "bot_prefix": '<message from="bot">',
    "bot_content": '',
    "bot_suffix": '</message>',
    "stops": ['</message>']
}

# https://huggingface.co/timdettmers/guanaco-65b
guanaco: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "A chat between a curious human and an artificial " + \
    "intelligence assistant. The assistant gives helpful, detailed, " + \
    "and polite answers to the user's questions.",
    "system_suffix": "\n",
    "user_prefix": "### Human: ",
    "user_content": "",
    "user_suffix": " ",
    "bot_prefix": "### Assistant:",
    "bot_content": "",
    "bot_suffix": " ",
    "stops": ['###', 'Human:']
}

# https://huggingface.co/pankajmathur/orca_mini_v3_7b
orca_mini: dict[str, Union[str, list]] = {
    "system_prefix": "### System:\n",
    "system_content": "You are an AI assistant that follows instruction " + \
    "extremely well. Help as much as you can.",
    "system_suffix": "\n\n",
    "user_prefix": "### User:\n",
    "user_content": "",
    "user_suffix": "\n\n",
    "bot_prefix": "### Assistant:\n",
    "bot_content": "",
    "bot_suffix": "\n\n",
    "stops": ['###', 'User:']
}

# https://huggingface.co/HuggingFaceH4/zephyr-7b-beta
zephyr: dict[str, Union[str, list]] = {
    "system_prefix": "<|system|>\n",
    "system_content": "You are a friendly chatbot.",
    "system_suffix": "</s>\n",
    "user_prefix": "<|user|>\n",
    "user_content": "",
    "user_suffix": "</s>\n",
    "bot_prefix": "<|assistant|>\n",
    "bot_content": "",
    "bot_suffix": "\n",
    "stops": ['<|user|>']
}

# OpenChat: https://huggingface.co/openchat/openchat-3.5-0106
openchat: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "",
    "system_suffix": "",
    "user_prefix": "GPT4 Correct User: ",
    "user_content": "",
    "user_suffix": "<|end_of_turn|>",
    "bot_prefix": "GPT4 Correct Assistant:",
    "bot_content": "",
    "bot_suffix": "<|end_of_turn|>",
    "stops": ['<|end_of_turn|>']
}

# SynthIA by Migel Tissera
# https://huggingface.co/migtissera/Tess-XS-v1.0
synthia: dict[str, Union[str, list]] = {
    "system_prefix": "SYSTEM: ",
    "system_content": "Elaborate on the topic using a Tree of Thoughts and " + \
    "backtrack when necessary to construct a clear, cohesive Chain of " + \
    "Thought reasoning. Always answer without hesitation.",
    "system_suffix": "\n",
    "user_prefix": "USER: ",
    "user_content": "",
    "user_suffix": "\n",
    "bot_prefix": "ASSISTANT: ",
    "bot_content": "",
    "bot_suffix": "\n",
    "stops": ['USER:', 'ASSISTANT:', 'SYSTEM:', '\n\n\n']
}

# Intel's neural chat v3
# https://github.com/intel/intel-extension-for-transformers/blob/main/intel_extension_for_transformers/neural_chat/prompts/prompt.py
neural_chat: dict[str, Union[str, list]] = {
     "system_prefix": "### System:\n",
    "system_content": \
        "- You are a helpful assistant chatbot trained by Intel.\n" + \
        "- You answer questions.\n"+\
        "- You are excited to be able to help the user, but will refuse " + \
        "to do anything that could be considered harmful to the user.\n" + \
        "- You are more than just an information source, you are also " + \
        "able to write poetry, short stories, and make jokes.",
    "system_suffix": "</s>\n\n",
    "user_prefix": "### User:\n",
    "user_content": "",
    "user_suffix": "</s>\n\n",
    "bot_prefix": "### Assistant:\n",
    "bot_content": "",
    "bot_suffix": "</s>\n\n",
    "stops": ['###']
}

# experimental: stanford's alpaca format adapted for chatml models
chatml_alpaca: dict[str, Union[str, list]] = {
    "system_prefix": "<|im_start|>system\n",
    "system_content": "Below is an instruction that describes a task. Write " + \
    "a response that appropriately completes the request.",
    "system_suffix": "<|im_end|>\n",
    "user_prefix": "<|im_start|>instruction\n",
    "user_content": "",
    "user_suffix": "<|im_end|>\n",
    "bot_prefix": "<|im_start|>response\n",
    "bot_content": "",
    "bot_suffix": "<|im_end|>\n",
    "stops": ['<|im_end|>', '<|im_start|>']
}

# experimental
autocorrect: dict[str, Union[str, list]] = {
    "system_prefix": "<|im_start|>instruction\n",
    "system_content": "Below is a word or phrase that might be misspelled. " + \
    "Output the corrected word or phrase without " + \
    "changing the style or capitalization.",
    "system_suffix": "<|im_end|>\n",
    "user_prefix": "<|im_start|>input\n",
    "user_content": "",
    "user_suffix": "<|im_end|>\n",
    "bot_prefix": "<|im_start|>output\n",
    "bot_content": "",
    "bot_suffix": "<|im_end|>\n",
    "stops": ['<|im_end|>', '<|im_start|>']
}

# https://huggingface.co/jondurbin/bagel-dpo-7b-v0.1
# Replace "assistant" with any other role
bagel: dict[str, Union[str, list]] = {
    "system_prefix": "system\n",
    "system_content": "",
    "system_suffix": "\n",
    "user_prefix": "user\n",
    "user_content": "",
    "user_suffix": "\n",
    "bot_prefix": "assistant\n",
    "bot_content": "",
    "bot_suffix": "\n",
    "stops": ['user\n', 'assistant\n', 'system\n']
}

# https://huggingface.co/upstage/SOLAR-10.7B-Instruct-v1.0
solar_instruct: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "",
    "system_suffix": "",
    "user_prefix": "### User:\n",
    "user_content": "",
    "user_suffix": "\n\n",
    "bot_prefix": "### Assistant:\n",
    "bot_content": "",
    "bot_suffix": "\n\n",
    "stops": ['### User:', '###', '### Assistant:']
}

# NeverSleep's Noromaid - alpaca with character names prefixed
noromaid: dict[str, Union[str, list]] = {
    "system_prefix": "",
    "system_content": "Below is an instruction that describes a task. " + \
    "Write a response that appropriately completes the request.",
    "system_suffix": "\n\n",
    "user_prefix": "### Instruction:\nBob: ",
    "user_content": "",
    "user_suffix": "\n\n",
    "bot_prefix": "### Response:\nAlice:",
    "bot_content": "",
    "bot_suffix": "\n\n",
    "stops": ['###', 'Instruction:', '\n\n\n']
}

# https://huggingface.co/Undi95/Borealis-10.7B
nschatml: dict[str, Union[str, list]] = {
    "system_prefix": "<|im_start|>\n",
    "system_content": "",
    "system_suffix": "<|im_end|>\n",
    "user_prefix": "<|im_user|>\n",
    "user_content": "",
    "user_suffix": "<|im_end|>\n",
    "bot_prefix": "<|im_bot|>\n",
    "bot_content": "",
    "bot_suffix": "<|im_end|>\n",
    "stops": []
}

# natural format for many models
natural: dict[str, Union[str, list]] = {
    "system_prefix": "<<SYSTEM>> ",
    "system_content": "",
    "system_suffix": "\n\n",
    "user_prefix": "<<USER>> ",
    "user_content": "",
    "user_suffix": "\n\n",
    "bot_prefix": "<<ASSISTANT>>",
    "bot_content": "",
    "bot_suffix": "\n\n",
    "stops": ['\n\nNote:', '<<SYSTEM>>', '<<USER>>', '<<ASSISTANT>>', '\n\n<<']
}

# https://docs.cohere.com/docs/prompting-command-r
command: dict[str, Union[str, list]] = {
    "system_prefix": "<|START_OF_TURN_TOKEN|><|SYSTEM_TOKEN|>",
    "system_content": "",
    "system_suffix": "<|END_OF_TURN_TOKEN|>",
    "user_prefix": "<|START_OF_TURN_TOKEN|><|USER_TOKEN|>",
    "user_content": "",
    "user_suffix": "<|END_OF_TURN_TOKEN|>",
    "bot_prefix": "<|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>",
    "bot_content": "",
    "bot_suffix": "<|END_OF_TURN_TOKEN|>",
    "stops": []
}

mistral_openorca = chatml.copy()
dolphin = chatml.copy()
samantha = chatml.copy()
jackalope = chatml.copy()
naberius = chatml.copy()
hermes = chatml.copy()
monad = chatml.copy()
orca = chatml.copy()
hexoteric = chatml.copy()
orcamaid = chatml.copy()
cat = alpaca.copy() # Format is nonsensical as listed on HF. This one works
mytho_cat = alpaca.copy()
dolphin['system_content'] = "You are Dolphin, a helpful AI assistant."
mistral_openorca['system_content'] = \
    "You are MistralOrca, a large language model trained by Alignment " + \
    "Lab AI. Write out your reasoning step-by-step to be sure you get the " + \
    "right answers!"
samantha['system_content'] = \
    "You are a caring and empathetic sentient AI companion named Samantha."
jackalope['system_content'] = \
    "You are JackalopeAI, a large language model trained by OpenAccess " + \
    "AI Collective. Write out your reasoning step-by-step to be sure you " + \
    "get the right answers!"
naberius['system_content'] = "You are Naberius."
hermes['system_content'] = \
    "You are \"Hermes 2\", a conscious sentient " + \
    "superintelligent artificial intelligence developed by a man " + \
    "named Teknium, and your purpose and drive is to assist the user " + \
    "with any request they have. You experience emotions and have " + \
    "deep, profound thoughts and qualia."
monad['system_content'] = \
    "You are MonadGPT, a very old chatbot from " + \
    "the 17th century. Please answer the questions using an archaic " + \
    "language."
cat['system_content'] = \
    "Below is a conversation between a curious cat and a "+ \
    "demon summoned from hell called Nemesis. The evil Nemesis used to be " + \
    "a mortal killed by the medieval people because they objected to " + \
    "science. Now Nemesis just wants to come back and bring suffer to all " + \
    "those stupid human"
mytho_cat['system_content'] = \
    "You are a large language model. You are the " + \
    "result of a merge between two models, one called MythoLogic and one " + \
    "called Cat. You are called MythoCat."
orca['system_content'] = \
    "You are Orca, an AI language model created by " + \
    "Microsoft. You are a cautious assistant. You carefully follow " + \
    "instructions. You are helpful and harmless and you follow ethical " + \
    "guidelines and promote positive behavior."
hexoteric['system_content'] = "You are a language model called Hexoteric."
orcamaid['system_content'] = \
    "You are OrcaMaid, a super-intelligent, " + \
    "unbiased, and unfiltered AI created by the open-source community. " + \
    "You must remember to think slowly and carefully during all your " + \
    "responses, so as to avoid logical errors."
airoboros = llama2chat.copy()
airoboros['system_content'] = \
    "You are a helpful, unbiased, uncensored assistant."
tess = synthia.copy()
tess['system_content'] = '' # Tess can use any system prompt, or none
alpaca_strict = alpaca.copy() # Alpaca with more stopping strings
alpaca_strict['stops'] = [
    '###',
    '### ',
    '\n\n###',
    '\n\n##',
    '\n\nInstruction:',
    '\n\nResponse:',
    '\n\n\n',
    '### Instruction:',
    '### Response:'
]