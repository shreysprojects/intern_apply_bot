'''
THE safety test: this project must contain no code that submits an application.

The user's standing rule is "fill, but never submit". Unlike the LinkedIn bot
(which needed a guard in front of an upstream submit click), this project is
built with no submit action at all - and this test keeps it that way. It fails
if any interaction call (click/press/tap/check/dispatch_event/evaluate) is
added whose call chain mentions "submit" in any string.
'''

import ast
import os

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INTERACTION_METHODS = {
    "click", "dblclick", "press", "tap", "check", "set_checked",
    "dispatch_event", "evaluate", "evaluate_handle", "eval_on_selector",
}


def _project_py_files():
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ("venv", "tests", "__pycache__", ".git")]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(root, name)


def _strings_in(node):
    return [
        n.value.lower() for n in ast.walk(node)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]


def test_no_interaction_ever_targets_submit():
    offenders = []
    for path in _project_py_files():
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if node.func.attr not in INTERACTION_METHODS:
                continue
            if any("submit" in s for s in _strings_in(node)):
                offenders.append(f"{os.path.relpath(path, PROJECT_ROOT)}:{node.lineno}")
    assert not offenders, (
        "Interaction call(s) target something named 'submit' - this project "
        "must never submit an application: %s" % offenders
    )


def test_no_form_submit_calls():
    '''No direct element.submit() / form.submit() style calls either.'''
    offenders = []
    for path in _project_py_files():
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "submit"):
                offenders.append(f"{os.path.relpath(path, PROJECT_ROOT)}:{node.lineno}")
    assert not offenders, "Found .submit() call(s): %s" % offenders


def test_keyboard_never_presses_enter_in_forms():
    '''Pressing Enter inside a form can submit it. Only Escape is allowed.'''
    offenders = []
    for path in _project_py_files():
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if node.func.attr != "press":
                continue
            for s in _strings_in(node):
                if "enter" in s or "return" in s:
                    offenders.append(f"{os.path.relpath(path, PROJECT_ROOT)}:{node.lineno}")
    assert not offenders, (
        "press() with Enter/Return found - inside a form this can submit: %s" % offenders
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
