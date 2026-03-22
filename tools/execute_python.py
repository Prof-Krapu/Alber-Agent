def execute_python(code: str):
    import sys, io, contextlib
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            exec(code, {})
        return {'output': stdout.getvalue()}
    except Exception as e:
        return {'error': str(e)}