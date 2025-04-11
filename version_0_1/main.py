import pyautogui
import tkinter as tk
from tkinter import scrolledtext
import numpy as np
import keyboard
from ttkbootstrap import Style
from pynput import mouse
from PIL import ImageGrab
import os
from PIL import Image
from abc import ABC, abstractmethod
import asyncio
from googletrans import Translator
import easyocr
from paddleocr import PaddleOCR
from manga_ocr import MangaOcr
class OcrBody(ABC):
    @abstractmethod
    def getocrtxt(app, img):
        pass
    @abstractmethod
    def getoklang(app):
        pass
    @abstractmethod
    def setlang(app, language):
        pass
    @abstractmethod
    def checklang():
        pass
class imgutil:
    @staticmethod
    def img2type(img, xtype):
        if os.path.isfile(img):
            img = Image.open(img)
        elif isinstance(img, np.ndarray) and img.ndim == 3 and img.shape[2] in [3, 4]:
            img = Image.fromarray(img)
        elif isinstance(img, Image.Image):
            img = img
        else:
            print('图片不支持')
            return None
        match xtype:
            case 'image':
                return img
            case 'ndarray':
                img_np = np.array(img)
                return img_np
            case _:
                print(f'不能转换到格式{xtype}.')
                return None
class transutil:
    oklang = {
        "English": "en",
        "Chinese(Simplified)": "zh-cn",
        "Chinese(Traditional)": "zh-tw",
        "French": "fr",
        "German": "de",
        "Japanese": "ja",
        "Korean": "ko",
        "Spanish": "es"
    }
    @staticmethod
    async def transtxt(text, srclang='en',tarlang='zh-cn') -> None:
        srclang = transutil.changelang(srclang)
        tarlang = transutil.changelang(tarlang)
        translator = Translator()
        srclang = 'en' if srclang == '' else srclang 
        tarlang = 'zh-cn' if tarlang == '' else tarlang
        translated = await translator.translate(text, src=srclang,dest=tarlang)
        return translated.text
    @staticmethod
    def getoklang():
        return list(transutil.oklang.keys())   
    @staticmethod
    def changelang(language):
        transutil.checklang(language)
        return transutil.oklang[language]  
    @staticmethod
    def checklang(language):
        if language not in transutil.oklang:
            raise ValueError(f"不支持语言'{language}'.")
class EasyOcrBody(OcrBody):
    def __init__(app, language):
        app.oklang = {
            'English': 'en',
            'Chinese(Simplified)': 'ch_sim',
            'Chinese(Traditional)': 'ch_tra',
            'Japanese': 'ja',
            'Korean': 'ko'
        }
        app.checklang(language)
        app.ocr = easyocr.Reader([app.oklang[language]])
    def getocrtxt(app, img):
        img = imgutil.img2type(img, 'ndarray')
        result = app.ocr.readtext(img)
        return ' '.join([line[1] for line in result])
    def getoklang(app):
        return list(app.oklang.keys())
    def setlang(app, language):
        app.checklang(language)
        app.ocr = easyocr.Reader([app.oklang[language]])  
    def checklang(app, language):
        if language not in app.oklang:
            raise ValueError(f"不支持语言'{language}'.")
class MangaOcrBody(OcrBody):
    def __init__(app,language):
        app.oklang = {
            'Japanese': 'japan'
        }
        app.checklang(language)
        app.ocr = MangaOcr()
    def getocrtxt(app, img):
        img = imgutil.img2type(img, 'image')
        return app.ocr(img)
    def getoklang(app):
        return list(app.oklang.keys())
    def setlang(app, language):
        app.checklang(language)  
    def checklang(app, language):
        if language not in app.oklang:
            raise ValueError(f"不支持语言{language}'.")
class PaddleOcrBody(OcrBody):
    def __init__(app, language):
        app.oklang = {
            'English': 'en',
            'Chinese(Simplified)': 'ch',
            'Chinese(Traditional)': 'chinese_cht',
            'Japanese': 'japan',
            'Korean': 'korean',
        }
        app.checklang(language)
        app.ocr = PaddleOCR(use_angle_cls=True, lang=language, max_text_length=1000)
    def getocrtxt(app, img):
        img = imgutil.img2type(img, 'ndarray')
        result = app.ocr.ocr(img, cls=True)
        texts = [line[1][0] for line in result[0]]
        return ' '.join(texts)
    def getoklang(app):
        return list(app.oklang.keys())
    def setlang(app, language):
        app.checklang(language)
        app.ocr = PaddleOCR(use_angle_cls=True, lang=app.oklang[language], max_text_length=1000)
    def checklang(app, language):
        if language not in app.oklang:
            raise ValueError(f"不支持语言'{language}'.")
class OcrContext:
    def __init__(app, body: OcrBody):
        app._body = body
    def setbody(app, body: OcrBody):
        app._body = body
    def getocrtxt(app, img):
        return app._body.getocrtxt(img)
    def getoklang(app):
        return app._body.getoklang()
    def setlang(app, language):
        app._body.setlang(language)
class OcrBodyFactory:
    @staticmethod
    def mkocrbody(ocrtype, language):
        if ocrtype == 'paddleocr':
            return PaddleOcrBody(language)
        elif ocrtype == 'easyocr':
            return EasyOcrBody(language)
        elif ocrtype == 'mangaocr':
            return MangaOcrBody(language)
        else:
            raise ValueError(f"Unsupported OCR type: {ocrtype}")
class ScreenWindow:
    def  __init__(app, tk_root):
        app.tk_root = tk_root
        app.selectwindow = None
        app.canvas = None
    def mkselectwindow(app):
        try:
            selectwindow = tk.Toplevel(app.tk_root)
            selectwindow.attributes('-fullscreen', True)
            selectwindow.attributes('-alpha', 0.3)
            selectwindow.configure(bg='gray')
            selectwindow.overrideredirect(True)
            selectwindow.attributes("-topmost", True)     
            app.selectwindow = selectwindow
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"  
    def createselectcanvas(app):
        try:
            if not app.selectwindow:
                raise Exception('选择不存在')
            screenwidth, screenheight = pyautogui.size()
            canvas = tk.Canvas(app.selectwindow, cursor='cross', width=screenwidth, height=screenheight)
            canvas.pack(fill=tk.BOTH, expand=True)
            app.canvas = canvas
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"
    def canvasdraw(app, xstart, ystart, xend, yend):
        app.canvas.delete("selection")
        app.canvas.create_rectangle(xstart, ystart, xend, yend, outline='red', width=2, tags="selection")
    def selectwindowbreak(app):
        if app.selectwindow:
            app.selectwindow.destroy()
        app.selectwindow = None
        app.canvas = None
class TranslationWindow:
    selectlang = {
        "Chinese(Simplified)": "Chinese(Simplified)",
        "Chinese(Traditional)":'Chinese(Traditional)',
        "English": "English",
        "Japanese": "Japanese",
        "Korean": "Korean"
    }
    def __init__(app):
        app.root = tk.Tk()
        app.style = Style(theme='journal')
        TOP6 = app.style.master
        app.root.title("xuwithbean")
        app.root.geometry("450x600")
        app.root.protocol("WM_DELETE_WINDOW", app.closing)
        app.root.attributes("-topmost", True)
        app.stopflag = False
        app.ctrlclick = False
        app.initselectwindow = False
        app.ismanga = tk.BooleanVar(value=False)
        app.issrclang = tk.StringVar(value='English')
        app.issrclang.trace_add("write", app.langchanging)
        app.istarlang = tk.StringVar(value='Chinese(Simplified)')
        app.txtarea = scrolledtext.ScrolledText(app.root, wrap=tk.WORD)
        app.txtarea.pack(expand=True, fill='both', padx=5, pady=5)
        app.createdownbutton()
        app.createlangselect()
        app.screenwindow = ScreenWindow(app.root)
        app.ocrbody = OcrBodyFactory.mkocrbody('easyocr', app.issrclang.get())
        app.ocrcontext = OcrContext(app.ocrbody)
        app.mouselisten = mouse.Listener(on_click=app.mouseclick, on_move=app.mousemove)
        app.mouselisten.start()
        keyboard.add_hotkey('ctrl+alt', app.mkselectwindow)
        keyboard.add_hotkey('esc', app.closingselectwindow)
    def createdownbutton(app):
        buttonframe = tk.Frame(app.root)
        buttonframe.pack(fill='x', pady=5, side='bottom')
        app.switchbut = tk.Checkbutton(buttonframe, text="漫画模式", variable=app.ismanga, command=app.switchchanging)
        app.clcbut = tk.Button(buttonframe, text="清除", command=app.clctxt)
        app.clcbut.pack(side='left', padx=5)
    def createlangselect(app):
        langframe = tk.Frame(app.root)
        langframe.pack(fill='x', pady=5, side='bottom')
        srcframe = tk.Frame(langframe)
        srcframe.pack(side='left', padx=5, fill='y')
        app.srclabel = tk.Label(srcframe, text="原语言:")
        app.srclabel.pack(anchor='w')
        app.srcmenu = tk.OptionMenu(srcframe, app.issrclang, *TranslationWindow.selectlang.keys())
        app.srcmenu.pack(anchor='w')
        tarframe = tk.Frame(langframe)
        tarframe.pack(side='right', padx=5, fill='y')
        app.tarlabel = tk.Label(tarframe, text="目标语言:")
        app.tarlabel.pack(anchor='e')
        app.tarmenu = tk.OptionMenu(tarframe, app.istarlang, *TranslationWindow.selectlang.keys())
        app.tarmenu.pack(anchor='e')
    def mouseclick(app, x, y, button, pressed):
        if button == mouse.Button.left:
            if keyboard.is_pressed('ctrl') and pressed:
                if not app.initselectwindow:
                    return
                app.xstart, app.ystart = x, y
                app.ctrlclick = True
                print(f'Init xstart:{app.xstart},ystart:{app.ystart}')
            else:
                if not app.ctrlclick:
                    return
                app.xend, app.yend = x, y
                app.ctrlclick = False
                app.screenwindow.selectwindowbreak()
                srclangkey = app.issrclang.get()
                tarlangkey = app.istarlang.get()
                if srclangkey == tarlangkey:
                    app.wrttxt("不要选择相同语言")
                    return
                ocr_text = app.getocrtxt()
                transtxt = asyncio.run(transutil.transtxt(ocr_text, srclangkey, tarlangkey))
                app.wrttxt(f"[原文本]: {ocr_text}")
                app.wrttxt(f"[翻译]: {transtxt}") 
                app.xstart, app.ystart, app.xend, app.yend = None, None, None, None
    def getocrtxt(app, languages = []):
        try:
            app.xstart, app.xend = sorted([app.xstart, app.xend])
            app.ystart, app.yend = sorted([app.ystart, app.yend])
            screenshot = ImageGrab.grab(bbox=(app.xstart, app.ystart, app.xend, app.yend))
            screenshot_np = np.array(screenshot)
            text = app.ocrcontext.getocrtxt(screenshot_np)
            return text
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"
    def mousemove(app, x, y):
        if app.ctrlclick:
            app.screenwindow.canvasdraw(app.xstart, app.ystart, x, y)
    def clctxt(app):
        app.txtarea.delete(1.0, tk.END)
    def wrttxt(app, text):
        app.txtarea.insert(tk.END, text + '\n\n')
        app.txtarea.see(tk.END)
    def closingselectwindow(app):
        if app.screenwindow:
            app.screenwindow.selectwindowbreak()
            app.initselectwindow = False
    def mkselectwindow(app):
        if app.initselectwindow:
            app.closingselectwindow()
            return
        app.screenwindow.mkselectwindow()
        app.screenwindow.createselectcanvas()
        app.initselectwindow = True
    def langchanging(app, *args):
        srclang = app.issrclang.get()
        print(f"源语言改变({srclang}).")
        if srclang == 'Japanese':
            app.switchbut.pack(side='right', padx=5)
        else:
            app.switchbut.pack_forget()
            app.ismanga.set(False)
        app.ocrbody = OcrBodyFactory.mkocrbody('easyocr', srclang)
        app.ocrcontext.setbody(app.ocrbody)  
    def switchchanging(app):
        is_checked = app.ismanga.get()
        srclang = app.issrclang.get()
        
        if srclang != 'Japanese' and is_checked:
            print(f"漫画模式只支持日文")
            return  
        if not is_checked:
            app.ocrbody = OcrBodyFactory.mkocrbody('easyocr', srclang)
        else:
            app.ocrbody = OcrBodyFactory.mkocrbody('mangaocr', srclang)
        app.ocrcontext.setbody(app.ocrbody)
    def closing(app):
        app.stopflag = True
        app.closingselectwindow()
        app.mouselisten.stop()
        app.root.destroy()
    def satrt(app):
        app.root.mainloop()
def main():
    app = TranslationWindow()
    app.satrt()
if __name__ == "__main__":
    main()