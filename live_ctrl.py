#!/usr/bin/python
# -*- coding: utf-8 -*

import cgi
import cgitb
cgitb.enable()

form = cgi.FieldStorage()
print("Content-type: text/html; charset=utf-8\n")

# print(form.getvalue("name"))

html_hdr="""<!DOCTYPE html>
<head>
    <title>Fluid Live Controller</title>
</head>
<body>"""

html_body="""
    <form action="/live_ctrl.py" method="post">
        <input type="text" name="name" value="Votre nom" />
        <input type="submit" name="send" value="Envoyer information au serveur" >
        <input type=checkbox name="item" value="1" >
        <select name="list">
            <option value = "1">Toto</option>
            <option value = "2">Titi</option>
        </select>
    </form>"""
html_ftr="""
</body>
</html>
"""

print(html_hdr + html_body + html_ftr)
