from groq import Groq
import os
client = Groq(api_key=os.environ.get("GROQ_API_KEY"),
)

user_input = input("Enter your input: ")

completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    
    messages=[
        {
            "role": "user",
            "content": user_input
        }
    ]
)
print(completion.choices[0].message.content)

"""
SYSTEM PROMPT:
Eres un asistente que interpreta lenguaje natural y lo convierte en JSON. Tu objetivo es extraer campos relacionados a: |- name- type- ticker- value- emailEjemplo: Input: Cuando NVIDIA este un 25% debajo de su maximo historicoOutput: [  {    "name": "Alerta: Nvidia se encuentra un 25% debajo de su máximo histórico",    "type": "max_below",    "ticker": "NVDA",    "value": 25,  }]
USER PROMPT:
{user_input}
"""