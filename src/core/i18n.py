from __future__ import annotations

# --- Operadores (símbolo <-> palabra ES) ---
OP_SYMBOL2WORD_ES = {
    ">=": "al menos",
    ">": "mayor que",
    "==": "igual a",
    "<=": "como máximo",
    "<": "menor que",
    "!=": "distinto de",
}

# Versión más clara para mostrar en desplegable
OP_SYMBOL2LONGWORD_ES = {
    ">=": "mayor o igual que",
    ">": "mayor que",
    "==": "igual que",
    "<=": "menor o igual que",
    "<": "menor que",
    "!=": "distinto de",
}

# Inverso (texto -> símbolo)
OP_WORD2SYMBOL_ES = {
    "al menos": ">=",
    "mayor o igual que": ">=",
    "mayor que": ">",
    "igual a": "==",
    "igual que": "==",
    "como máximo": "<=",
    "menor o igual que": "<=",
    "menor que": "<",
    "distinto de": "!=",
}

# --- Tipos de regla: nombre legible ES ---
RULE_TITLE_ES = {
    "category_count": "Cantidad de categoría",
    "item_count": "Cantidad de alimento",
    "forbid_allergen": "Prohibir alérgeno",
    "do_not_repeat_consecutive_item": "No repetir alimento en días consecutivos",
}
