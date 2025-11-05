from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Preformatted, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import os

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
input_path = os.path.join(project_root, 'database_preview.txt')
output_path = os.path.join(project_root, 'database_preview.pdf')

if not os.path.exists(input_path):
    raise FileNotFoundError(f"Input file not found: {input_path}")

with open(input_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Create a monospace style for Preformatted text
code_style = ParagraphStyle(
    name='Code',
    fontName='Courier',
    fontSize=8,
    leading=9,
)

# Build PDF
doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
elements = []

# Preformatted preserves whitespace and monospace layout
elements.append(Preformatted(text, code_style))

doc.build(elements)
print(f"Saved PDF to {output_path}")
