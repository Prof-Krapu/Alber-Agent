import tarfile, io, base64

def latex_to_tar(latex_source: str) -> str:
    """
    Crée une archive tar.gz contenant un fichier document.tex à partir du code LaTeX fourni.
    """
    data = latex_source.encode('utf-8')
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        info = tarfile.TarInfo(name='document.tex')
        info.size = len(data)
        tar.addfile(tarinfo=info, fileobj=io.BytesIO(data))
    tar_bytes = buf.getvalue()
    return base64.b64encode(tar_bytes).decode('utf-8')
