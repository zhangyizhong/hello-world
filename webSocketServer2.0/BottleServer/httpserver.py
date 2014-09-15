'''
Created on 2014-9-12

@author: Administrator
'''


from bottle import route, run, template, static_file


@route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)


web_home = './Jumpstart.SetTopBox/'
#web_home = './html/'
@route('/<p:path>')
def foo(p):
    return static_file(p, web_home)


run(host='10.86.8.71', port=80)