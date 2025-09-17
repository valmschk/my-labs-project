
import os
import time
from flask import Flask, request, render_template_string, send_file
from PIL import Image, TiffImagePlugin, JpegImagePlugin
import threading
import queue

app = Flask(__name__)
SUPPORTED_EXT = {'.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx'}

COMPRESSION_MAP = {
    'JPEG': 'Lossy (JPEG)',
    'PNG': 'Deflate (Lossless)', 
    'GIF': 'LZW',
    'BMP': 'None',
    'PCX': 'RLE',
    'TIFF': {
        1: 'None (Uncompressed)',
        2: 'CCITT Group 3',
        3: 'CCITT Group 4', 
        5: 'LZW (Lossless)',
        6: 'JPEG (Lossy)',
        7: 'JPEG (Lossy)',
        8: 'Deflate (Lossless)',
        32773: 'PackBits (Lossless)',
        32946: 'Deflate (Lossless)'
    }
}

MODE_TO_BPP = {
    '1': 1,      # 1-bit pixels, black and white
    'L': 8,      # 8-bit pixels, grayscale
    'P': 8,      # 8-bit pixels, mapped to any other mode using a color palette
    'RGB': 24,   # 3x8-bit pixels, true color
    'RGBA': 32,  # 4x8-bit pixels, true color with transparency mask
    'CMYK': 32,  # 4x8-bit pixels, color separation
    'YCbCr': 24, # 3x8-bit pixels, color video format
    'I': 32,     # 32-bit signed integer pixels
    'F': 32,     # 32-bit floating point pixels
}

class ImageScanner:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.results = []
        self.processed_count = 0
        self.error_count = 0
        
    def get_compression(self, img):
        fmt = img.format.upper() if img.format else 'UNKNOWN'
        
        if fmt == 'TIFF':
            try:
                tag = img.tag_v2.get(TiffImagePlugin.COMPRESSION, 1)
                comp_name = COMPRESSION_MAP['TIFF'].get(tag, f'Unknown (tag {tag})')
                return f"TIFF: {comp_name}"
            except:
                return "TIFF: Unknown compression"
        
        return f"{fmt}: {COMPRESSION_MAP.get(fmt, 'Unknown compression')}"
    
    def get_resolution(self, img):
        try:
            dpi = img.info.get('dpi')
            if dpi and isinstance(dpi, tuple) and len(dpi) >= 2:
                return f"{dpi[0]}×{dpi[1]} DPI"
            return "N/A (метаданные отсутствуют)"
        except:
            return "N/A"
    
    def get_bpp(self, img):
        try:
            bpp = MODE_TO_BPP.get(img.mode)
            if bpp:
                return f"{bpp} бит/пиксель ({img.mode})"
            return f"Unknown mode: {img.mode}"
        except:
            return "Unknown"
    
    def get_jpeg_quant_tables(self, img):
        try:
            if hasattr(img, 'quantization') and img.quantization:
                tables = {}
                for i, table in img.quantization.items():
                    if table and len(table) >= 64:
                        tables[i] = f"Таблица {i}: {len(table)} коэффициентов"
                return tables if tables else "Стандартные таблицы"
            return "Стандартные таблицы"
        except:
            return "Ошибка чтения таблиц"
    
    def get_gif_palette_info(self, img):
        try:
            if img.mode == 'P' and img.format.upper() == 'GIF':
                palette = img.getpalette()
                if palette:
                    color_count = len(palette) // 3
                    return f"{color_count} цветов в палитре"
                return "Палитра не найдена"
            return "Не GIF с палитрой"
        except:
            return "Ошибка чтения палитры"
    
    def get_file_info(self, file_path):
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                file_size = os.path.getsize(file_path)
                
                return {
                    'file': os.path.basename(file_path),
                    'path': file_path,
                    'size_pixels': f"{width}×{height}",
                    'resolution': self.get_resolution(img),
                    'color_depth': self.get_bpp(img),
                    'compression': self.get_compression(img),
                    'format': img.format.upper() if img.format else 'UNKNOWN',
                    'mode': img.mode,
                    'file_size': f"{file_size / 1024:.1f} KB",
                    'quant_tables': self.get_jpeg_quant_tables(img),
                    'gif_palette': self.get_gif_palette_info(img),
                    'error': None
                }
                
        except Exception as e:
            return {
                'file': os.path.basename(file_path),
                'path': file_path,
                'size_pixels': 'Error',
                'resolution': 'Error',
                'color_depth': 'Error',
                'compression': 'Error',
                'format': 'Error',
                'mode': 'Error',
                'file_size': 'Error',
                'quant_tables': 'Error',
                'gif_palette': 'Error',
                'error': str(e)
            }
    
    def scan_worker(self, file_queue, results):
        while not file_queue.empty():
            try:
                file_path = file_queue.get_nowait()
                result = self.get_file_info(file_path)
                results.append(result)
                self.processed_count += 1
                if result['error']:
                    self.error_count += 1
                file_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                self.error_count += 1
                file_queue.task_done()
    
    def scan_folder(self, folder_path, max_files=1000):
        self.results = []
        self.processed_count = 0
        self.error_count = 0
        
        all_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXT:
                    all_files.append(os.path.join(root, file))
                    if len(all_files) >= max_files:
                        break
        
        file_queue = queue.Queue()
        for file_path in all_files:
            file_queue.put(file_path)
        
        threads = []
        for _ in range(min(self.max_workers, len(all_files))):
            thread = threading.Thread(target=self.scan_worker, args=(file_queue, self.results))
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
        
        return self.results

scanner = ImageScanner(max_workers=4)

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Image Metadata Scanner</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1800px; margin: 0 auto; }
        .form-group { margin: 15px 0; }
        .stats { background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0; }
        table { border-collapse: collapse; width: 100%; font-size: 12px; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background: #f0f0f0; position: sticky; top: 0; }
        tr:hover { background: #f9f9f9; }
        .error { color: red; }
        .success { color: green; }
        pre { margin: 2px; font-size: 10px; max-height: 100px; overflow: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📷 Image Metadata Scanner</h1>
        
        <form method="POST">
            <div class="form-group">
                <label for="folder">Путь к папке:</label>
                <input type="text" id="folder" name="folder" value="{{ folder }}" size="60" 
                       placeholder="C:\\Path\\To\\Your\\Images" required>
            </div>
            
            <button type="submit">Сканировать</button>
        </form>

        {% if scan_time %}
        <div class="stats">
            <strong>Статистика сканирования:</strong><br>
            • Папка: {{ folder }}<br>
            • Обработано файлов: {{ processed_count }}<br>
            • Ошибок: {{ error_count }}<br>
            • Время выполнения: {{ scan_time }} секунд
        </div>
        
        {% if rows %}
        <div style="overflow-x: auto;">
            <table>
                <tr>
                    <th>Файл</th>
                    <th>Размер (пиксели)</th>
                    <th>Разрешение (DPI)</th>
                    <th>Глубина цвета</th>
                    <th>Сжатие</th>
                    <th>Формат</th>
                    <th>Размер файла</th>
                    <th>Таблицы квантования</th>
                    <th>Палитра</th>
                </tr>
                {% for row in rows %}
                <tr class="{{ 'error' if row.error }}">
                    <td title="{{ row.path }}">{{ row.file }}</td>
                    <td>{{ row.size_pixels }}</td>
                    <td>{{ row.resolution }}</td>
                    <td>{{ row.color_depth }}</td>
                    <td>{{ row.compression }}</td>
                    <td>{{ row.format }}</td>
                    <td>{{ row.file_size }}</td>
                    <td>{{ row.quant_tables }}</td>
                    <td>{{ row.gif_palette }}</td>
                </tr>
                {% if row.error %}
                <tr class="error">
                    <td colspan="9"><strong>Ошибка:</strong> {{ row.error }}</td>
                </tr>
                {% endif %}
                {% endfor %}
            </table>
        </div>
        {% endif %}
        {% endif %}
    </div>
</body>
</html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    folder = request.form.get('folder', '') if request.method == 'POST' else ''
    
    rows = []
    scan_time = 0
    processed_count = 0
    error_count = 0
    
    if request.method == 'POST' and folder and os.path.isdir(folder):
        start_time = time.time()
        rows = scanner.scan_folder(folder, 1000)
        scan_time = time.time() - start_time
        processed_count = scanner.processed_count
        error_count = scanner.error_count
    
    return render_template_string(
        HTML_TEMPLATE, 
        rows=rows, 
        folder=folder,
        scan_time=round(scan_time, 2),
        processed_count=processed_count,
        error_count=error_count
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
