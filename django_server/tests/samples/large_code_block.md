# Large Code Block Test

## Section 1
This is a test document with a very large code block to verify that our chunking strategy preserves code block integrity.

```python
def large_function_part_1():
    print("This is part 1 of a very long function.")
    # ... more lines to increase size ...
    data = [i for i in range(100)]
    for item in data:
        print(f"Processing item: {item}")
    return True

def large_function_part_2():
    print("This is part 2 of a very long function.")
    # Repeat many lines to reach > 3000 characters
    long_string = """
    This is a very long string that will take up a lot of space.
    We need this to exceed the normal chunk size limit of 2500 characters
    while remaining inside a single code block.
    Let's repeat this content many times.
    """ * 50
    print(long_string)
    return False

def large_function_part_3():
    # Adding even more content
    complex_logic = {
        "key_" + str(i): "value_" + str(i)
        for i in range(50)
    }
    for k, v in complex_logic.items():
        if "25" in k:
            print(f"Found it: {v}")
    return complex_logic
```

## Section 2
Final section after the large code block.
