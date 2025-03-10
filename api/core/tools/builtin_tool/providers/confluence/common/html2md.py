#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from html.parser import HTMLParser
import json

def extract_language(parameters):
    """从 data-macro-parameters 中提取语言信息"""
    match = re.search(r'language=(\w+)', parameters)
    return match.group(1) if match else 'plaintext'

class ConfluenceHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        # 存储最终 Markdown 的各行
        self.md_lines = []
        # 当前累积的普通文本（或单元格内容）
        self.current_text = ""

        # 代码块相关
        self.in_pre = False
        self.current_code_text = ""
        # 内联代码标记
        self.in_inline_code = False

        # 标题相关
        self.in_heading = False
        self.heading_level = 0

        # 普通表格相关
        self.in_table = False
        self.current_table = []   # 每一项为一行：列表中存放 cell 字典
        self.current_row = []     # 当前行（列表），每个 cell 为字典 {text, cell_type, rowspan, colspan}
        self.in_cell = False      # 正在处理表格单元格
        self.cell_info = None     # 正在构造的单元格信息

        # 代码宏相关（独立的代码块）
        self.in_code_macro = False
        self.code_macro_language = None

        # 标识是否处于代码块宏 table 中（Confluence 中代码块以 table 包裹）
        self.in_code_table = False

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        # 优先处理 table 标签：如果有 data-macro-name="code"，视为代码块宏
        if tag == "table":
            if attr_dict.get("data-macro-name") == "code":
                self.flush_current_text()
                # 切换到代码块宏模式，无论是否嵌套在单元格内
                self.in_code_table = True
                self.in_code_macro = True
                self.code_macro_language = extract_language(attr_dict.get("data-macro-parameters", ""))
                # 后续标签（如 <tbody>, <tr>, <td>）内部忽略，等待 <pre>
                return
            else:
                # 普通表格
                self.flush_current_text()
                self.in_table = True
                self.current_table = []
                return

        # 如果当前处于代码块宏 table 内，但标签不是 <pre>，则忽略其内部标签
        if self.in_code_table and tag != "pre":
            return

        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.flush_current_text()
            self.in_heading = True
            self.heading_level = int(tag[1])
        elif tag == 'p':
            self.flush_current_text()
        elif tag == 'br':
            self.current_text += "\n"
        elif tag == 'pre':
            self.flush_current_text()
            # 若当前处于代码块宏 table，则按代码块处理
            if self.in_code_table:
                self.in_pre = True
                self.current_code_text = ""
                # 如果嵌套在普通表格单元格中，代码块将追加到 cell 文本中
                if self.in_table and self.in_cell:
                    self.cell_info["text"] += f"\n```{self.code_macro_language}\n"
                else:
                    self.md_lines.append(f"\n```{self.code_macro_language}")
                return
            # 普通 pre 标签（可能在表格中或页面中）
            elif self.in_table and self.in_cell:
                self.in_pre = True
                self.current_code_text = ""
                self.table_pre = True
            else:
                self.in_pre = True
                self.current_code_text = ""
                if self.in_code_macro and self.code_macro_language:
                    self.md_lines.append(f"\n```{self.code_macro_language}")
                else:
                    self.md_lines.append("\n```")
        elif tag == 'code':
            # 内联代码
            if not self.in_pre:
                self.current_text += "`"
                self.in_inline_code = True
        elif tag == 'tr':
            if self.in_table:
                self.current_row = []
        elif tag in ['td', 'th']:
            if self.in_table:
                self.in_cell = True
                # 初始化单元格数据，提取 rowspan 与 colspan 属性
                rowspan = int(attr_dict.get("rowspan", "1"))
                colspan = int(attr_dict.get("colspan", "1"))
                self.cell_info = {
                    "text": "",
                    "cell_type": tag,
                    "rowspan": rowspan,
                    "colspan": colspan
                }
        # 其他标签可根据需要扩展

    def handle_data(self, data):
        # 若处于代码块宏 table 中且在 pre 内，则收集代码文本
        if self.in_code_table and self.in_pre:
            self.current_code_text += data
            return

        # 在普通表格单元格内，将文本追加到当前 cell
        if self.in_table and self.in_cell:
            self.cell_info["text"] += data
        elif self.in_pre:
            # 普通 pre 标签处理
            if hasattr(self, "table_pre") and self.table_pre:
                self.cell_info["text"] += data
            else:
                self.current_code_text += data
        else:
            self.current_text += data

    def handle_endtag(self, tag):
        # 如果处于代码块宏 table 中，但标签不是 pre 或 table，则忽略结束标签
        if self.in_code_table and tag not in ['pre', 'table']:
            return

        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            heading_text = self.current_text.strip()
            self.md_lines.append("\n" + ("#" * self.heading_level) + " " + heading_text + "\n")
            self.current_text = ""
            self.in_heading = False
            self.heading_level = 0
        elif tag == 'p':
            self.md_lines.append(self.current_text.strip() + "\n")
            self.current_text = ""
        elif tag == 'code':
            if self.in_inline_code:
                self.current_text += "`"
                self.in_inline_code = False
        elif tag == 'pre':
            if self.in_code_table:
                self.in_pre = False
                # 构造代码块 Markdown格式
                code_block = f"{self.current_code_text}\n```\n"
                if self.in_table and self.in_cell:
                    # 追加到当前单元格中
                    self.cell_info["text"] += code_block
                else:
                    self.md_lines.append(code_block)
                self.current_code_text = ""
            elif hasattr(self, "table_pre") and self.table_pre:
                self.in_pre = False
                self.table_pre = False
            else:
                self.in_pre = False
                self.md_lines.append(self.current_code_text)
                self.md_lines.append("```\n")
                self.current_code_text = ""
        elif tag == 'table':
            if self.in_code_table:
                # 结束代码块宏 table，不生成表格 Markdown
                self.in_code_table = False
                self.in_code_macro = False
                self.code_macro_language = None
                return
            elif self.in_table:
                self.flush_current_text()
                table_md = self.convert_table_to_markdown(self.current_table)
                # 如果当前在表格单元格内，将生成的表格 Markdown 追加到 cell 文本中
                if self.in_table and self.in_cell:
                    self.cell_info["text"] += "\n" + table_md + "\n"
                else:
                    self.md_lines.append("\n" + table_md + "\n")
                self.in_table = False
                self.current_table = []
                return
        elif tag == 'tr':
            if self.in_table:
                if self.current_row:
                    self.current_table.append(self.current_row)
                self.current_row = []
        elif tag in ['td', 'th']:
            if self.in_table and self.in_cell:
                self.current_row.append(self.cell_info)
                self.in_cell = False
                self.cell_info = None

    def flush_current_text(self):
        if self.current_text.strip():
            self.md_lines.append(self.current_text.strip())
            self.current_text = ""

    def convert_table_to_markdown(self, table):
        """
        将解析后的表格数据（list of rows，每行为 cell 字典列表）转换为 Markdown 表格。
        支持 rowspan 与 colspan（采用简单算法逐行填充跨行单元格）。
        """
        if not table:
            return ""
        markdown_table = []
        col_spans = []  # 每一列剩余跨行计数
        num_cols = 0
        for row in table:
            markdown_row = []
            col_index = 0
            # 填充因跨行而空出的单元格
            while col_index < len(col_spans) and col_spans[col_index] > 0:
                markdown_row.append("   ")
                col_spans[col_index] -= 1
                col_index += 1
            for cell in row:
                # 填充前置空白（极端情况）
                while col_index < len(col_spans) and col_spans[col_index] > 0:
                    markdown_row.append("   ")
                    col_spans[col_index] -= 1
                    col_index += 1
                text = cell.get("text", "").strip().replace('\n', ' ')
                rowspan = cell.get("rowspan", 1)
                colspan = cell.get("colspan", 1)
                markdown_row.append(text)
                for _ in range(colspan - 1):
                    markdown_row.append("   ")
                for _ in range(colspan):
                    if col_index < len(col_spans):
                        col_spans[col_index] = rowspan - 1 if rowspan > 1 else 0
                    else:
                        col_spans.append(rowspan - 1 if rowspan > 1 else 0)
                    col_index += 1
            while col_index < len(col_spans) and col_spans[col_index] > 0:
                markdown_row.append("   ")
                col_spans[col_index] -= 1
                col_index += 1
            if not markdown_table:
                num_cols = len(markdown_row)
            row_str = "| " + " | ".join(markdown_row) + " |"
            markdown_table.append(row_str)
        if len(markdown_table) > 1:
            header_sep = "| " + " | ".join(["---"] * num_cols) + " |"
            markdown_table.insert(1, header_sep)
        return "\n".join(markdown_table) + "\n"

    def get_markdown(self):
        self.flush_current_text()
        return "\n".join(self.md_lines)

def main(wiki: str) -> dict:
    parser = ConfluenceHTMLParser()
    parser.feed(wiki)
    markdown_output = parser.get_markdown()
    return {
        "result": markdown_output
    }