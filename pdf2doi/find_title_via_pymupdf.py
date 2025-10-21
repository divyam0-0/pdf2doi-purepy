# PDFMiner version of the original PyMuPDF code
# Entry point remains find_title_via_pymupdf

from operator import itemgetter
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTChar

def fonts(file, granularity=False):
    styles = {}
    font_counts = {}

    for page_layout in extract_pages(file):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                for line in element:
                    for char in line:
                        if isinstance(char, LTChar):
                            if granularity:
                                identifier = f"{char.size}_{char.fontname}_{char.ncs}"
                                styles[identifier] = {'size': char.size, 'font': char.fontname, 'color': char.ncs}
                            else:
                                identifier = f"{char.size}"
                                styles[identifier] = {'size': char.size, 'font': char.fontname}

                            font_counts[identifier] = font_counts.get(identifier, 0) + 1

    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")

    return font_counts, styles

def font_tags(font_counts, styles):
    p_style = styles[font_counts[0][0]]  # most used font
    p_size = p_style['size']

    font_sizes = [float(font_size) for font_size, _ in font_counts]
    font_sizes.sort(reverse=True)

    idx = 0
    size_tag = {}
    for size in font_sizes:
        idx += 1
        if size == p_size:
            idx = 0
            size_tag[size] = '<p>'
        if size > p_size:
            size_tag[size] = f'<h{idx}>'
        elif size < p_size:
            size_tag[size] = f'<s{idx}>'

    return size_tag

def headers_para(file, size_tag):
    header_para = []
    first = True
    previous_s = {}

    for page_layout in extract_pages(file):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                block_string = ""
                for line in element:
                    for char in line:
                        if isinstance(char, LTChar):
                            text = char.get_text().strip()
                            if not text:
                                continue

                            if first:
                                previous_s = char
                                first = False
                                block_string = size_tag[char.size] + text
                            else:
                                if char.size == previous_s.size:
                                    if block_string and all((c == "|") for c in block_string):
                                        block_string = size_tag[char.size] + text
                                    elif block_string == "":
                                        block_string = size_tag[char.size] + text
                                    else:
                                        block_string += " " + text
                                else:
                                    header_para.append(block_string)
                                    block_string = size_tag[char.size] + text

                                previous_s = char

                    block_string += "|"

                header_para.append(block_string)

    return header_para

def find_title_via_pymupdf(file):
    font_counts, styles = fonts(file, granularity=False)
    size_tag = font_tags(font_counts, styles)
    elements = headers_para(file, size_tag)
    for e in elements:
        if e.startswith('<h1>'):
            return e.lstrip("<h1>").replace("|", "")
