# -*- python -*-
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2014 INRIA - CIRAD - INRA
#
#       File author(s): Julien Coste <julien.coste@inria.fr>
#
#       File contributor(s):
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################
from openalea.oalab.model.python import PythonModel


def test_run():
    model_src = '''"""input = x=1, y=2
output = result"""
result = x + y
'''
    model = PythonModel(code=model_src)
    assert model is not None
    assert model.outputs == []
    result = model()
    assert model.outputs == 3
    assert result == 3

    result = model.run(4)
    assert result == 6

    result = model.run(1, 1)
    assert result == 2

    result = model(5)
    assert result == 7

    result = model(3, 5)
    assert result == 8

    model.inputs = 5, 6
    result = model()
    assert result == 11


def test_run_list():
    model_src = '''"""input = x, y=[1,2,3]
output = result"""
result = 0
for val in x:
    result += val
for val in y:
    result += val
'''
    model = PythonModel(code=model_src)
    assert model is not None
    assert model.outputs == []
    result = model([4])
    assert model.outputs == 10
    assert result == 10

    result = model.run([5])
    assert result == 11

    result = model.run([1, 1], [1, 1])
    assert result == 4

    result = model([2, 2], [2, 2])
    assert result == 8


def test_run_tuple():
    model_src = '''"""input = x, y=(1,2,3)
output = result"""
result = 0
for val in x:
    result += val
for val in y:
    result += val
'''
    model = PythonModel(code=model_src)
    assert model is not None
    assert model.outputs == []
    result = model([4])
    assert model.outputs == 10
    assert result == 10

    result = model.run([5])
    assert result == 11

    result = model.run([1, 1], [1, 1])
    assert result == 4

    result = model([2, 2], [2, 2])
    assert result == 8

    result = model.run((5,))
    assert result == 11

    result = model.run((1, 1), (1, 1))
    assert result == 4

    result = model((2, 2), [2, 2])
    assert result == 8


def test_recursif():
    model_src = '''"""input = x
output = result"""
result = x + 1
'''
    model = PythonModel(code=model_src)
    result = model(model(model(model(model(1)))))
    assert result == 6
