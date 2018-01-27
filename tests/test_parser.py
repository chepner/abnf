import pytest
from abnf.parser import (Node, LiteralNode, Literal, ABNFGrammarRule, Rule, CharVal, ParseError, Alternation,
    Concatenation, Repeat, Repetition, Option)


def test_empty_literal():
    parser = Literal('')
    assert parser

def test_literal():
    parser = Literal('moof')
    source = 'moof'
    node, start = parser.parse(source, 0)
    assert node.value == 'moof'

def test_literal_range_fail():
    parser = Literal(('a', 'b'))
    with pytest.raises(ParseError):
        parser.parse('c', 0)

def test_literal_range_out_of_bounds():
    parser = Literal(('a', 'b'))
    with pytest.raises(ParseError):
        parser.parse('a', 1)

def test_empty_literal_out_of_bounds():
    parser = Literal('')
    src = 'a'
    with pytest.raises(ParseError):
        parser.parse(src, 1)

@pytest.mark.parametrize('value, expected', [('foo', r"Literal('foo')"), ('\r', r"Literal('\x0d')")])
def test_literal_str(value, expected):
    parser = Literal(value)
    assert str(parser) == expected

@pytest.mark.parametrize('value, src', [('A', 'A'), ('A', 'a'), ('a', 'A'), ('a', 'a')])
def test_literal_case_insensitive(value, src):
    parser = Literal(value)
    node, start = parser.parse(src, 0)
    assert node.value == src

@pytest.mark.parametrize("src", ['moof', 'MOOF', 'mOOf', 'mOoF'])
def test_char_val(src):
    node, start = ABNFGrammarRule('char-val').parse('"moof"', 0)
    parser = CharVal(node)
    char_node, start = parser.parse(src, 0)
    assert char_node and char_node.value == src

@pytest.mark.parametrize("src", ['moof', 'MOOF', 'mOOf', 'mOoF'])
def test_char_val_case_insensitive(src):
    node, start = ABNFGrammarRule('char-val').parse('%i"moof"', 0)
    parser = CharVal(node)
    char_node, start = parser.parse(src, 0)
    assert char_node and char_node.value.casefold() == 'moof'

def test_CharVal_case_sensitive():
    node, start = ABNFGrammarRule('char-val').parse('%s"MOOF"', 0)
    parser = CharVal(node)
    assert parser.case_sensitive

def test_char_val_case_sensitive():
    node, start = ABNFGrammarRule('char-val').parse('%s"MOOF"', 0)
    parser = CharVal(node)
    src = 'MOOF'
    char_node, start = parser.parse(src, 0)
    assert char_node and char_node.value == src

def test_CharVal_bad_node():
    node = Node(name='foo')
    with pytest.raises(ParseError):
        CharVal(node)

@pytest.mark.parametrize("src", ['MOOF', 'mOOf', 'mOoF'])
def test_char_val_case_sensitive_fail(src):
    node, start = ABNFGrammarRule('char-val').parse('%s"moof"', 0)
    parser = CharVal(node)
    with pytest.raises(ParseError):
        parser.parse(src, 0)

@pytest.mark.parametrize("src", ['A', 'B', 'Z'])
def test_literal_range(src):
    parser = Literal(('\x41', '\x5A'))
    node, start = parser.parse(src, 0)
    assert node and node.value == src

@pytest.mark.parametrize("src", ['foo', 'bar'])
def test_alternation(src):
    parser = Alternation(Literal('foo'), Literal('bar'))
    node, start = parser.parse(src, 0)
    assert node.value == src

# test repetition and match of empty elements.
@pytest.mark.parametrize("src, expected", [
    ('1*43', (1, 43)),
    ('1*', (1, None)),
    ('*43', (0, 43)),
    ('43', (43, 43)),
    ])
def test_rule_repeat(src, expected):
    node, start = ABNFGrammarRule('repeat').parse(src, 0)
    parser = Rule.make_parser_repeat(node)
    assert (parser.min, parser.max) == expected


def test_repetition():
    parser = Repetition(Repeat(1, 2), Literal('a'))
    node, start = parser.parse('aa', 0)
    assert [x for x in node] == [LiteralNode('a', x, 1) for x in range(0, 2)]

def test_repetition_str():
    parser = Repetition(Repeat(1, 2), Literal('a'))
    assert str(parser) == "Repetition(Repeat(1, 2), Literal('a'))"

@pytest.mark.parametrize("src", ['bc', 'a', pytest.param('ac', marks=pytest.mark.xfail)])
def test_operator_precedence(src):
    grammar_src = '"a" / "b" "c"'
    node, start = ABNFGrammarRule('alternation').parse(grammar_src, 0)
    parser = Rule.make_parser(node)
    node, start = parser.parse(src, 0)
    print(node)
    assert ''.join(x.value for x in node) == src


@pytest.mark.parametrize("src", ['ac', 'bc'])
def test_operator_precedence_1(src):
    grammar_src = '("a" / "b") "c"'
    node, start = ABNFGrammarRule('concatenation').parse(grammar_src, 0)
    parser = Rule.make_parser(node)
    node, start = parser.parse(src, 0)
    print(node)
    assert ''.join(x.value for x in node) == src

def test_node_str():
    node_name = 'foo'
    node_children = []
    node = Node(name=node_name, *node_children)
    assert str(node) == 'Node(name=%s, children=%s)' % (node_name, str(node_children))

def test_literal_node_children():
    node = LiteralNode('', 0, 0)
    assert node.children == []

def test_Alternation_eq():
    p1 = Alternation(Rule('a'), Rule('b'))
    p2 = Alternation(Rule('a'), Rule('b'))
    assert p1 == p2

def test_Alternation_str():
    parser = Alternation(Literal('foo'), Literal('bar'))
    assert str(parser) == "Alternation(Literal('foo'), Literal('bar'))"

def test_Concatenation_str():
    parser = Concatenation(Literal('foo'), Literal('bar'))
    assert str(parser) == "Concatenation(Literal('foo'), Literal('bar'))"

def test_option_str():
    parser = Option(Alternation(Literal('foo')))
    assert str(parser) == "Option(Alternation(Literal('foo')))"

def test_rule_undefined():
    with pytest.raises(ParseError):
        Rule('undefined').parse('x', 0)

def test_rule_str():
    assert str(Rule('ALPHA')) == "Rule('ALPHA')"

@pytest.mark.parametrize("src", ['a', 'b'])
def test_rule_def_alternation(src):
    class TestRule(Rule):
        pass

    rulelist = ['moof = "a"', 'moof =/ "b"']
    for rule in rulelist:
        TestRule.create(rule)

    node, start = TestRule('moof').parse(src, 0)
    assert node and node.value == src

def test_rule_bad_defined_as():
    node = Node('rule', *[Node('rulename', *[Node('ALPHA', *[LiteralNode('a', 0, 1)])]), Node('defined-as', *[LiteralNode("=\\", 1, 2)]), Node('elements', *[Node('alternation', *[Node('concatenation', *[Node('repetition', *[Node('element', *[Node('rulename', *[Node('ALPHA', *[LiteralNode('b', 3, 1)])])])])])])]), Node('c-nl', *[Node('CRLF', *[Node('CR', *[LiteralNode('\r', 4, 1)]), Node('LF', *[LiteralNode('\n', 5, 1)])])])])
    with pytest.raises(AssertionError):
        Rule.make_parser_rule(node)

def test_rule_make_parser_alternation():
    src = 'a/b'
    node, start = ABNFGrammarRule('alternation').parse(src, 0)    
    parser = Rule.make_parser_alternation(node)
    assert parser == Alternation(Rule('a'), Rule('b'))

def test_rule_rules():
    class XRule(Rule):
        pass
    
    # an XRule object is created, albeit without definition.
    XRule('foo')
    assert XRule.rules() == [XRule('foo')]
