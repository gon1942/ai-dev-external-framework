"""Update package bundle.zip after changing template files."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent.parent / 'src/teamdev/assets'
bundle = root / 'bundle.zip'
with ZipFile(bundle, 'w', compression=ZIP_DEFLATED) as z:
    for file in sorted(root.rglob('*')):
        if file.is_file() and file != bundle:
            z.write(file, file.relative_to(root).as_posix())
print(f'Created {bundle}')
