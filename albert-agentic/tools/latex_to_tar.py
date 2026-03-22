import tarfile, io, base64, textwrap, sys, json

def latex_to_tar(latex_source: str) -> str:
    """Creates a gzipped tar archive containing a single file 'document.tex' with the given LaTeX source, and returns the base64‑encoded tar.
    """
    # Ensure the source is bytes
    data = latex_source.encode('utf-8')
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        info = tarfile.TarInfo(name='document.tex')
        info.size = len(data)
        tar.addfile(tarinfo=info, fileobj=io.BytesIO(data))
    tar_bytes = buf.getvalue()
    return base64.b64encode(tar_bytes).decode('utf-8')
