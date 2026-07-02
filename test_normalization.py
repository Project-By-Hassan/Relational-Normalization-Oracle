import unittest
from normalization_engine import (
    compute_closure,
    find_candidate_keys,
    check_2nf,
    check_3nf,
    check_bcnf,
    check_4nf,
    check_5nf,
    find_canonical_cover,
    decompose_3nf,
    decompose_bcnf_trace,
    check_dependency_preservation,
    check_lossless_join,
    discover_fds_from_dataframe
)

class TestNormalizationEngine(unittest.TestCase):

    def setUp(self):
        # Setup common academic schemas
        
        # 1. R(A, B, C, D) with FDs: A -> B, B -> C
        self.R1 = {"A", "B", "C", "D"}
        self.fds1 = [
            {"lhs": {"A"}, "rhs": {"B"}},
            {"lhs": {"B"}, "rhs": {"C"}}
        ]
        # Candidate keys should be: {A, D}
        # Closure of A is {A, B, C}
        # Closure of {A, D} is {A, B, C, D}
        
        # 2. R(A, B, C, D, E) with FDs: A -> B, BC -> D, E -> A
        self.R2 = {"A", "B", "C", "D", "E"}
        self.fds2 = [
            {"lhs": {"A"}, "rhs": {"B"}},
            {"lhs": {"B", "C"}, "rhs": {"D"}},
            {"lhs": {"E"}, "rhs": {"A"}}
        ]
        # Candidate keys of R2: {C, E}
        # Let's check closure of {C, E}: {C, E} -> {A, C, E} -> {A, B, C, E} -> {A, B, C, D, E} = R2
        
        # 3. BCNF Violation case: R(A, B, C) with FDs: A -> B, B -> C, C -> A
        # Candidate keys: {A}, {B}, {C} (all attributes are prime, no BCNF violation here since all LHS are superkeys!)
        # Let's use: R(A, B, C) with FDs: A -> B, B -> A, B -> C (Keys: {A}, {B}, all FDs have superkey LHS, so it's in BCNF)
        # Violating BCNF: R(A, B, C) with FDs: A -> B, C -> B (Keys: {A, C}, LHS is not superkey, so not in BCNF, violates 2NF/3NF/BCNF)
        self.R3 = {"A", "B", "C"}
        self.fds3 = [
            {"lhs": {"A"}, "rhs": {"B"}},
            {"lhs": {"C"}, "rhs": {"B"}}
        ]
        
    def test_compute_closure(self):
        # Under fds1: A -> B, B -> C
        self.assertEqual(compute_closure({"A"}, self.fds1), {"A", "B", "C"})
        self.assertEqual(compute_closure({"B"}, self.fds1), {"B", "C"})
        self.assertEqual(compute_closure({"A", "D"}, self.fds1), {"A", "B", "C", "D"})
        
    def test_find_candidate_keys(self):
        keys1 = find_candidate_keys(self.R1, self.fds1)
        self.assertEqual(len(keys1), 1)
        self.assertEqual(keys1[0], {"A", "D"})
        
        keys2 = find_candidate_keys(self.R2, self.fds2)
        # Candidates should be {C, E}
        self.assertEqual(len(keys2), 1)
        self.assertEqual(keys2[0], {"C", "E"})

    def test_check_2nf(self):
        # R1 keys: {A, D}. Non-primes: {B, C}.
        # Subset {A} of key {A, D} determines B (non-prime) -> violates 2NF!
        keys1 = [{"A", "D"}]
        non_primes1 = {"B", "C"}
        is_2nf, violations = check_2nf(self.R1, self.fds1, keys1, non_primes1)
        self.assertFalse(is_2nf)
        self.assertTrue(len(violations) > 0)
        
        # Another test: R(A, B, C) with FDs: A -> B, A -> C (Key: {A}. Since Key size is 1, no partial dependencies, must be 2NF)
        R_temp = {"A", "B", "C"}
        fds_temp = [{"lhs": {"A"}, "rhs": {"B", "C"}}]
        keys_temp = [{"A"}]
        non_primes_temp = {"B", "C"}
        is_2nf_temp, violations_temp = check_2nf(R_temp, fds_temp, keys_temp, non_primes_temp)
        self.assertTrue(is_2nf_temp)

    def test_check_3nf(self):
        # R1 with keys {A, D} and FDs: A -> B, B -> C
        # B -> C is non-trivial, B is not superkey, C is not prime -> violates 3NF
        keys1 = [{"A", "D"}]
        prime1 = {"A", "D"}
        is_3nf, violations = check_3nf(self.R1, self.fds1, keys1, prime1)
        self.assertFalse(is_3nf)
        
    def test_check_bcnf(self):
        keys1 = [{"A", "D"}]
        is_bcnf, violations = check_bcnf(self.R1, self.fds1, keys1)
        self.assertFalse(is_bcnf)
        
    def test_canonical_cover(self):
        # R(A, B, C) with FDs: A -> B, B -> C, A -> C
        fds = [
            {"lhs": {"A"}, "rhs": {"B"}},
            {"lhs": {"B"}, "rhs": {"C"}},
            {"lhs": {"A"}, "rhs": {"C"}}
        ]
        cover = find_canonical_cover({"A", "B", "C"}, fds)
        # A -> C should be redundant and removed
        self.assertEqual(len(cover), 2)
        # The FDs left should be A -> B and B -> C
        lhs_sets = [f["lhs"] for f in cover]
        self.assertIn({"A"}, lhs_sets)
        self.assertIn({"B"}, lhs_sets)

    def test_decompose_3nf(self):
        keys1 = [{"A", "D"}]
        relations, cover, added_key = decompose_3nf(self.R1, self.fds1, keys1)
        # Relations should be: {A, B}, {B, C}, and the candidate key {A, D}
        expected = [{"A", "B"}, {"B", "C"}, {"A", "D"}]
        self.assertEqual(len(relations), 3)
        for r in expected:
            self.assertIn(r, relations)

    def test_decompose_bcnf(self):
        # R(A, B, C, D) with A -> B, B -> C, C -> D (Key: {A})
        # Violating FDs: B -> C (B is not superkey), C -> D (C is not superkey)
        R = {"A", "B", "C", "D"}
        fds = [
            {"lhs": {"A"}, "rhs": {"B"}},
            {"lhs": {"B"}, "rhs": {"C"}},
            {"lhs": {"C"}, "rhs": {"D"}}
        ]
        decomp, trace = decompose_bcnf_trace(R, fds)
        # Decomposition should result in BCNF schemas
        # Expected: {A, B}, {B, C}, {C, D}
        for schema in decomp:
            keys = find_candidate_keys(schema, project_fds(schema, fds))
            is_bcnf, violations = check_bcnf(schema, project_fds(schema, fds), keys)
            self.assertTrue(is_bcnf)
            
    def test_dependency_preservation(self):
        # R(A, B, C) with A -> B, B -> C, C -> A
        # Decomposed into {A, B} and {B, C}
        # Under A -> B, B -> C, projection preserves both.
        R = {"A", "B", "C"}
        fds = [
            {"lhs": {"A"}, "rhs": {"B"}},
            {"lhs": {"B"}, "rhs": {"C"}},
            {"lhs": {"C"}, "rhs": {"A"}}
        ]
        D = [{"A", "B"}, {"B", "C"}]
        is_preserving, preserved, failed = check_dependency_preservation(D, fds, R)
        # Let's verify: D is dependency preserving since C -> A can be inferred:
        # C -> B (via B -> C projected) and B -> A (via A -> B and C -> A projected) ... wait, is it?
        # Actually, let's see. Z = {C}. In R_2={B,C}, intersection = {C}, closure = {A,B,C}, Z becomes {C} U ({A,B,C} intersect {B,C}) = {B,C}.
        # In R_1={A,B}, intersection = {B}, closure = {A,B,C}, Z becomes {B,C} U ({A,B,C} intersect {A,B}) = {A,B,C}.
        # Since A is in Z, C -> A is preserved! So is_preserving should be True.
        self.assertTrue(is_preserving)
        
        # Case of non-preserving: R(A, B, C) with A, B -> C and C -> A. Decomposed into {A, C} and {B, C}
        # Original FD A, B -> C.
        fds_non = [
            {"lhs": {"A", "B"}, "rhs": {"C"}},
            {"lhs": {"C"}, "rhs": {"A"}}
        ]
        D_non = [{"A", "C"}, {"B", "C"}]
        is_preserving_non, preserved_non, failed_non = check_dependency_preservation(D_non, fds_non, R)
        # A, B -> C is not preserved because it needs attributes from both schemas and cannot be derived.
        self.assertFalse(is_preserving_non)
        self.assertEqual(len(failed_non), 1)
        self.assertEqual(failed_non[0]["lhs"], {"A", "B"})

    def test_chase_algorithm(self):
        # Lossless: R(A, B, C) with A -> B. Decomposed into {A, B} and {A, C}.
        # Intersection is {A}, which is a key of {A, B}. Should be lossless.
        R = {"A", "B", "C"}
        fds = [{"lhs": {"A"}, "rhs": {"B"}}]
        D = [{"A", "B"}, {"A", "C"}]
        is_lossless, table = check_lossless_join(D, fds, R)
        self.assertTrue(is_lossless)
        
        # Lossy: R(A, B, C) with B -> C. Decomposed into {A, B} and {B, C} ... wait, intersection is B, which is a key of {B,C}. That's lossless.
        # Lossy example: R(A, B, C) with no FDs, decomposed into {A, B} and {B, C}.
        fds_lossy = []
        is_lossless_lossy, table_lossy = check_lossless_join(D, fds_lossy, R)
        self.assertFalse(is_lossless_lossy)

    def test_mvd_4nf_check(self):
        # R(A, B, C) with MVD: A ->-> B. Keys: {A, B, C} (no FDs).
        # Trivial MVDs: A ->-> A, A ->-> A,B,C.
        # Self-defined MVD A ->-> B is non-trivial (B is not subset of A, A U B = {A,B} != R).
        # A is not superkey. So 4NF is violated.
        R = {"A", "B", "C"}
        mvds = [{"lhs": {"A"}, "rhs": {"B"}}]
        fds = []
        keys = [{"A", "B", "C"}]
        is_4nf, violations = check_4nf(R, mvds, fds, keys)
        self.assertFalse(is_4nf)
        self.assertEqual(len(violations), 1)

    def test_jd_5nf_check(self):
        # R(A, B, C) with JD: Join(AB, BC, AC). Keys: {A, B, C} (no FDs).
        # Components AB, BC, AC are not superkeys. So 5NF is violated.
        R = {"A", "B", "C"}
        jds = [{
            "name": "Join(AB, BC, AC)",
            "components": [{"A", "B"}, {"B", "C"}, {"A", "C"}]
        }]
        fds = []
        keys = [{"A", "B", "C"}]
        is_5nf, violations = check_5nf(R, jds, fds, keys)
        self.assertFalse(is_5nf)
        self.assertEqual(len(violations), 1)

    def test_discover_fds_from_dataframe(self):
        import pandas as pd
        # Create a simple dataset where A -> B and C -> D hold
        data = {
            "A": [1, 2, 1, 2, 3],
            "B": [10, 20, 10, 20, 30], # A -> B
            "C": [100, 100, 200, 200, 300],
            "D": [5, 5, 6, 6, 7] # C -> D
        }
        df = pd.DataFrame(data)
        mined_fds = discover_fds_from_dataframe(df, max_lhs_size=1)
        
        mappings = {}
        for fd in mined_fds:
            lhs_tup = tuple(sorted(list(fd["lhs"])))
            mappings[lhs_tup] = fd["rhs"]
            
        self.assertIn(("A",), mappings)
        self.assertIn("B", mappings[("A",)])
        self.assertIn(("C",), mappings)
        self.assertIn("D", mappings[("C",)])

# Helper to project fds in tests
def project_fds(R_sub, fds):
    projected = []
    R_sub_list = list(R_sub)
    import itertools
    for r in range(1, len(R_sub) + 1):
        for comb in itertools.combinations(R_sub_list, r):
            lhs = set(comb)
            closure = compute_closure(lhs, fds)
            rhs = (closure & R_sub) - lhs
            if rhs:
                projected.append({"lhs": lhs, "rhs": rhs})
    return find_canonical_cover(R_sub, projected)

if __name__ == "__main__":
    unittest.main()
