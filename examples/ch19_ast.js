"use strict";

const { parse } = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const t = require("@babel/types");
const generate = require("@babel/generator").default;

const source = process.env.AST_SOURCE || "const total = 2 + 3 * 4;";
const ast = parse(source, { sourceType: "script" });

traverse(ast, {
  BinaryExpression: {
    exit(path) {
      const { left, right, operator } = path.node;
      if (!t.isNumericLiteral(left) || !t.isNumericLiteral(right)) return;
      let value;
      if (operator === "+") value = left.value + right.value;
      if (operator === "*") value = left.value * right.value;
      if (value !== undefined && Number.isFinite(value)) {
        path.replaceWith(t.numericLiteral(value));
      }
    },
  },
});

console.log(generate(ast).code);
