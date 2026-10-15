"""Tests of the ValueRef/TypeRef API used to avoid parsing printed IR."""
from __future__ import print_function, absolute_import

from llvmlite import binding as llvm
from . import TestCase


def setUpModule():
    llvm.initialize()
    llvm.initialize_native_target()


def _insts(mod, fname):
    return [i for b in mod.get_function(fname).blocks for i in b.instructions]


class TestAlignment(TestCase):
    ir = r"""
    @g1 = global i32 0, align 16
    @g2 = global i32 0
    define void @f(ptr %p) {
      %a = alloca i64, align 8
      %b = alloca i8
      %l = load i32, ptr %p, align 2
      %m = load i32, ptr %p
      store i32 1, ptr %p, align 1
      store i64 1, ptr %a, align 4
      %c = add i32 %l, %m
      ret void
    }
    """

    def test_alignment(self):
        mod = llvm.parse_assembly(self.ir)
        mod.verify()
        self.assertEqual(mod.get_global_variable('g1').alignment, 16)
        self.assertIsNone(mod.get_global_variable('g2').alignment)
        i = _insts(mod, 'f')
        self.assertEqual([x.opcode for x in i[:4]],
                         ['alloca', 'alloca', 'load', 'load'])
        self.assertEqual(i[0].alignment, 8)
        self.assertEqual(i[1].alignment, 1)
        self.assertEqual(i[2].alignment, 2)
        self.assertEqual(i[3].alignment, 4)  # not given: ABI alignment of i32
        self.assertEqual(i[4].alignment, 1)
        self.assertEqual(i[5].alignment, 4)

    def test_no_alignment(self):
        mod = llvm.parse_assembly(self.ir)
        i = _insts(mod, 'f')
        self.assertEqual(i[6].opcode, 'add')
        with self.assertRaises(ValueError):
            i[6].alignment
        with self.assertRaises(ValueError):
            i[7].alignment
