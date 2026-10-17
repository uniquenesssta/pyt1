DEFAULT_EXTENSIONS = (".ttf", ".otf", ".woff", ".woff2", ".dfont")
DEFAULT_NAME_IDS = (4, 1, 16, 6)
DEFAULT_LANG_IDS = (0x0804, 0x0404, 0x0C04, 0x0409, 0)

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

STATUS_RENAME = "将重命名"
STATUS_SKIP = "跳过"
STATUS_ERROR = "错误"
STATUS_DONE = "成功"


