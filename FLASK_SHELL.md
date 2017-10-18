
$ flask shell

>>> ctx = app.test_request_context()
>>> ctx.push()
>>> app.preprocess_request()
