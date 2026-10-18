"""Upgrade untouched defaults and generated text without losing personal edits."""
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS
from scene_tool.domain.prompts import make_prompt


def migrate_prompt_state(state, legacy_constraints):
    result = dict(state)
    if isinstance(state.get("values"), dict):
        result["values"] = dict(state["values"])
        result["values"].setdefault("environment", "室外")
    known_defaults = (legacy_constraints,) if isinstance(legacy_constraints, str) else tuple(legacy_constraints)
    if result.get('constraints') in known_defaults:
        result['constraints'] = DEFAULT_CONSTRAINTS
    # An edited prompt is user content, never silently replace it.
    if isinstance(result.get('prompt'), str) and result['prompt'] == result.get('rendered'):
        try:
            prompt = make_prompt(result.get('values', {}), result.get('industry', '美业'),
                                 result.get('constraints', DEFAULT_CONSTRAINTS),
                                 result.get('copy', ''), result.get('extra', ''))
        except (ValueError, AttributeError, TypeError):
            return result
        result['prompt'] = result['rendered'] = prompt
    return result
