#!/usr/bin/env python

"""
MODULE:       v.mapcalc
AUTHOR(S):    Thomas Leppelt, Soeren Gebbert, Thünen Institut Germany,

PURPOSE:      Vector map algebra
COPYRIGHT:    (C) 2013-2015 by the GRASS Development Team

              This program is free software under the GNU General
              Public License (>=v2). Read the file COPYING that
              comes with GRASS for details.
"""

# %module
# % description: Vector map calculator.
# % keyword: vector
# % keyword: algebra
# % overwrite: yes
# %end
# %option
# % key: expression
# % type: string
# % description: Expression to evaluate
# % key_desc: expression
# % required: yes
# %end


import sys
import re
import os
from grass.script import core as grass
import grass.pygrass.modules as mod


class CmdMapList(object):
    """Listing and execution of PyGRASS module objects"""

    def __init__(self):
        self.exec_list = []

    # Execute command list.

    def exec_cmd_list(self):
        for cmd in self.exec_list:
            cmd.run()
            if cmd.popen.returncode != 0:
                grass.ScriptError(
                    "Error starting %s : \n%s" % (cmd.get_bash(), cmd.popen.stderr)
                )

    # Print command list.

    def get_cmd_list(self):
        print((self.exec_list))

    # Add new command to list.

    def add_cmd(self, newcmd):
        self.exec_list.append(newcmd)


class VectorAlgebraLexer(object):
    """!Lexical analyzer for the GRASS GIS vector algebra"""

    # Buffer functions from v.buffer
    vector_buff_functions = {
        "buff_p": "BUFF_POINT",
        "buff_l": "BUFF_LINE",
        "buff_a": "BUFF_AREA",
    }

    # This is the list of token names.
    tokens = (
        "INT",
        "FLOAT",
        "LPAREN",
        "RPAREN",
        "COMMA",
        "EQUALS",
        "SYMBOL",
        "NAME",
        "AND",  # v.overlay
        "NOT",  # v.overlay
        "OR",  # v.overlay
        "XOR",  # v.overlay
        "DISOR",  # v.patch
    )

    # Build the token list
    tokens = tokens + tuple(vector_buff_functions.values())

    # Regular expression rules for simple tokens
    t_LPAREN = r"\("
    t_RPAREN = r"\)"
    t_COMMA = r","
    t_EQUALS = r"="
    t_AND = r"&"
    t_NOT = r"\~"
    t_OR = r"\|"
    t_XOR = r"\^"
    t_DISOR = r"\+"

    # These are the things that should be ignored.
    t_ignore = " \t"

    def __init__(self):
        self.name_list = {}

    # Read in a float. This rule has to be done before the int rule.
    def t_FLOAT(self, t):
        r"-?\d+\.\d*(e-?\d+)?"
        t.value = float(t.value)
        return t

    # Read in an int.
    def t_INT(self, t):
        r"-?\d+"
        t.value = int(t.value)
        return t

    # Ignore comments.
    def t_comment(self, t):
        r"[#][^\n]*"
        pass

    # Track line numbers.
    def t_newline(self, t):
        r"\n+"
        t.lineno += len(t.value)

    # Parse symbols
    def t_SYMBOL(self, t):
        r"[a-zA-Z_][a-zA-Z_0-9]*"
        # Check for reserved words
        if t.value in list(VectorAlgebraLexer.vector_buff_functions.keys()):
            t.type = VectorAlgebraLexer.vector_buff_functions.get(t.value)
        else:
            t.type = "NAME"
            self.name_list[t.value] = t.value
        return t

    # Handle errors.
    def t_error(self, t):
        raise SyntaxError("syntax error on line %d near '%s'" % (t.lineno, t.value))

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Just for testing
    def test(self, data):
        self.name_list = {}
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)


class VectorAlgebraParser(object):
    """This is the vector algebra parser class"""

    # Get the tokens from the lexer class
    tokens = VectorAlgebraLexer.tokens

    # Setting equal precedence level for boolean operations.
    precedence = (("left", "AND", "OR", "NOT", "XOR", "DISOR"),)  # 1

    def __init__(self, pid=None, run=True, debug=False):
        self.run = run
        self.debug = debug
        self.pid = pid
        self.lexer = VectorAlgebraLexer()
        self.lexer.build()
        # Intermediate vector map names
        self.names = {}
        # Count map names
        self.count = 0
        self.parser = yacc.yacc(module=self)
        # Create empty command list object
        self.cmdlist = CmdMapList()

    def parse(self, expression):
        self.count = 0
        self.parser.parse(expression)

    def generate_vector_map_name(self):
        """!Generate an unique intermediate vector map name
        and register it in the objects map list for later removement.

        The vector map names are unique between processes. Do not use the
        same object for map name generation in multiple threads.
        """
        self.count += 1
        if self.pid is not None:
            pid = self.pid
        else:
            pid = os.getpid()
        name = "tmp_vect_name_%i_%i" % (pid, self.count)
        self.names[name] = name
        # print(name)
        return name

    def p_statement_assign(self, t):
        """
        statement : NAME EQUALS expression
                  | NAME EQUALS name
                  | NAME EQUALS paren_name
        """
        # We remove the invalid vector name from the list
        if t[3] in self.names:
            self.names.pop(t[3])

        # We rename the resulting vector map
        if self.debug:
            print("g.rename vector=%s,%s" % (t[3], t[1]))

        if self.run:
            m = mod.Module(
                "g.rename", vector=(t[3], t[1]), overwrite=grass.overwrite(), run_=False
            )
            self.cmdlist.add_cmd(m)
        self.remove_intermediate_vector_maps()

    def remove_intermediate_vector_maps(self):
        if self.debug:
            for name in self.names:
                print("g.remove type=vector name=%s -f" % (name))
        if self.run:
            for name in self.names:
                m = mod.Module(
                    "g.remove", type="vector", name=name, flags="f", run_=False
                )
                self.cmdlist.add_cmd(m)

    def p_bool_and_operation(self, t):
        """
        expression : name AND name
                   | expression AND name
                   | name AND expression
                   | expression AND expression
                   | name OR name
                   | expression OR name
                   | name OR expression
                   | expression OR expression
                   | name XOR name
                   | expression XOR name
                   | name XOR expression
                   | expression XOR expression
                   | name NOT name
                   | expression NOT name
                   | name NOT expression
                   | expression NOT expression
                   | name DISOR name
                   | expression DISOR name
                   | name DISOR expression
                   | expression DISOR expression
        """

        # Generate an intermediate name
        name = self.generate_vector_map_name()

        # Assign ids to expressions, names and operators.
        firstid = 1
        secondid = 3
        operatorid = 2

        # Define operation commands.
        if t[operatorid] == "&":
            if self.debug:
                print(
                    "v.overlay operator=and ainput=%s binput=%s output=%s"
                    % (t[firstid], t[secondid], name)
                )

            if self.run:
                m = mod.Module(
                    "v.overlay",
                    operator="and",
                    ainput=t[firstid],
                    binput=t[secondid],
                    output=name,
                    run_=False,
                )
                self.cmdlist.add_cmd(m)
            t[0] = name

        elif t[operatorid] == "|":
            if self.debug:
                print(
                    "v.overlay operator=or ainput=%s binput=%s output=%s"
                    % (t[firstid], t[secondid], name)
                )

            if self.run:
                m = mod.Module(
                    "v.overlay",
                    operator="or",
                    ainput=t[firstid],
                    binput=t[secondid],
                    output=name,
                    run_=False,
                )
                self.cmdlist.add_cmd(m)
            t[0] = name

        elif t[operatorid] == "^":
            if self.debug:
                print(
                    "v.overlay operator=xor ainput=%s binput=%s output=%s"
                    % (t[firstid], t[secondid], name)
                )

            if self.run:
                m = mod.Module(
                    "v.overlay",
                    operator="xor",
                    ainput=t[firstid],
                    binput=t[secondid],
                    output=name,
                    run_=False,
                )
                self.cmdlist.add_cmd(m)
            t[0] = name

        elif t[operatorid] == "~":
            if self.debug:
                print(
                    "v.overlay operator=not ainput=%s binput=%s output=%s"
                    % (t[firstid], t[secondid], name)
                )

            if self.run:
                m = mod.Module(
                    "v.overlay",
                    operator="not",
                    ainput=t[firstid],
                    binput=t[secondid],
                    output=name,
                    run_=False,
                )
                self.cmdlist.add_cmd(m)
            t[0] = name

        elif t[operatorid] == "+":
            patchinput = t[firstid] + "," + t[secondid]
            if self.debug:
                print("v.patch input=%s output=%s" % (patchinput, name))

            if self.run:
                m = mod.Module("v.patch", input=patchinput, output=name, run_=False)
                self.cmdlist.add_cmd(m)
            t[0] = name

    def p_buffer_operation(self, t):
        """
        expression : buff_function LPAREN name COMMA number RPAREN
                   | buff_function LPAREN expression COMMA number RPAREN
        """
        # Generate an intermediate name
        name = self.generate_vector_map_name()

        # Assign ids to expressions, names and operators.
        mapid = 3
        operatorid = 5

        if t[1] == "buff_p":
            if self.debug:
                print(
                    "v.buffer input=%s type=point distance=%g output=%s"
                    % (t[mapid], t[operatorid], name)
                )

            if self.run:
                m = mod.Module(
                    "v.buffer",
                    type="point",
                    input=t[mapid],
                    distance=float(t[operatorid]),
                    output=name,
                    run_=False,
                )
                self.cmdlist.add_cmd(m)
            t[0] = name
        elif t[1] == "buff_l":
            if self.debug:
                print(
                    "v.buffer input=%s type=line distance=%g output=%s"
                    % (t[mapid], t[operatorid], name)
                )

            if self.run:
                m = mod.Module(
                    "v.buffer",
                    type="line",
                    input=t[mapid],
                    distance=float(t[operatorid]),
                    output=name,
                    run_=False,
                )
                self.cmdlist.add_cmd(m)
            t[0] = name
        elif t[1] == "buff_a":
            if self.debug:
                print(
                    "v.buffer input=%s type=area distance=%g output=%s"
                    % (t[mapid], t[operatorid], name)
                )

            if self.run:
                m = mod.Module(
                    "v.buffer",
                    type="area",
                    input=t[mapid],
                    distance=float(t[operatorid]),
                    output=name,
                    run_=False,
                )
                self.cmdlist.add_cmd(m)
            t[0] = name

    def p_paren_expr(self, t):
        """expression : LPAREN expression RPAREN"""
        t[0] = t[2]

    def p_number_int(self, t):
        """number : INT"""
        t[0] = t[1]

    def p_number_float(self, t):
        """number : FLOAT"""
        t[0] = t[1]

    def p_name(self, t):
        """name : NAME
        | SYMBOL
        """
        t[0] = t[1]

    def p_paren_name(self, t):
        """paren_name : LPAREN NAME RPAREN
        | LPAREN SYMBOL RPAREN
        """
        t[0] = t[2]

    def p_buff_function(self, t):
        """buff_function    : BUFF_POINT
        | BUFF_LINE
        | BUFF_AREA
        """
        t[0] = t[1]

    # Error rule for syntax errors.
    def p_error(self, t):
        raise SyntaxError("invalid syntax")


def main():
    expression = options["expression"]

    p = VectorAlgebraParser(run=True, debug=False)
    p.parse(expression)
    p.cmdlist.get_cmd_list()
    p.cmdlist.exec_cmd_list()


if __name__ == "__main__":
    options, flags = grass.parser()

    try:
        import ply.lex as lex
        import ply.yacc as yacc
    except ImportError as error:
        grass.fatal("You need to install Python PLY: {}".format(error))

    sys.exit(main())
