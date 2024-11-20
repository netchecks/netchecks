import os
import re
from typing import Dict
import logging

from netcheck.validation import evaluate_cel_with_context

logger = logging.getLogger("netcheck.context")

# Regular expression to match and capture the content inside '{{' and '}}'
TEMPLATE_REGEX = re.compile(r"\{\{(.*?)\}\}")


def evaluate_template(template: str, context: Dict) -> str:
    """
    Evaluate a template string e.g. `contextname.key` and return the result of evaluating
    with CEL.

    Args:
        template (str): The template string to be evaluated.
        context (Dict): The context dictionary used for evaluation.

    Returns:
        str: The evaluated result converted to string.
    """
    return str(evaluate_cel_with_context(context, template))


def replace_template_in_string(s: str, evaluation_context: Dict) -> str:
    """
    Replace all templates in a given string using the provided evaluation context.

    Args:
        s (str): The input string that may contain templates.
        evaluation_context (Dict): The context dictionary used for evaluation.

    Returns:
        str: The input string with all templates replaced by the output of the evaluate_template function.

    """
    # Extract the group from the regex match and pass to `evaluate_template`.
    return TEMPLATE_REGEX.sub(lambda m: evaluate_template(m.group(1).strip(), evaluation_context), s)


def replace_template(original: Dict, evaluation_context: Dict):
    """
    Recursively replace all templates in the keys and values of a dictionary
    using the provided evaluation context.

    Args:
        original (Dict): The input dictionary that may contain templates in keys and/or values.
        evaluation_context (Dict): The context dictionary used for evaluation.

    Returns:
        Dict: A new dictionary with all templates in keys and values replaced by the output of the evaluate_template function.
    """
    result = {}
    for k, v in original.items():
        if isinstance(v, dict):
            v = replace_template(v, evaluation_context)
        elif isinstance(v, list):
            for i in range(len(v)):
                if isinstance(v[i], dict):
                    v[i] = replace_template(v[i], evaluation_context)
                elif isinstance(v[i], str) and TEMPLATE_REGEX.search(v[i]):
                    v[i] = replace_template_in_string(v[i], evaluation_context)
        elif isinstance(v, str) and TEMPLATE_REGEX.search(v):
            v = replace_template_in_string(v, evaluation_context)

        if isinstance(k, str) and TEMPLATE_REGEX.search(k):
            k = replace_template_in_string(k, evaluation_context)

        result[k] = v

    return result


class LazyFileLoadingDict(dict):
    def __init__(self, directory, *args, **kwargs):
        self.directory = directory
        super().__init__(*args, **kwargs)
        # Pre-populate the dictionary with keys for each file in the directory
        for filename in os.listdir(directory):
            # We'll use None as a placeholder for the file contents
            self[filename] = None

    def __getitem__(self, key):
        filepath = os.path.join(self.directory, key)
        if super().__getitem__(key) is None and os.path.isfile(filepath):
            # If the value is None (our placeholder), replace it with the actual file contents
            with open(filepath, "rt") as f:
                self[key] = f.read()
        return super().__getitem__(key)

    def items(self):
        # Override items() to call __getitem__ for each key
        return [(key, self[key]) for key in self]

