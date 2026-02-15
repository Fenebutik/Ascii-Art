import cv2
import numpy as np
import os
import threading
import json
import webbrowser
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import imageio

class AsciiArtPro:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCII Art Pro")
        self.root.geometry("1300x800")
        self.root.configure(bg='#2b2b2b')
        
        # Палитры
        self.palettes = {
            'Блочная': '█▓▒░ ',
            'Градиентная': '█▇▆▅▄▃▂▁ ',
            'Минимальная': '@ ',
            '3D-стиль': ' .:!/r(l1Z4H9W8$@'
        }
        
        # Символы для направлений
        self.direction_chars = {
            'horizontal': '-',
            'vertical': '|',
            'diag_up': '/',
            'diag_down': '\\',
            'cross': '+'
        }
        
        self.image_path = None
        self.ascii_art = None
        self.ascii_color_data = None
        self.resized_color = None
        self.font_size = 8
        self.stop_flag = False
        self.settings_file = os.path.join(os.path.expanduser("~"), "ascii_art_pro_settings.json")
        self.preview_photo = None
        self.gif_frames = None
        self.is_gif_result = False
        self.gif_original_frames = []  # для хранения кадров оригинального GIF
        self.anim_timer = None
        self.anim_index = 0
        self.ascii_frames = []  # для хранения ASCII-строк (анимация)
        self.ascii_anim_timer = None
        self.ascii_anim_index = 0
        
        # Переменные для хранения настроек
        self.width_var = IntVar(value=150)
        self.palette_var = StringVar(value='3D-стиль')
        self.contrast_var = DoubleVar(value=1.5)
        self.edges_var = BooleanVar(value=True)
        self.use_gradient_var = BooleanVar(value=True)
        self.gradient_threshold_var = IntVar(value=30)
        self.v_compress_var = DoubleVar(value=1.0)
        self.font_size_var = IntVar(value=8)
        self.export_html_var = BooleanVar(value=False)
        
        self.load_settings()
        self.setup_ui()
    
    def load_settings(self):
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.width_var.set(settings.get('width', 150))
                self.palette_var.set(settings.get('palette', '3D-стиль'))
                self.contrast_var.set(settings.get('contrast', 1.5))
                self.edges_var.set(settings.get('edges', True))
                self.use_gradient_var.set(settings.get('use_gradient', True))
                self.gradient_threshold_var.set(settings.get('gradient_threshold', 30))
                self.v_compress_var.set(settings.get('v_compress', 1.0))
                self.font_size_var.set(settings.get('font_size', 8))
                self.export_html_var.set(settings.get('export_html', False))
        except:
            pass
    
    def save_settings(self):
        settings = {
            'width': self.width_var.get(),
            'palette': self.palette_var.get(),
            'contrast': self.contrast_var.get(),
            'edges': self.edges_var.get(),
            'use_gradient': self.use_gradient_var.get(),
            'gradient_threshold': self.gradient_threshold_var.get(),
            'v_compress': self.v_compress_var.get(),
            'font_size': self.font_size_var.get(),
            'export_html': self.export_html_var.get()
        }
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def setup_ui(self):
        main_frame = Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        left_frame = Frame(main_frame, bg='#3c3c3c', relief=RAISED, bd=2)
        left_frame.pack(side=LEFT, fill=Y, padx=(0, 10))
        
        right_frame = Frame(main_frame, bg='#2b2b2b')
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        
        Label(left_frame, text="НАСТРОЙКИ", font=('Arial', 14, 'bold'),
              bg='#3c3c3c', fg='white').pack(pady=(10, 20))
        
        btn_style = {'font': ('Arial', 10), 'bg': '#4CAF50', 'fg': 'white',
                     'activebackground': '#45a049', 'bd': 0, 'padx': 20, 'pady': 10}
        
        Button(left_frame, text="📁 ВЫБРАТЬ ИЗОБРАЖЕНИЕ/ГИФКУ",
               command=self.load_image, **btn_style).pack(pady=(0, 15))
        
        Label(left_frame, text="Ширина ASCII:", bg='#3c3c3c', fg='white').pack(anchor=W, padx=10)
        Scale(left_frame, from_=50, to=300, variable=self.width_var,
              orient=HORIZONTAL, length=200, bg='#3c3c3c', fg='white',
              highlightthickness=0).pack(pady=(0, 15))
        
        Label(left_frame, text="Палитра символов:", bg='#3c3c3c', fg='white').pack(anchor=W, padx=10)
        palette_combo = ttk.Combobox(left_frame, textvariable=self.palette_var,
                                    values=list(self.palettes.keys()), state='readonly',
                                    width=20)
        palette_combo.pack(pady=(0, 15))
        
        self.palette_preview = Label(left_frame, text=self.palettes[self.palette_var.get()],
                                    font=('Courier', 14), bg='black', fg='white', width=25, height=2)
        self.palette_preview.pack(pady=(0, 15))
        palette_combo.bind('<<ComboboxSelected>>', self.update_palette_preview)
        
        Label(left_frame, text="Контрастность:", bg='#3c3c3c', fg='white').pack(anchor=W, padx=10)
        Scale(left_frame, from_=0.5, to=3.0, variable=self.contrast_var,
              orient=HORIZONTAL, length=200, resolution=0.1,
              bg='#3c3c3c', fg='white').pack(pady=(0, 15))
        
        self.edges_var = BooleanVar(value=True)
        Checkbutton(left_frame, text="Обводить границы", variable=self.edges_var,
                   bg='#3c3c3c', fg='white', selectcolor='#3c3c3c').pack(anchor=W, padx=10, pady=5)
        
        self.use_gradient_var = BooleanVar(value=True)
        Checkbutton(left_frame, text="🎯 Контурный стиль (учёт градиента)",
                   variable=self.use_gradient_var, bg='#3c3c3c', fg='white',
                   selectcolor='#3c3c3c').pack(anchor=W, padx=10, pady=5)
        
        Label(left_frame, text="Порог градиента:", bg='#3c3c3c', fg='white').pack(anchor=W, padx=10)
        Scale(left_frame, from_=0, to=100, variable=self.gradient_threshold_var,
              orient=HORIZONTAL, length=200, bg='#3c3c3c', fg='white').pack(pady=(0, 10))
        
        Label(left_frame, text="Сжатие по вертикали (1.0 = без сжатия):",
              bg='#3c3c3c', fg='white').pack(anchor=W, padx=10)
        Scale(left_frame, from_=0.3, to=2.0, resolution=0.1, variable=self.v_compress_var,
              orient=HORIZONTAL, length=200, bg='#3c3c3c', fg='white').pack(pady=(0, 15))
        
        Label(left_frame, text="Размер шрифта в окне:", bg='#3c3c3c', fg='white').pack(anchor=W, padx=10)
        Spinbox(left_frame, from_=4, to=24, textvariable=self.font_size_var, width=10,
                command=self.change_font_size).pack(pady=(0, 15))
        
        self.export_html_var = BooleanVar(value=False)
        Checkbutton(left_frame, text="🌐 Сохранить как цветной HTML",
                   variable=self.export_html_var, bg='#3c3c3c', fg='white',
                   selectcolor='#3c3c3c').pack(anchor=W, padx=10, pady=5)
        
        btn_frame = Frame(left_frame, bg='#3c3c3c')
        btn_frame.pack(pady=10)
        
        Button(btn_frame, text="⚡ СГЕНЕРИРОВАТЬ",
               command=self.generate_ascii, **btn_style).pack(side=LEFT, padx=5)
        
        self.stop_btn = Button(btn_frame, text="⏹ СТОП",
                              command=self.stop_generation, state=DISABLED,
                              bg='#f44336', fg='white', font=('Arial', 10),
                              activebackground='#d32f2f', bd=0, padx=20, pady=10)
        self.stop_btn.pack(side=LEFT, padx=5)
        
        self.btn_save = Button(left_frame, text="💾 СОХРАНИТЬ",
                              command=self.save_ascii, state=DISABLED, **btn_style)
        self.btn_save.pack(pady=10)
        
        self.progress = ttk.Progressbar(left_frame, orient=HORIZONTAL, length=250, mode='determinate')
        self.progress.pack(pady=10)
        
        # Правая панель: контейнер для картинки или текста
        self.right_content = Frame(right_frame, bg='#2b2b2b')
        self.right_content.pack(fill=BOTH, expand=True)
        
        # Виджет для картинки (будет показывать как статичные фото, так и анимацию)
        self.image_label = Label(self.right_content, bg='#1e1e1e', text="Нет изображения")
        
        # Виджет для текста
        self.text_frame = Frame(self.right_content, bg='#1e1e1e')
        self.ascii_text = scrolledtext.ScrolledText(self.text_frame, font=('Courier', self.font_size),
                                                    bg='black', fg='white',
                                                    insertbackground='white',
                                                    wrap=NONE)
        self.ascii_text.pack(fill=BOTH, expand=True)
        
        # Показываем текстовое поле с приветствием
        self.show_text_mode("Выберите изображение и нажмите 'СГЕНЕРИРОВАТЬ'")
        
        self.status_var = StringVar(value="Готов к работе")
        status_bar = Label(self.root, textvariable=self.status_var,
                          bg='#3c3c3c', fg='white', anchor=W, relief=SUNKEN)
        status_bar.pack(side=BOTTOM, fill=X)
    
    def show_image_mode(self, pil_image=None, gif_frames=None):
        """Показывает картинку или анимацию в правой панели, скрывает текст."""
        self.stop_animation()          # останавливаем предыдущую анимацию
        self.stop_ascii_animation()    # останавливаем ASCII-анимацию
        self.text_frame.pack_forget()
        self.image_label.pack(fill=BOTH, expand=True)
        
        if gif_frames is not None:
            # Это анимация
            self.gif_original_frames = gif_frames
            self.anim_index = 0
            self.play_animation()
        elif pil_image is not None:
            # Статичное изображение
            self.preview_photo = ImageTk.PhotoImage(pil_image)
            self.image_label.config(image=self.preview_photo, text="")
    
    def play_animation(self):
        """Воспроизводит следующий кадр GIF."""
        if not self.gif_original_frames:
            return
        frame = self.gif_original_frames[self.anim_index]
        self.preview_photo = ImageTk.PhotoImage(frame)
        self.image_label.config(image=self.preview_photo)
        self.anim_index = (self.anim_index + 1) % len(self.gif_original_frames)
        self.anim_timer = self.root.after(100, self.play_animation)
    
    def stop_animation(self):
        """Останавливает анимацию, если она запущена."""
        if self.anim_timer:
            self.root.after_cancel(self.anim_timer)
            self.anim_timer = None
    
    def play_ascii_animation(self):
        """Воспроизводит следующий кадр ASCII-анимации."""
        if not self.ascii_frames:
            return
        self.ascii_text.delete(1.0, END)
        self.ascii_text.insert(1.0, self.ascii_frames[self.ascii_anim_index])
        self.ascii_anim_index = (self.ascii_anim_index + 1) % len(self.ascii_frames)
        self.ascii_anim_timer = self.root.after(100, self.play_ascii_animation)
    
    def stop_ascii_animation(self):
        """Останавливает ASCII-анимацию."""
        if self.ascii_anim_timer:
            self.root.after_cancel(self.ascii_anim_timer)
            self.ascii_anim_timer = None
    
    def show_text_mode(self, content=None, is_animation=False):
        """Показывает текстовое поле в правой панели, скрывает картинку."""
        self.stop_animation()
        self.stop_ascii_animation()
        self.image_label.pack_forget()
        self.text_frame.pack(fill=BOTH, expand=True)
        if content is not None:
            self.ascii_text.delete(1.0, END)
            self.ascii_text.insert(1.0, content)
        if is_animation and self.ascii_frames:
            self.ascii_anim_index = 0
            self.play_ascii_animation()
    
    def change_font_size(self):
        self.font_size = self.font_size_var.get()
        self.ascii_text.config(font=('Courier', self.font_size))
    
    def update_palette_preview(self, event=None):
        palette = self.palette_var.get()
        if palette in self.palettes:
            self.palette_preview.config(text=self.palettes[palette])
    
    def stop_generation(self):
        self.stop_flag = True
        self.status_var.set("Остановка...")
    
    def load_image(self):
        filename = filedialog.askopenfilename(
            title="Выберите изображение или GIF",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if filename:
            self.image_path = filename
            # Сбрасываем флаги
            self.is_gif_result = False
            self.gif_frames = None
            self.ascii_frames = []
            # Загружаем и показываем
            try:
                img = Image.open(filename)
                if filename.lower().endswith('.gif'):
                    # Это GIF — извлекаем все кадры
                    frames = []
                    try:
                        while True:
                            frame_copy = img.copy().convert('RGB')
                            frame_copy.thumbnail((800, 600))
                            frames.append(frame_copy)
                            img.seek(img.tell() + 1)
                    except EOFError:
                        pass
                    if frames:
                        self.show_image_mode(gif_frames=frames)
                    else:
                        # Если не удалось извлечь кадры, показываем первый как статику
                        img.thumbnail((800, 600))
                        self.show_image_mode(pil_image=img)
                else:
                    # Обычное изображение
                    img.thumbnail((800, 600))
                    self.show_image_mode(pil_image=img)
                
                self.status_var.set(f"Загружено: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить превью: {str(e)}")
                self.show_text_mode(f"Ошибка загрузки {os.path.basename(filename)}")
            self.stop_flag = False
            self.btn_save.config(state=DISABLED)
    
    def generate_ascii(self):
        if not self.image_path:
            messagebox.showwarning("Внимание", "Сначала выберите изображение!")
            return
        
        self.save_settings()
        self.btn_save.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.stop_flag = False
        self.progress['value'] = 0
        self.status_var.set("Генерация...")
        
        thread = threading.Thread(target=self._generate_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_thread(self):
        try:
            width = self.width_var.get()
            palette_name = self.palette_var.get()
            palette = self.palettes.get(palette_name, list(self.palettes.values())[0])
            gamma = self.contrast_var.get()
            use_edges = self.edges_var.get()
            use_gradient = self.use_gradient_var.get()
            grad_thresh = self.gradient_threshold_var.get()
            v_compress = self.v_compress_var.get()
            export_html = self.export_html_var.get()
            
            is_gif = self.image_path.lower().endswith('.gif')
            
            if is_gif:
                self._process_gif(width, palette, gamma, use_edges, use_gradient, grad_thresh, v_compress, export_html)
            else:
                self._process_single_image(width, palette, gamma, use_edges, use_gradient, grad_thresh, v_compress, export_html)
            
            if not self.stop_flag:
                self.root.after(0, self._generation_done)
            else:
                self.root.after(0, self._generation_stopped)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.root.after(0, self._generation_finished)
    
    def _process_single_image(self, width, palette, gamma, use_edges, use_gradient, grad_thresh, v_compress, export_html):
        img = self._load_image(self.image_path)
        if img is None:
            raise ValueError("Не удалось загрузить изображение")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
        gray = cv2.LUT(gray, table)
        gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
        
        if use_edges:
            edges = cv2.Canny(gray, 100, 200)
            kernel = np.ones((2, 2), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)
            gray = cv2.addWeighted(gray, 0.8, edges, 0.2, 0)
        
        height, orig_width = gray.shape
        char_aspect = 2.0
        aspect_ratio = height / orig_width
        new_height = int(width * aspect_ratio / char_aspect * v_compress)
        if new_height < 1:
            new_height = 1
        
        resized = cv2.resize(gray, (width, new_height), interpolation=cv2.INTER_CUBIC)
        
        if use_gradient:
            gx = cv2.Sobel(resized, cv2.CV_64F, 1, 0, ksize=3)
            gy = cv2.Sobel(resized, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(gx**2 + gy**2)
            angle = np.arctan2(gy, gx) * 180 / np.pi
            angle = (angle + 360) % 360
        else:
            magnitude = None
            angle = None
        
        chars = palette
        char_range = len(chars) - 1
        
        ascii_str = ""
        color_data = []
        
        if export_html:
            img_color = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.resized_color = cv2.resize(img_color, (width, new_height), interpolation=cv2.INTER_CUBIC)
        
        for y in range(new_height):
            if self.stop_flag:
                return
            line_chars = []
            line_colors = []
            for x in range(width):
                pixel = resized[y, x]
                
                if use_gradient and magnitude is not None and magnitude[y, x] > grad_thresh:
                    ang = angle[y, x]
                    if (0 <= ang < 22.5) or (157.5 <= ang < 202.5) or (337.5 <= ang < 360):
                        char = self.direction_chars['horizontal']
                    elif (22.5 <= ang < 67.5) or (202.5 <= ang < 247.5):
                        char = self.direction_chars['diag_up']
                    elif (67.5 <= ang < 112.5) or (247.5 <= ang < 292.5):
                        char = self.direction_chars['vertical']
                    elif (112.5 <= ang < 157.5) or (292.5 <= ang < 337.5):
                        char = self.direction_chars['diag_down']
                    else:
                        char = self.direction_chars['cross']
                else:
                    char_index = int(pixel / 255 * char_range)
                    char = chars[char_index]
                
                line_chars.append(char)
                
                if export_html and self.resized_color is not None:
                    r, g, b = self.resized_color[y, x]
                    line_colors.append((r, g, b))
            
            ascii_str += ''.join(line_chars) + "\n"
            if line_colors:
                color_data.append(line_colors)
            
            # Обновление прогресса
            self.root.after(0, lambda val=(y+1)/new_height*100: self.progress.config(value=val))
        
        self.ascii_art = ascii_str
        self.ascii_color_data = color_data if export_html else None
        self.ascii_frames = [ascii_str]  # один кадр
    
    def _process_gif(self, width, palette, gamma, use_edges, use_gradient, grad_thresh, v_compress, export_html):
        try:
            pil_gif = Image.open(self.image_path)
            frames = []
            while True:
                frame_rgb = pil_gif.convert('RGB')
                frame_bgr = cv2.cvtColor(np.array(frame_rgb), cv2.COLOR_RGB2BGR)
                frames.append(frame_bgr)
                try:
                    pil_gif.seek(pil_gif.tell() + 1)
                except EOFError:
                    break
            
            total_frames = len(frames)
            if total_frames == 0:
                raise ValueError("GIF не содержит кадров")
            
            gif_ascii_frames = []
            ascii_strings = []  # для хранения только текста
            
            for idx, frame in enumerate(frames):
                if self.stop_flag:
                    return
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                inv_gamma = 1.0 / gamma
                table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
                gray = cv2.LUT(gray, table)
                gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
                
                if use_edges:
                    edges = cv2.Canny(gray, 100, 200)
                    kernel = np.ones((2, 2), np.uint8)
                    edges = cv2.dilate(edges, kernel, iterations=1)
                    gray = cv2.addWeighted(gray, 0.8, edges, 0.2, 0)
                
                height, orig_width = gray.shape
                char_aspect = 2.0
                aspect_ratio = height / orig_width
                new_height = int(width * aspect_ratio / char_aspect * v_compress)
                if new_height < 1:
                    new_height = 1
                
                resized = cv2.resize(gray, (width, new_height), interpolation=cv2.INTER_CUBIC)
                
                if use_gradient:
                    gx = cv2.Sobel(resized, cv2.CV_64F, 1, 0, ksize=3)
                    gy = cv2.Sobel(resized, cv2.CV_64F, 0, 1, ksize=3)
                    magnitude = np.sqrt(gx**2 + gy**2)
                    angle = np.arctan2(gy, gx) * 180 / np.pi
                    angle = (angle + 360) % 360
                else:
                    magnitude = None
                    angle = None
                
                chars = palette
                char_range = len(chars) - 1
                
                ascii_str = ""
                color_data = []
                
                if export_html:
                    img_color = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    resized_color = cv2.resize(img_color, (width, new_height), interpolation=cv2.INTER_CUBIC)
                
                for y in range(new_height):
                    line_chars = []
                    line_colors = []
                    for x in range(width):
                        pixel = resized[y, x]
                        
                        if use_gradient and magnitude is not None and magnitude[y, x] > grad_thresh:
                            ang = angle[y, x]
                            if (0 <= ang < 22.5) or (157.5 <= ang < 202.5) or (337.5 <= ang < 360):
                                char = self.direction_chars['horizontal']
                            elif (22.5 <= ang < 67.5) or (202.5 <= ang < 247.5):
                                char = self.direction_chars['diag_up']
                            elif (67.5 <= ang < 112.5) or (247.5 <= ang < 292.5):
                                char = self.direction_chars['vertical']
                            elif (112.5 <= ang < 157.5) or (292.5 <= ang < 337.5):
                                char = self.direction_chars['diag_down']
                            else:
                                char = self.direction_chars['cross']
                        else:
                            char_index = int(pixel / 255 * char_range)
                            char = chars[char_index]
                        
                        line_chars.append(char)
                        
                        if export_html and resized_color is not None:
                            r, g, b = resized_color[y, x]
                            line_colors.append((r, g, b))
                    
                    ascii_str += ''.join(line_chars) + "\n"
                    if line_colors:
                        color_data.append(line_colors)
                
                gif_ascii_frames.append((ascii_str, color_data))
                ascii_strings.append(ascii_str)
                progress_val = (idx+1)/total_frames * 100
                self.root.after(0, lambda val=progress_val: self.progress.config(value=val))
            
            self.gif_frames = gif_ascii_frames
            self.ascii_frames = ascii_strings
            self.is_gif_result = True
            self.ascii_art = gif_ascii_frames[0][0]
            self.ascii_color_data = gif_ascii_frames[0][1] if export_html else None
        except Exception as e:
            raise e
    
    def _generation_done(self):
        self.progress['value'] = 100
        self.stop_btn.config(state=DISABLED)
        self.btn_save.config(state=NORMAL)
        self.status_var.set("Готово!")
        # Переключаемся на текстовый режим
        if self.ascii_frames and len(self.ascii_frames) > 1:
            # Это анимация
            self.show_text_mode(is_animation=True)
        else:
            # Статичный текст
            self.show_text_mode(self.ascii_art)
    
    def _generation_stopped(self):
        self.stop_btn.config(state=DISABLED)
        self.status_var.set("Прервано пользователем")
        self.progress['value'] = 0
    
    def _generation_finished(self):
        self.stop_btn.config(state=DISABLED)
    
    def save_ascii(self):
        if not self.ascii_art:
            return
        
        base = os.path.splitext(os.path.basename(self.image_path))[0]
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Если это гифка и есть кадры, предлагаем сохранить анимацию (только при сохранении)
        if self.is_gif_result and self.gif_frames and len(self.gif_frames) > 1:
            choice = messagebox.askyesno("Сохранение анимации",
                                         "Сохранить как анимированный HTML?\n\n"
                                         "Нажмите 'Да' для HTML (цветной, можно открыть в браузере).\n"
                                         "Нажмите 'Нет' для сохранения первого кадра как изображение (TXT или HTML).")
            if choice:
                self._save_animated_html()
                return
            # иначе продолжаем обычное сохранение (первый кадр)
        
        if self.export_html_var.get() and self.ascii_color_data:
            default_name = f"{base}_{now}.html"
            filename = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML", "*.html"), ("Все файлы", "*.*")],
                initialfile=default_name
            )
            if filename:
                self.save_as_html(filename, single=True)
        else:
            default_name = f"{base}_{now}.txt"
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text", "*.txt"), ("Все файлы", "*.*")],
                initialfile=default_name
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.ascii_art)
                self.status_var.set(f"Сохранено: {os.path.basename(filename)}")
                messagebox.showinfo("Успех", "ASCII арт сохранён!")
    
    def _save_animated_html(self):
        base = os.path.splitext(os.path.basename(self.image_path))[0]
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"{base}_animated_{now}.html"
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Все файлы", "*.*")],
            initialfile=default_name
        )
        if not filename:
            return
        
        html_lines = ['<!DOCTYPE html><html><head><meta charset="UTF-8">',
                      '<style>body { background: black; font-family: "Courier New", monospace; font-size: 8px; line-height: 8px; }',
                      '#ascii-container { white-space: pre; }',
                      '</style>',
                      '</head><body>',
                      '<div id="ascii-container"></div>',
                      '<script>']
        
        frames_js = []
        for ascii_str, color_data in self.gif_frames:
            lines = ascii_str.split('\n')
            html_frame = ''
            for y, line in enumerate(lines):
                if y >= len(color_data):
                    html_frame += line + '\n'
                    continue
                for x, ch in enumerate(line):
                    if x < len(color_data[y]):
                        r, g, b = color_data[y][x]
                        html_frame += f'<span style="color: rgb({r},{g},{b});">{ch}</span>'
                    else:
                        html_frame += ch
                html_frame += '\n'
            frame_escaped = html_frame.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
            frames_js.append(frame_escaped)
        
        html_lines.append(f'const frames = [`{frames_js[0]}`')
        for frame in frames_js[1:]:
            html_lines.append(',')
            html_lines.append(f'`{frame}`')
        html_lines.append('];')
        
        html_lines.extend([
            'let currentFrame = 0;',
            'const container = document.getElementById("ascii-container");',
            'function showFrame() {',
            '  container.innerHTML = frames[currentFrame];',
            '  currentFrame = (currentFrame + 1) % frames.length;',
            '}',
            'setInterval(showFrame, 100);',
            '</script></body></html>'
        ])
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_lines))
        
        self.status_var.set(f"Сохранена анимация: {os.path.basename(filename)}")
        if messagebox.askyesno("Открыть", "Открыть анимацию в браузере?"):
            webbrowser.open(filename)
    
    def save_as_html(self, filename, single=False):
        if single:
            html = ['<!DOCTYPE html><html><head><meta charset="UTF-8"><style>',
                    'body { background: black; font-family: "Courier New", monospace; font-size: 8px; line-height: 8px; }',
                    'pre { margin: 0; }',
                    '</style></head><body><pre>']
            
            lines = self.ascii_art.split('\n')
            for y, line in enumerate(lines):
                if y >= len(self.ascii_color_data):
                    break
                html_line = ''
                for x, ch in enumerate(line):
                    if x < len(self.ascii_color_data[y]):
                        r, g, b = self.ascii_color_data[y][x]
                        html_line += f'<span style="color: rgb({r},{g},{b});">{ch}</span>'
                    else:
                        html_line += ch
                html.append(html_line)
            
            html.append('</pre></body></html>')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html))
            
            self.status_var.set(f"Сохранён цветной HTML: {os.path.basename(filename)}")
            messagebox.showinfo("Успех", "Цветной HTML сохранён!")
    
    def _load_image(self, path):
        img = cv2.imread(path)
        if img is None:
            try:
                pil_img = Image.open(path)
                pil_img = pil_img.convert('RGB')
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except:
                return None
        return img

if __name__ == "__main__":
    root = Tk()
    app = AsciiArtPro(root)
    root.mainloop()