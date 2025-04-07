from transformers import LlamaForCausalLM, LlamaTokenizer
from transformers import BitsAndBytesConfig
import torch

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

class TinyLlamaModel:
    def __init__(self, model_name: str = MODEL_NAME):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        self.tokenizer = LlamaTokenizer.from_pretrained(model_name)
        self.model = LlamaForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto"
        )
    
    def format_prompt(self, message: str) -> str:
        return f"""<|system|>
You are a helpful AI assistant.</s>
<|user|>
{message}</s>
<|assistant|>"""
    
    def generate(self, prompt: str, max_length: int = 256, temperature: float = 0.7) -> str:
        formatted_prompt = self.format_prompt(prompt)
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=0.9,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3,
                do_sample=True
            )
        
        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Вырезаем только ответ ассистента
        return full_text.split("<|assistant|>")[-1].strip()

if __name__ == "__main__":
    model = TinyLlamaModel()
    print(model.generate("Привет, как тебя зовут?"))