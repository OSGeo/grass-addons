# Contributing to PoPS

## Style guide

### C++ code

The style is inspired by well-defined Python's PEP8 and for C++ specific
items by mix of LLVM and Qt.

#### Curly brackets

Put the opening curly bracket on a newline for functions and classes.
This makes the function or class separate from the rest of the code.
Exception are oneliner functions such as setters and getters
where all can be one line.

Loops, if-statements, and namespaces can have the opening bracket on
the same line to save vertical space.

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

For functions with a lot of parameters, long parameter names, or long
type names, write one parameter per line.

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

#### Types

Make the `*` or `&` for pointer or reference a part of the variable type
by putting no space before and one space after, i.e. `Type& value` and
not `Type &value`.

### Documentation

Don't document obvious things like in "this line assigns a variable"
but keep in mind that people unfamiliar with C++ will read or even use
or change the code, so point out some things which might be obvious to
a C++ developer, but are unexpected coming from a different programming
language, for example that a function parameter which is not a pointer
or reference actually copies the whole object.
