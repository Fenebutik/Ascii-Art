import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'Ascii Art.py',
    '--onefile',
    '--windowed',
    '--name=ASCII Art',
    '--icon=icon.ico',
    '--clean',
    '--noconsole',
])