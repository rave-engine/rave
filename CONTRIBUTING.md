Contributing to rave
=====================

Style guide
-----------

__Naming__
- Classes: upper camel case: `MyClass`
- Functions, methods, variables: lowercase separated by underscores: `read_file`
- Modules: lowercase, no separation characters: `filesystem`
- Constants: full uppercase separated by underscores: `ZIP_MAGIC`
- Use names that are concise but descriptive in their context.
- Prefix functions and variables internal to the module with an underscore. Do not do this for classes.

__Whitespace__
- Indent with 4 spaces per level. Do not indent empty lines.
- Use a single space after a comma.
- Operators (`=`, `+`, `-`, `*`, `/`, `**`, etc.) and compound operators should be surrounded by spaces on both sides.
- Single-line docstring: space between triple quotes and contents.
- Multi-line docstring: newline after opening triple quotes and before ending triple quotes. No extra identation.
- Separate logical groups of code with empty lines
- Separate function, method and class definitions with an empty line, possibly two.
- The newline character is `\n`. No DOS-style `\r\n` newlines.

__Miscellaneous__
- Try to keep a line within 120 characters in width. We don't specify a hard line wrap limit - use common sense.
- (Almost) never use `from ... import *`. Always qualify the names you want to import, if you *have to* use the `from ... import ...` syntax.
  * The test cases are an exception.
- Use import aliases (`import foo.bar.baz as baz`) if you feel name references are becoming too long.
- End a file with a newline.
- Try to section off relevant grouped parts of your code, preferably with a comment header like '## Internals.' or '## API.'


Commit messages
---------------

For quick fixes, a short one-line message is fine. For bigger commits, use the full message to describe what you added and how it works, briefly. Wrap those lines to 78 characters.
Use the imperative form (`Add filesystem module tests.`, `Fix bug #1732.`, etc.) and proper punctuation and capitalisation in your commit messages.

Seperate the distinct changes you make into seperate ('atomic') commits. Don't push a single commit that adds multiple features, or adds a feature and fixes a bug elsewhere, et cetera.

Prefix the first line in your commit message with the subsystem the commit applies to. Valid subsystems are:
  * core: the engine core.
  * modules/*module*: an engine module.
  * common: common asset files.
  * build: the build and test system.
  * tests: unit or integration tests.
  * misc: anything that doesn't fit into the above categories.

An example of a proper full commit message would be "core: Fix crash in rave.events.emit() if registered event callback is not callable.".
