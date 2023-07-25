import ast
import dataclasses
from typing import Set, Tuple

from flake8_private_name_import import Plugin

@dataclasses.dataclass
class TstCase:
    code: str
    expected_results: Set[Tuple[int, int, str, str]]


test_cases = (
    TstCase(code='import module', expected_results=set()),
    TstCase(code='import module.sub_module', expected_results=set()),
    TstCase(code='from module import allowed_name', expected_results=set()),
    TstCase(code='from module.sub_module import allowed_name', expected_results=set()),
    TstCase(code='from module.sub_module import allowed_name, allowed_name2', expected_results=set()),
    TstCase(code='from module.sub_module import (\nallowed_name,\nallowed_name2\n)', expected_results=set()),
    TstCase(code='from module.sub_module import \\\nallowed_name,\\\nallowed_name2', expected_results=set()),
    TstCase(code='import _module', expected_results={(1, 0, 'PNI001', '_module')}),
    TstCase(code='import module._sub_module', expected_results={(1, 0, 'PNI001', '_sub_module')}),
    TstCase(
        code='import _module._sub_module',
        expected_results={(1, 0, 'PNI001', '_module'), (1, 0, 'PNI001', '_sub_module')},
    ),
    TstCase(code='from module import _private', expected_results={(1, 0, 'PNI001', '_private')}),
    TstCase(code='from module.sub_module import _private', expected_results={(1, 0, 'PNI001', '_private')}),
    TstCase(
        code='from module.sub_module import allowed_name, _private',
        expected_results={(1, 0, 'PNI001', '_private')},
    ),
    TstCase(
        code='from module.sub_module import (\nallowed_name,\n_private\n)',
        expected_results={(1, 0, 'PNI001', '_private')},
    ),
    TstCase(
        code='from module.sub_module import \\\nallowed_name,\\\n_private',
        expected_results={(1, 0, 'PNI001', '_private')},
    ),
    TstCase(code='\n\nimport _module', expected_results={(3, 0, 'PNI001', '_module')}),
)


def test_plugin():
    for test_case in test_cases:
        assert _run_plugin(test_case.code) == test_case.expected_results


def _run_plugin(code: str) -> Set[Tuple[int, int, str, str]]:
    return {(ln, cn, msg[:6], msg.split(': ')[1]) for ln, cn, msg, _ in Plugin(ast.parse(code)).run()}
