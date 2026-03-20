import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Cargar variables del .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: No se encontró GEMINI_API_KEY en el .env")
else:
    try:
        # 2. Configurar el SDK
        genai.configure(api_key=api_key)

        # 3. Intentar una generación simple (Flash es el que usas en el Dashboard)
        # Intenta con el nombre exacto que Google espera hoy:
        model = genai.GenerativeModel('gemini-2.5-flash')

        # O si el anterior falla, el modelo estable:
        # model = genai.GenerativeModel('gemini-pro')

        print(f"Testing Gemini with key: {api_key[:5]}...{api_key[-5:]}")
        response = model.generate_content(
            "Hola, dime 'Conexión exitosa' si puedes leerme.")

        print("-" * 30)
        print(f"Respuesta de la IA: {response.text}")
        print("-" * 30)
        print("✅ ¡Tu API Key funciona perfectamente!")

    except Exception as e:
        print(f"❌ Error de conexión con Gemini: {str(e)}")
