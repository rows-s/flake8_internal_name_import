# flake8_internal_name_import
flake8 plugin that reports imports of internal names.

# Installation

```text
pip install flake8_intenal_name_import
```

# Purpose

Developers mark they code as internal with leading underscore 
because they don't want to maintain that interfaces as public with guarantee of existence, 
high usability and backward compatibility.

And so you must avoid usage of internal interfaces finding another solution if it is possible. 
But if some member of your team do not follow the rule and keep importing internal names, 
this plugin is probably what you are looking for.  

# Where does plugin look for imports

- Most of the time you would import name in top of the module.
- Less of the time imports will be under if-else-statements (as example - `if sys.version_info`) 
- Even less they will be placed in try-except blocks (`ImportError` usually)
- But if package dependencies was broken into a circular imports, you will use them locally (within functions).

Trying to cover these cases, plugin looks for:
- Module-level imports including `if-elif-else` and `try-except-else-finally` statements with any nesting-level.
- Local imports, but only first-indent level of them, if import places in function and under an `if` it will be skipped.

But skips:
- Imports under `TYPE_CHECKING`. It must not harm your project while it's not used in production.
- Imports in test files and directories; It ofthen required to test some internal parts of code.

# Codes

<details>
  <summary>PNI001 found import of internal name: {name}</summary>

  ```python
  from module import _my_internal_name  # PNI001 found import of internal name: _my_internal_name
  ```

</details>

<details>
  <summary>PNI002 found import of internal module: {module}</summary>

  ```python
  import _module  # PNI002 found import of internal module: _module
  import module._sub_module  # PNI002 found import of internal module: module._sub_module
  ```

</details>

<details>
  <summary>PNI003 found import from internal module: {module}</summary>

  ```python
  from _module import name  # PNI003 found import from internal module: _module
  from module._sub_module import name  # PNI003 found import from internal module: module._sub_module
  ```

</details>

# Options

### Skip names (`PNI001`)

`console`: --internal-name-import-skip-names  
`config_file`: internal_name_import_skip_names  
`type`: comma separated list (list for config_file)

Internal names import of which must not be reported.  
Accepts full path (`module.sub_module._name`) or plain name (`_name`).  
If full path used then only that name from that module would be skipped.  
If plain name used then name would be skipped independent on module it imported from.

Relative modules must be specified as they imported (`.module`, `..module`)

<details>
  <summary>Example (specific name from specific module)</summary>
  
  ```text
  flake8 --internal-name-import-skip-names=module.sub_module._function,module.sub_module._Class
  ```

  ```python
  from module.sub_module import _function, _Class  # both skipped
  # `_CONSTANT` was not specified to be skipped from the module 
  from module.sub_module import _CONSTANT  # PNI001 found import of internal name: _CONSTANT
  ```

</details>

<details>
  <summary>Example (module independent name)</summary>
  
  ```text
  flake8 --internal-name-import-skip-names=_function,_Class
  ```

  ```python
  from module import _function, _Class  # both skipped
  from module.sub_module import _function, _Class  # both skipped
  ```

</details>

### Skip modules (`PNI002`)

`console`: --internal-name-import-skip-modules  
`config_file`: internal_name_import_skip_modules  
`type`: comma separated list (list for config_file)
 
Internal modules import of which must not be reported.  
Affects only imports of modules, imports of names from those modules will be reported.

Relative modules must be specified as they imported (`.module`, `..module`)

<details>
  <summary>Example</summary>
  
  ```text
  flake8 --internal-name-import-skip-modules=_module,module._sub_module
  ```

  ```python
  import _module  # skipped
  import module._sub_module  # skipped
  # but imports of names from the module will be reported
  from _module import name  # PNI003 found import from internal module: _module
  ```

</details>

### Skip names from modules (`PNI003`, `PNI001`)

`console`: --internal-name-import-skip-names-from-modules  
`config_file`: internal_name_import_skip_names_from_modules  
`type`: comma separated list (list for config_file)
 
Comma separated modules imports of internal names from which must not be reported.  
Affects only imports of names from those modules, imports of modules will be reported.

<details>
  <summary>Example</summary>
  
  ```text
  flake8 --internal-name-import-skip-names-from-modules=_module,module._sub_module
  ```

  ```python
  from _module import name  # skipped
  from module._sub_module import _name  # skipped (both internal module and internal name)
  # but imports of the module will be reported
  import _module  # PNI002 found import of internal module: _module
  ```

</details>

### Skip local imports

`console`: --internal-name-import-skip-local  
`config_file`: internal_name_import_skip_local  
`type`: flag
 
When option used, import inside functions will not be reported.

### Skip relative imports

`console`: --internal-name-import-skip-relative  
`config_file`: internal_name_import_skip_relative  
`type`: flag

When option used, relative imports will not be reported.

Plugin can't realize that `_module` and `._module` are the same module even if they are.
If you skip one of them another will be reported.

And it's common case when you have some in-package module 
that shares internal names for in-package-only usage.  
If you are in that case, you may either skip names and modules 
or just disable plugin for relative imports. 
