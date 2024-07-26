import numpy as np
import logging as logger
from config import ParserConfig
from tree_sitter_ast import SourceCodeAST
from parsers import ASTParser
from visitor import ASTVisitor


META_TYPES = ["string", "docstring",
              "comment", "class_definition", "function_definition"]


def ast_parser(source_code, lang="guess", **kwargs):
    """
    Parses the AST of source code of most programming languages quickly.

    Parameters
    ----------
    source_code : str
        Source code to parsed as a string. Also
        supports parsing of incomplete source code
        snippets (by deactivating the syntax checker; see syntax_error)
    
    lang : [python, java, javascript, ...]
        String identifier of the programming language
        to be parsed. Supported are most programming languages
        including python, java and javascript (see README)
        Default: guess (Guesses language / Not supported currently throws error currently)
    
    syntax_error : [raise, warn, ignore]
        Reaction to syntax error in code snippet.
        raise:  raises a Syntax Error
        warn:   prints a warning to console
        ignore: Ignores syntax errors. Helpful for parsing code snippets.
        Default: raise

    Returns
    -------
    Root
        root of AST tree as parsed by tree-sitter
    """

    if len(source_code.strip()) == 0:
        raise ValueError("The code string is empty. Cannot tokenize anything empty: %s" % source_code)

    # If lang == guess, automatically determine the language
    if lang == "guess":
        lang = _lang_detect(source_code)

    logger.debug("Parses source code with parser for %s" % lang)

    # Setup config
    config = ParserConfig(lang, **kwargs)

    # Parse source tree
    parser = ASTParser(config.lang)
    tree, code = parser.parse(source_code)

    # Check for errors if necessary
    check_tree_for_errors(tree, mode=config.syntax_error)

    return SourceCodeAST(config, tree, code)


# Lang detect --------------------------------------
def _lang_detect(source_code):
    """Guesses the source code type using pygments"""
    raise NotImplementedError(
        "Guessing the language automatically is currently not implemented. "
        "Please specify a language with the lang keyword\n code_tokenize.tokenize(code, lang = your_lang)"
    )


# Detect error --------------------------------
class ErrorVisitor(ASTVisitor):

    def __init__(self, error_mode):
        self.error_mode = error_mode

    def visit_ERROR(self, node):

        if self.error_mode == "raise":
            raise_syntax_error(node)
            return

        if self.error_mode == "warn":
            warn_syntax_error(node)
            return


def check_tree_for_errors(tree, mode="raise"):
    if mode == "ignore":
        return

    # Check for errors
    ErrorVisitor(mode)(tree)


# Error handling -----------------------------------------------------------
def _construct_error_msg(node):
    start_line, start_char = node.start_point
    end_line, end_char = node.end_point

    position = "?"
    if start_line == end_line:
        position = "in line %d [pos. %d - %d]" % (start_line, start_char, end_char)
    else:
        position = "inbetween line %d (start: %d) to line %d (end: %d)" % (start_line, start_char, end_line, end_char)

    return "Problem while parsing given code snipet. Error occured %s" % position


def warn_syntax_error(node):
    logger.warn(_construct_error_msg(node))


def raise_syntax_error(node):
    raise SyntaxError(_construct_error_msg(node))


def get_all_components(root_node):
    subtree_roots = []
    if not root_node:
        return subtree_roots

    while len(root_node.children) == 1:
        root_node = root_node.children[0]

    if root_node.type in META_TYPES or root_node.type.endswith("_statement"):
        return [root_node]
    children = root_node.children

    for i, child in enumerate(children):
        if len(child.children) == 0 or child.type in META_TYPES or root_node.type.endswith("_statement"):
            subtree_roots.append(child)
        else:
            subtree_roots.extend(get_all_components(child))
    return subtree_roots


if __name__ == "__main__":
    s = '''
import torch
import numpy as np


def my_func():
    print("Hello World")

class GraphAlgos:

    @staticmethod
    def topo_sort(graph: nx.DiGraph) -> List:
        return list(nx.topological_sort(graph))
'''
    lang = "python"
    config = ParserConfig(lang)
    parser = ASTParser(lang)
    tree, code = parser.parse(s)
    print(SourceCodeAST(config, tree, code))
    # test_ast = ast_parser(s, lang=lang)
    nodes = get_all_components(tree.root_node)
    for n in nodes:
        print(n.text)
