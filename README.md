# flake8_private_name_import
flake8 plugin that reports imports of private names. 

# documentation is soon
I will prepare documentation for the plugin soon but for now you may check 
[tests](https://github.com/rows-s/flake8_private_name_import/blob/master/flake8_private_name_import_test.py).
They have examples of what it will report and what options are available, and they are easy to read:
```python
    TestCase(
        'from module.sub_module import _function, _variable',
        {
            '1:0: PNI001 found import of private name: _function',
            '1:0: PNI001 found import of private name: _variable',
        },
    ),
```
