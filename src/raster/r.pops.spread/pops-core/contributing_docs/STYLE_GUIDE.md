# Contributing to PoPS Core

This guide applies to PoPS Core (the C++ library), but also the
C++ parts of the rpops R package.

## Style guide

### C++ code

The style is inspired by well-defined Python's PEP8, specifically the
subset enforced by Black and for C++ specific items by mix of LLVM and Qt.

#### Formatting

Formatting is managed by _clang-format_ tool. You need to have version 10
to produce results consistent with the current formatting.

Run the formatting on all the files in the top directory:

```sh
clang-format -i include/*/*.hpp tests/*.cpp
```

If you have other versions of _clang-format_ than 10, use:

```sh
clang-format-10 -i include/*/*.hpp tests/*.cpp
```

If it is hard for your to get clang-format or the version 10 directly,
build a Docker image using:

```sh
docker build -t doozyx/clang-format-lint-action "github.com/DoozyX/clang-format-lint-action"
```

Then run the formatting using a Docker container in the top directory:

<!-- markdownlint-disable line-length -->

```sh
docker run --rm --workdir /src -v $(pwd):/src --entrypoint /clang-format/clang-format10 doozyx/clang-format-lint-action -i include/*/*.hpp tests/*.cpp
```

<!-- markdownlint-enable line-length -->

#### Functions and methods

Use underscores to separate words.

For setters use `set_name()`. Don't overuse the `set` prefix, e.g. in
case of `set_open()` it is not clear if just a property is being set
or if some opening action is being performed as a result of the call
(simple `open()` would likely express it better).

For getters use just `name()` like e.g. in Qt.
For getters of boolean properties, it is usually appropriate to
use `is` prefix like in `is_empty()` or `is_open()` especially
when it would not be clear if it refers to an action or property,
e.g. `empty()` versus `is_empty()`.

#### Member variables

Use trailing underscore, i.e. `name_`, or nothing, i.e. `name` for
member variables. No special marking is nice
when used internally but not exposed to the outside
world. However, if you need to distinguish a private member variable
from a getter method or a function parameter name, use trailing
underscore for the private variable.
The underscore, as opposed to using nothing, makes it easier to
distinguish member variables from other variables when reading code
of a method (and `this->` is not used).

Do not use leading underscore, i.e. `_name`, like in Python because that might
be reserved or used by standard library. Do not use leading letter `m`
with or without underscore, i.e. `m_name` or `mname`, because it is
harder to read.
The trailing underscore is the closest thing to Python's marking of
private members.

### Documentation

Don't document obvious things like in "this line assigns a variable"
but keep in mind that people unfamiliar with C++ will read or even use
or change the code, so point out some things which might be obvious to
a C++ developer, but are unexpected coming from a different programming
language, for example that a function parameter which is not a pointer
or reference actually copies the whole object.
