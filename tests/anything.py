from openpyxl import load_workbook
from openpyxl.drawing.image import Image

# 读取 Excel 文件
file_path = '/Users/lei/Downloads/1.xlsx'  # 替换成你的 Excel 文件路径
workbook = load_workbook(file_path)
sheet = workbook.active

# 添加水印图片
watermark_path = '/Users/lei/Downloads/1.png'  # 替换成你的水印图片路径
img = Image(watermark_path)
img.width = 200  # 设置水印宽度
img.height = 100  # 设置水印高度

# 调整水印位置（这里设置为左上角，可以根据需求调整）
sheet.add_image(img, 'A1')

# 保存修改后的 Excel 文件
workbook.save('output_with_watermark.xlsx')  # 替换成你想要保存的文件名
