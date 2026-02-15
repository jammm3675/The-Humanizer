import sys
import os

with open('services/ai_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update DYNAMIC_PROMPT in generate_response to include Markdown instruction
markdown_instruction = "\nИНСТРУКЦИЯ ПО ФОРМАТИРОВАНИЮ:\nРазрешено и приветствуется использование Markdown (жирный, курсив)."
content = content.replace('ИНСТРУКЦИЯ:', markdown_instruction + '\nИНСТРУКЦИЯ:')

# 2. Add generate_interjection method before 'ai_service = AIService()'
interjection_method = """
    async def generate_interjection(self, global_lore: str):
        if not self.client: return None

        system_prompt = self.bot_params.get("description", "")

        prompt = f\"\"\"{system_prompt}

БАЗА ЗНАНИЙ (Lore):
{global_lore}

ЗАДАЧА:
Напиши короткую ироничную реплику, шутку или мем-фразу про коллекцию NOTAPES или крипту в целом.
Это должно быть внезапное сообщение в чат.
Используй Markdown для форматирования (жирный, курсив).
Пиши как Pinkie Ape: дерзко, цифровой вайб, коротко.\"\"\"

        try:
            completion = await self.client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model=self.model_name,
                temperature=0.9,
                max_tokens=200
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Interjection generation error: {e}")
            return None

"""

insertion_point = content.find('ai_service = AIService()')
content = content[:insertion_point] + interjection_method + content[insertion_point:]

with open('services/ai_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("ai_service.py updated successfully")
