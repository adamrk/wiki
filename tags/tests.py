import unittest
import doctest
import minewords as mw

class TestLabelCitations(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def testEmpty(self):
        r = mw.label_citations([])
        self.assertEqual(r, [])
    def testSingle(self):
        r = mw.label_citations(["aouaou[1]"])
        s = mw.label_citations(["oauauooa[3"])
        t = mw.label_citations(["[3]auuuu"])
        u = mw.label_citations(["huhu hh foo [citation needed]"])
        self.assertEqual(r,[1])
        self.assertEqual(s,[0])
        self.assertEqual(t,[0])
        self.assertEqual(u,[1])

if __name__ == '__main__':
    nfails, ntest = doctest.testmod(mw)
    if nfails == 0:
        print "Doctests OK"
    print "Unit Tests:"
    unittest.main()
