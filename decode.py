"""Декодирует update.b64 в update.zip и распаковывает его в текущую папку."""
import base64, zipfile, io, sys

with open("update.b64") as f:
    data = base64.b64decode(f.read())

with open("update.zip", "wb") as f:
    f.write(data)

zipfile.ZipFile(io.BytesIO(data)).extractall(".")
print("OK: файл", len(data), "байт, распаковано в текущую папку")
