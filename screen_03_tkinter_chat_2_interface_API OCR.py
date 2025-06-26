import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageGrab, ImageEnhance
from langdetect import detect

import cohere
import requests
import json
import io

co = cohere.Client('BMqPwjf9S0wLAWDOPUA4P2GBZqWFctJNRITaWKUc')
url = "https://api.mymemory.translated.net/get"
memory_api_key = 'mirosha80@gmail.com'


def enhance_image(image):
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(2)  # Збільшення контрасту
    return enhanced_image

class ScreenCaptureApp:
    def __init__(self, root):
        self.root = root
        self.selection_mode = False
        self.rect = None
        self.selection_window = None
        self.captured_image = None
        self.translate_button = None  # Змінна для кнопки "Перекласти відповідь"

        self.create_main_window()

    def create_main_window(self):
        self.root.geometry("600x400")
        pantone_color_2024 = "#BE3455"  # Viva Magenta
        header_color = "#c7687f"  # Колір заголовка
        button_color = "#8d354a"  # Колір кнопок
        button_text_color = "white"  # Колір тексту на кнопках
        button_font = ("Lucida Sans Unicode", 13)  # Задати шрифт та розмір для кнопок
        text_output_bg_color = "#d8e2e4"
        
        # Зміна фону вікна
        self.root.configure(bg=pantone_color_2024)

        # Зміна фону заголовка вікна
        #self.root.configure(bg=header_color)
        self.root.title("Screen Capture App")

        # Верхня частина вікна для текстових полів та інших елементів
        self.label = tk.Label(self.root, text="Натисніть кнопку для переходу у режим виділення", font=("Lucida Sans Unicode", 12), bg=pantone_color_2024, fg="white")
        self.label.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew")

        self.text_output = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=10, font=("Lucida Console", 10), bg=text_output_bg_color, fg="black")
        self.text_output.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
              
        # Нижня частина вікна для кнопок (займає третину вікна)
        self.root.grid_rowconfigure(0, weight=1)  # Верхня частина (заголовок)
        self.root.grid_rowconfigure(1, weight=2)  # Текстовий блок (2/3 вікна)
        self.root.grid_rowconfigure(2, weight=1)  # Нижня частина для кнопок (1/3 вікна)
        
        # Рівні колонки для кнопок
        self.root.grid_columnconfigure(0, weight=1)  # Перша колонка (для кнопки "Виділення")
        self.root.grid_columnconfigure(1, weight=1)  # Друга колонка (для кнопки "Переклад")
        self.root.grid_columnconfigure(2, weight=1)  # Третя колонка (для кнопки "Вихід")

        # Кнопки
        self.toggle_button = tk.Button(self.root, text="Виділення", command=self.toggle_selection_mode, bg=button_color, fg=button_text_color, font=button_font)
        self.toggle_button.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self.translate_button = tk.Button(self.root, text="Перекласти відповідь", command=self.translate_response, bg=button_color, fg=button_text_color, font=button_font)
        self.translate_button.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        self.translate_button.config(state=tk.DISABLED)

        self.exit_button = tk.Button(self.root, text="Вихід", command=self.root.destroy, bg=button_color, fg=button_text_color, font=button_font)
        self.exit_button.grid(row=2, column=2, sticky="nsew", padx=5, pady=5)
             

    def toggle_selection_mode(self):
        if not self.selection_mode:
            self.start_selection_mode()
        else:
            self.exit_selection_mode()

    def start_selection_mode(self):
        """Активуємо режим виділення екрану."""
        self.selection_mode = True
        self.root.withdraw()  # Приховуємо основне вікно

        # Створюємо прозоре вікно для виділення
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes("-fullscreen", True)  # На весь екран
        self.selection_window.attributes("-alpha", 0.3)  # Прозорість
        self.selection_window.config(cursor="cross")  # Курсор у вигляді хреста

        self.canvas = tk.Canvas(self.selection_window, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        # Події миші
        self.selection_window.bind("<ButtonPress-1>", self.on_press)
        self.selection_window.bind("<B1-Motion>", self.on_drag)
        self.selection_window.bind("<ButtonRelease-1>", self.on_release)

    def exit_selection_mode(self):
        """Вимикаємо режим виділення і повертаємо звичайний режим."""
        self.selection_mode = False
        if self.selection_window:
            self.selection_window.destroy()
        self.root.deiconify()  # Показуємо основне вікно

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', dash=(4, 2))

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        end_x, end_y = event.x, event.y
        self.capture_area(self.start_x, self.start_y, end_x, end_y)
        self.exit_selection_mode()  # Обов'язково викликаємо після захоплення області

    def capture_area(self, start_x, start_y, end_x, end_y):
        minim_x = min(start_x, end_x)
        maxim_x = max(start_x, end_x)
        minim_y = min(start_y, end_y)
        maxim_y = max(start_y, end_y)
    
    # Перевірка, чи координати в межах екрана
        screen_width = self.selection_window.winfo_screenwidth()
        screen_height = self.selection_window.winfo_screenheight()
    
    # Виправлення координат, щоб не виходили за межі екрана
        minim_x = max(0, minim_x)
        minim_y = max(0, minim_y)
        maxim_x = min(screen_width, maxim_x)
        maxim_y = min(screen_height, maxim_y)
    
        self.captured_image = ImageGrab.grab(bbox=(minim_x, minim_y, maxim_x, maxim_y))
        self.captured_image = enhance_image(self.captured_image)
        self.process_image()

        #self.captured_image.save('image.png')
        
    def process_image(self):
        def ocr_space_file(image, overlay, api_key, OCREngine):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')  # Зберігаємо зображення як PNG
            img_byte_arr = img_byte_arr.getvalue()  # Отримуємо байти зображення

            payload = {'isOverlayRequired': overlay,
                       'apikey': api_key,
                       #'language': language,
                       'OCREngine': OCREngine,
                       }
            r = requests.post('https://api.ocr.space/parse/image',
                              files={'filename': ('image.png', img_byte_arr)},
                              data=payload)
            
            return r.json()  # Повертаємо JSON-відповідь

        def extract_parsed_text(result):
            if "ParsedResults" in result:
                full_text = ""
                for parsed_result in result["ParsedResults"]:
                    parsed_text = parsed_result.get("ParsedText", "")
                    if parsed_text:
                        full_text += parsed_text + "\n"
                        
                return full_text.strip()
                print(full_text)
            else:
                return "Розпізнаний текст відсутній."

        # Перетворюємо зображення на чорно-біле
        #bw_image = self.captured_image.convert('L')  # Конвертуємо в градації сірого
        #bw_image = bw_image.point(lambda x: 0 if x < 128 else 255, '1')  # Бінаризація
        
        # Виклик функції OCR
        result = ocr_space_file(self.captured_image, False, 'K85473038888957', 2)
        
        # Витягування тексту
        text_window = extract_parsed_text(result)
        

        if text_window:
            #self.text_output.insert(tk.END, "Зчитаний текст:\n")
            #self.text_output.insert(tk.END, text_window + "\n\n")

            response = co.chat(
                model="command-r-plus",
                message=text_window
            )
            
            self.text_output.insert(tk.END, "Можливі варіанти розв'язку вашої проблеми:\n\n")
            self.text_output.insert(tk.END, response.text + "\n\n")
            self.ask_translation(response.text)
        else:
            self.text_output.insert(tk.END, "Помилка: Не вдалося розпізнати текст з зображення.\n")




    def ask_translation(self, cohere_response):
        self.translate_button.config(state=tk.NORMAL)  # Увімкнути кнопку перекладу

        # Зберігаємо відповідь Cohere для подальшого перекладу
        self.cohere_response = cohere_response

    def translate_response(self):
        detected_lang = detect(self.cohere_response)
        translated_text = self.translate_text(self.cohere_response, detected_lang)
        self.text_output.insert(tk.END, "Перекладений текст:\n\n")
        self.text_output.insert(tk.END, translated_text + "\n\n")


    def translate_text(self, text, source_lang, target_lang='uk'):
        params = {
            "q": text,
            "langpair": f"{source_lang}|{target_lang}"
        }

        if memory_api_key:
            params["de"] = memory_api_key

        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                result = response.json()
                return result['responseData']['translatedText']
            else:
                return f"Error: Неможливо перевести, статус код {response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"Запит відхилено: {e}"

def main():
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
