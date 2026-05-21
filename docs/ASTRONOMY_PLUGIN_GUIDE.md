# Astronomy Plugin Guide

The Astronomy plugin is located at:

```text
src/plugins/astronomy/plugin.py
```

It supports the same actions as every tutor plugin:

- explain
- hint
- practice
- grade

## How it works

The router sends astronomy questions to this plugin when the subject is set to `astronomy` or when the student's message contains keywords like:

- planet
- star
- galaxy
- redshift
- telescope
- Kepler
- H-R diagram
- black hole

## How to add more astronomy topics

Open `src/plugins/astronomy/plugin.py` and add another branch inside `explain()`.

Example:

```python
elif "moon phases" in text:
    message = (
        "Moon phases happen because we see different portions of the Moon's sunlit half "
        "as the Moon orbits Earth."
    )
```

Then add keywords to the `keywords` list if needed.

## How to improve grading

The current grader checks for important vocabulary. Later you can replace it with:

- Rubric-based grading
- LLM grading
- Multiple-choice answer keys
- Saved practice question IDs
