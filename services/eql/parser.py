"""
EQL (Epistemic Query Language) Parser

Grammar:
    query ::= find_query | trace_query
    find_query ::= "FIND" target "WHERE" condition
    trace_query ::= "TRACE" hypothesis_id "OVER TIME"
    target ::= "traces" | "hypotheses" | "agents"
    condition ::= comparison | condition "AND" condition | condition "OR" condition | "(" condition ")"
    comparison ::= field operator value
    field ::= "agent" | "confidence" | "consensus" | "hypothesis_id" | "timestamp"
    operator ::= "=" | "!=" | ">" | "<" | ">=" | "<=" | "CONTAINS" | "BETWEEN"
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Dict, Union
from datetime import datetime


class TokenType(Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    OPERATOR = "OPERATOR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int


@dataclass
class Comparison:
    left: str
    operator: str
    right: Any


@dataclass
class Condition:
    operator: str
    conditions: List[Union[Comparison, 'Condition']] = field(default_factory=list)


@dataclass
class Query:
    type: str
    target: Optional[str] = None
    condition: Optional[Condition] = None
    hypothesis_id: Optional[str] = None
    time_range: Optional[str] = None
    limit: Optional[int] = None


class EQLSyntaxError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Syntax error at {line}:{column} - {message}")


class EQLTokenizer:
    KEYWORDS = {"FIND", "TRACE", "WHERE", "OVER", "TIME", "AND", "OR", "LIMIT", "CONTAINS", "BETWEEN"}
    OPERATORS = {"=", "!=", ">", "<", ">=", "<="}

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        self.tokens = []

        while self.position < len(self.source):
            char = self.source[self.position]

            if char.isspace():
                self._advance()
                continue

            if char == '-' and self._peek() == '-':
                self._advance()
                self._advance()
                self._skip_line()
                continue

            if char.isdigit() or (char == '-' and self._peek().isdigit()):
                self._read_number()
                continue

            if char == '"' or char == "'":
                self._read_string()
                continue

            if char.isalpha() or char == '_':
                self._read_identifier()
                continue

            if char in self.OPERATORS:
                self._read_operator()
                continue

            if char == '(':
                self.tokens.append(Token(TokenType.LPAREN, "(", self.line, self.column))
                self._advance()
                continue

            if char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ")", self.line, self.column))
                self._advance()
                continue

            raise EQLSyntaxError(f"Unexpected character: {char}", self.line, self.column)

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

    def _advance(self):
        if self.source[self.position] == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def _peek(self) -> str:
        if self.position + 1 >= len(self.source):
            return '\0'
        return self.source[self.position + 1]

    def _skip_line(self):
        while self.position < len(self.source) and self.source[self.position] != '\n':
            self._advance()

    def _read_number(self):
        start_col = self.column
        num_str = ""

        if self.source[self.position] == '-':
            num_str += '-'
            self._advance()

        while self.position < len(self.source) and self.source[self.position].isdigit():
            num_str += self.source[self.position]
            self._advance()

        if self.position < len(self.source) and self.source[self.position] == '.':
            num_str += '.'
            self._advance()
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num_str += self.source[self.position]
                self._advance()

        value = float(num_str) if '.' in num_str else int(num_str)
        self.tokens.append(Token(TokenType.NUMBER, value, self.line, start_col))

    def _read_string(self):
        quote_char = self.source[self.position]
        start_col = self.column
        self._advance()

        string_value = ""
        while self.position < len(self.source) and self.source[self.position] != quote_char:
            if self.source[self.position] == '\\':
                self._advance()
                if self.position < len(self.source):
                    escape_map = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', "'": "'", '\\': '\\'}
                    string_value += escape_map.get(self.source[self.position], self.source[self.position])
                    self._advance()
            else:
                string_value += self.source[self.position]
                self._advance()

        if self.position >= len(self.source):
            raise EQLSyntaxError("Unterminated string", self.line, start_col)

        self._advance()
        self.tokens.append(Token(TokenType.STRING, string_value, self.line, start_col))

    def _read_identifier(self):
        start_col = self.column
        identifier = ""

        while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
            identifier += self.source[self.position]
            self._advance()

        if identifier.upper() in self.KEYWORDS:
            token_type = TokenType.KEYWORD
            value = identifier.upper()
        else:
            token_type = TokenType.IDENTIFIER
            value = identifier

        self.tokens.append(Token(token_type, value, self.line, start_col))

    def _read_operator(self):
        start_col = self.column
        operator = self.source[self.position]
        self._advance()

        if operator in {'>', '<', '!', '='} and self.position < len(self.source) and self.source[self.position] == '=':
            operator += '='
            self._advance()

        self.tokens.append(Token(TokenType.OPERATOR, operator, self.line, start_col))


class EQLParser:
    def __init__(self):
        self.tokens: List[Token] = []
        self.position = 0

    def parse(self, source: str) -> Query:
        tokenizer = EQLTokenizer(source)
        self.tokens = tokenizer.tokenize()
        self.position = 0

        if self._is_eof():
            raise EQLSyntaxError("Empty query", 1, 1)

        token = self._peek()

        if token.value == "FIND":
            return self._parse_find_query()
        elif token.value == "TRACE":
            return self._parse_trace_query()
        else:
            raise EQLSyntaxError(f"Expected FIND or TRACE, got {token.value}", token.line, token.column)

    def _parse_find_query(self) -> Query:
        self._consume_keyword("FIND")
        target_token = self._consume(TokenType.IDENTIFIER)
        target = target_token.value

        self._consume_keyword("WHERE")
        condition = self._parse_condition()

        limit = None
        if not self._is_eof() and self._peek().value == "LIMIT":
            self._consume_keyword("LIMIT")
            limit_token = self._consume(TokenType.NUMBER)
            limit = int(limit_token.value)

        return Query(type="FIND", target=target, condition=condition, limit=limit)

    def _parse_trace_query(self) -> Query:
        self._consume_keyword("TRACE")
        hypothesis_token = self._consume(TokenType.STRING)
        hypothesis_id = hypothesis_token.value

        self._consume_keyword("OVER")
        self._consume_keyword("TIME")

        return Query(type="TRACE", hypothesis_id=hypothesis_id, time_range="OVER TIME")

    def _parse_condition(self) -> Condition:
        return self._parse_logical_expression()

    def _parse_logical_expression(self) -> Condition:
        left = self._parse_primary_condition()

        if self._is_eof():
            return Condition(operator=None, conditions=[left])

        next_token = self._peek()
        if next_token.value in ("AND", "OR"):
            operator = next_token.value
            self._advance()
            right = self._parse_logical_expression()
            return Condition(operator=operator, conditions=[left, right])

        return Condition(operator=None, conditions=[left])

    def _parse_primary_condition(self) -> Union[Comparison, Condition]:
        if self._peek().type == TokenType.LPAREN:
            self._advance()
            condition = self._parse_logical_expression()
            self._consume(TokenType.RPAREN)
            return condition

        return self._parse_comparison()

    def _parse_comparison(self) -> Comparison:
        field_token = self._consume(TokenType.IDENTIFIER)
        field = field_token.value

        op_token = self._peek()

        if op_token.type == TokenType.KEYWORD and op_token.value == "CONTAINS":
            self._advance()
            operator = "CONTAINS"
            value_token = self._consume(TokenType.STRING)
            value = value_token.value
        elif op_token.type == TokenType.KEYWORD and op_token.value == "BETWEEN":
            self._advance()
            operator = "BETWEEN"
            left_val = self._parse_value()
            self._consume_keyword("AND")
            right_val = self._parse_value()
            value = [left_val, right_val]
        else:
            op_token = self._consume(TokenType.OPERATOR)
            operator = op_token.value
            value = self._parse_value()

        return Comparison(left=field, operator=operator, right=value)

    def _parse_value(self) -> Any:
        token = self._peek()

        if token.type == TokenType.STRING:
            self._advance()
            return token.value
        elif token.type == TokenType.NUMBER:
            self._advance()
            return token.value
        elif token.type == TokenType.IDENTIFIER:
            val = token.value.lower()
            self._advance()
            if val == "true":
                return True
            elif val == "false":
                return False
            else:
                raise EQLSyntaxError(f"Expected value, got {val}", token.line, token.column)
        else:
            raise EQLSyntaxError(f"Expected value, got {token.type.name}", token.line, token.column)

    def _consume(self, expected_type: TokenType) -> Token:
        if self._is_eof():
            raise EQLSyntaxError(f"Unexpected end of input, expected {expected_type.name}",
                                 self.tokens[-1].line, self.tokens[-1].column)

        token = self._peek()
        if token.type != expected_type:
            raise EQLSyntaxError(f"Expected {expected_type.name}, got {token.type.name}",
                                 token.line, token.column)

        self._advance()
        return token

    def _consume_keyword(self, expected: str):
        token = self._consume(TokenType.KEYWORD)
        if token.value != expected:
            raise EQLSyntaxError(f"Expected {expected}, got {token.value}", token.line, token.column)

    def _peek(self) -> Token:
        return self.tokens[self.position]

    def _advance(self):
        self.position += 1

    def _is_eof(self) -> bool:
        return self.position >= len(self.tokens) or self.tokens[self.position].type == TokenType.EOF


class EQLExecutor:
    def __init__(self, history_data: List[Dict[str, Any]]):
        self.history_data = history_data

    def execute(self, query: Query) -> List[Dict[str, Any]]:
        if query.type == "FIND":
            return self._execute_find(query)
        elif query.type == "TRACE":
            return self._execute_trace(query)
        else:
            raise ValueError(f"Unknown query type: {query.type}")

    def _execute_find(self, query: Query) -> List[Dict[str, Any]]:
        results = self.history_data

        if query.condition:
            results = [r for r in results if self._evaluate_condition(r, query.condition)]

        if query.limit:
            results = results[:query.limit]

        return results

    def _execute_trace(self, query: Query) -> List[Dict[str, Any]]:
        return [r for r in self.history_data if r.get("hypothesis_id") == query.hypothesis_id]

    def _evaluate_condition(self, record: Dict[str, Any], condition: Condition) -> bool:
        if condition.operator is None:
            return self._evaluate_comparison(record, condition.conditions[0])

        if condition.operator == "AND":
            return all(self._evaluate_condition(record, c) for c in condition.conditions)
        elif condition.operator == "OR":
            return any(self._evaluate_condition(record, c) for c in condition.conditions)

        return False

    def _evaluate_comparison(self, record: Dict[str, Any], comparison: Comparison) -> bool:
        left_value = record.get(comparison.left)
        right_value = comparison.right

        if left_value is None:
            return False

        operator = comparison.operator

        if operator == "=":
            return left_value == right_value
        elif operator == "!=":
            return left_value != right_value
        elif operator == ">":
            return left_value > right_value
        elif operator == "<":
            return left_value < right_value
        elif operator == ">=":
            return left_value >= right_value
        elif operator == "<=":
            return left_value <= right_value
        elif operator == "CONTAINS":
            return right_value in str(left_value)
        elif operator == "BETWEEN":
            return right_value[0] <= left_value <= right_value[1]

        return False
