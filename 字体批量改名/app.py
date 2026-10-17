from font_renamer.ui.app import FontRenamerApp
from font_renamer.ui.platform import enable_windows_dpi_awareness

def main():
    enable_windows_dpi_awareness()
    FontRenamerApp().mainloop()

if __name__ == "__main__":
    main()
