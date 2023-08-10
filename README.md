# flake8_internal_name_import
flake8 plugin that reports imports of internal names.

# Purpose

Developers mark they code as internal with leading underscore 
because they don't want to maintain that interfaces as public with guarantee of existence, 
high usability and backward compatibility.

And so you must avoid usage of internal interfaces finding another solution if it is possible. 
But if some member of your team do not follow the rule and keep importing internal names, 
this plugin is probably what you are looking for.  

# Codes

<details>
  <summary>INI001 found import of internal name: {name}</summary>

  ```python
  from module import _my_internal_name  # INI001 found import of internal name: _my_internal_name
  ```

</details>

<details>
  <summary>INI002 found import of internal module: {module}</summary>

  ```python
  import _module  # INI002 found import of internal module: _module
  import module._sub_module  # INI002 found import of internal module: module._sub_module
  ```

</details>

<details>
  <summary>INI003 found import from internal module: {module}</summary>

  ```python
  from _module import name  # INI003 found import from internal module: _module
  from module._sub_module import name  # INI003 found import from internal module: module._sub_module
  ```

</details>

# Plugin skips some code

Skips test files:
- It is often necessary to import internal name to properly test code.
- It will never hurt you project if test fail after update of used internal interfaces.

Skips TYPE_CHECKING:
- It's fine to use internal names only for annotations.

Plugin has optional skips:
- [Relative imports](#skip-relative-imports)
- [Local imports](#skip-local-imports)

# How to deal with relative imports

Plugin is not smart enough to realize that `from module.sub_module` and `from .sub_module` 
are import from the same module and so if you skip imports from one module using [skip-names](#skip-names-ini001) or
[skip-names-from-modules](#skip-names-from-modules-ini003-ini001) another import will be reported by Plugin.  
It possible to make Plugin smart enough to realize that but for now it seems unnecessary because:
- It must not be common case and developers should prefer absolute imports.
- That knowledge would apply only for skips of names or modules but if it causes that much pain 
  you would rather turn Plugin off for any relative imports.

Imagine you have `utils` module that contains names which must be used only within that package,
and so they marked as internal and imported as `from .utils import _name`.  
And if you want to keep that strategy but also use the Plugin you have some options:
- Skip names or module as they imported if you have not that many names or modules. 
  And be aware that it applies for any modules with the same name and import depth: 
  - `internal_name_import_skip_names = ['.utils._name']`
  - `internal_name_import_skip_names_from_modules = ['.utils']`
- Or skip relative import at all:
  - `internal_name_import_skip_relative = true`
- Do not use relative imports:
  - Use linter to fix it for you. For example [absolufy-imports](https://github.com/MarcoGorelli/absolufy-imports) 

# Options

### Skip names (`INI001`)

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
  from module.sub_module import _CONSTANT  # INI001 found import of internal name: _CONSTANT
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

### Skip modules (`INI002`)

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
  from _module import name  # INI003 found import from internal module: _module
  ```

</details>

### Skip names from modules (`INI003`, `INI001`)

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
  import _module  # INI002 found import of internal module: _module
  ```

</details>

### Skip local imports

`console`: --internal-name-import-skip-local  
`config_file`: internal_name_import_skip_local  
`type`: flag
 
When option used, import inside functions and methods will not be reported.

### Skip relative imports

`console`: --internal-name-import-skip-relative  
`config_file`: internal_name_import_skip_relative  
`type`: flag

When option used, relative imports will not be reported.
