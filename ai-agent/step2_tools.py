"""步驟 2：寫出第一批工具（環境），先用手呼叫。

重點：工具就是普通的 Python 函式，規則只有兩條：
  1. 輸入是一個字串（Action 括號裡的參數）
  2. 輸出也是一個字串（Observation）
因為 LLM 只看得懂文字，所以工具的結果一定要轉成文字。

這一步還沒有 LLM 參與。

執行：python step2_tools.py
"""

import ast
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "subject" / "cart.py" #被測試的程式

def _load():
    """讀入 cart.py，解析成語法樹（AST），方便找出函式與類別。"""
    source = MODULE_PATH.read_text(encoding="utf-8")
    return source, ast.parse(source)


def _find(name):
    """依名稱找函式；類別的方法用 "Cart.total" 的寫法。找不到回傳 None。"""
    _, tree = _load()
    nodes, node = tree.body, None
    for part in name.strip().split("."):
        node = next((n for n in nodes
                     if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part),
                    None)
        if node is None:
            return None
        nodes = node.body
    return node


# ---------------- 工具 1：list_functions[] ----------------
def list_functions(arg=""):
    """列出模組中所有函式與方法的名稱和參數。"""
    _, tree = _load()
    lines = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            lines.append(f"def {node.name}({ast.unparse(node.args)})")
        elif isinstance(node, ast.ClassDef):
            lines.append(f"class {node.name}:")
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    lines.append(f"    def {sub.name}({ast.unparse(sub.args)})")
    return "\n".join(lines)


# ---------------- 工具 2：read_spec[NAME] ----------------
def read_spec(name):
    """只回傳規格（docstring），不回傳程式碼。"""
    node = _find(name)
    if node is None:
        # 找不到時也要回傳「有用的」文字，讓模型知道下一步可以怎麼做
        return f"Could not find {name!r}. Use list_functions[] to see the names."
    return ast.get_docstring(node) or f"{name} has no docstring."


# ---------------- 工具 3：read_source[NAME] ----------------
def read_source(name):
    """回傳實作的原始碼（包含 docstring）。"""
    node = _find(name)
    if node is None:
        return f"Could not find {name!r}. Use list_functions[] to see the names."
    source, _ = _load()
    return ast.get_source_segment(source, node)


# 動作名稱 -> 函式。之後 agent 會用這張表，把模型寫的 Action 對應到真正的函式。
TOOLS = {
    "list_functions": list_functions,
    "read_spec": read_spec,
    "read_source": read_source,
}