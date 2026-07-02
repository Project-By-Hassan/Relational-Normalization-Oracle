import itertools

def compute_closure(attributes, fds):
    """
    Computes the attribute closure of a set of attributes under a set of FDs.
    attributes: set of strings (attributes)
    fds: list of dicts {"lhs": set, "rhs": set}
    """
    closure = set(attributes)
    while True:
        added = False
        for fd in fds:
            if fd["lhs"].issubset(closure):
                new_elements = fd["rhs"] - closure
                if new_elements:
                    closure.update(new_elements)
                    added = True
        if not added:
            break
    return closure

def find_candidate_keys(R, fds):
    """
    Finds all candidate keys of a relation schema R under FDs.
    R: set of strings (all attributes in relation)
    fds: list of dicts {"lhs": set, "rhs": set}
    """
    if not R:
        return []
        
    all_lhs = set()
    all_rhs = set()
    for fd in fds:
        all_lhs.update(fd["lhs"])
        all_rhs.update(fd["rhs"])
        
    L = all_lhs - all_rhs
    R_only = all_rhs - all_lhs
    N = R - (all_lhs | all_rhs)
    B = R & all_lhs & all_rhs
    
    # Core set must be present in every candidate key
    core = L | N
    core_closure = compute_closure(core, fds)
    
    if core_closure == R:
        return [core]
        
    candidate_keys = []
    B_list = sorted(list(B))
    
    # Search combinations of B attributes
    for k in range(len(B_list) + 1):
        level_keys = []
        for comb in itertools.combinations(B_list, k):
            candidate = core | set(comb)
            
            # Prune if candidate is a superset of an already found candidate key
            is_superset = False
            for ck in candidate_keys:
                if ck.issubset(candidate):
                    is_superset = True
                    break
            if is_superset:
                continue
                
            if compute_closure(candidate, fds) == R:
                level_keys.append(candidate)
                
        if level_keys:
            candidate_keys.extend(level_keys)
            
    if not candidate_keys:
        candidate_keys = [R]
        
    # Sort candidate keys by size and then alphabetically for deterministic output
    candidate_keys.sort(key=lambda x: (len(x), sorted(list(x))))
    return candidate_keys

def check_2nf(R, fds, candidate_keys, non_prime_attrs):
    """
    Checks if relation R satisfies 2NF.
    2NF: No non-prime attribute is partially dependent on any candidate key.
    """
    violations = []
    for K in candidate_keys:
        if len(K) <= 1:
            continue
        # Proper subsets of candidate key K
        for r in range(1, len(K)):
            for subset in itertools.combinations(K, r):
                S = set(subset)
                S_closure = compute_closure(S, fds)
                violating_non_prime = (S_closure & non_prime_attrs) - S
                
                if violating_non_prime:
                    for attr in violating_non_prime:
                        violations.append({
                            "key": K,
                            "subset": S,
                            "target": attr,
                            "reason": f"Partial Dependency: Proper subset {sorted(list(S))} of candidate key {sorted(list(K))} determines non-prime attribute '{attr}'."
                        })
    # Remove duplicates from violations list
    unique_violations = []
    seen = set()
    for v in violations:
        # Create a unique key for deduplication
        v_key = (tuple(sorted(list(v["key"]))), tuple(sorted(list(v["subset"]))), v["target"])
        if v_key not in seen:
            seen.add(v_key)
            unique_violations.append(v)
            
    is_2nf = len(unique_violations) == 0
    return is_2nf, unique_violations

def check_3nf(R, fds, candidate_keys, prime_attrs):
    """
    Checks if relation R satisfies 3NF.
    3NF: For every non-trivial FD X -> Y, either X is a superkey, or Y - X is prime.
    """
    violations = []
    for fd in fds:
        lhs = fd["lhs"]
        rhs = fd["rhs"]
        non_trivial_rhs = rhs - lhs
        if not non_trivial_rhs:
            continue
            
        lhs_closure = compute_closure(lhs, fds)
        is_superkey = lhs_closure == R
        
        if not is_superkey:
            non_prime_in_rhs = non_trivial_rhs - prime_attrs
            if non_prime_in_rhs:
                violations.append({
                    "fd": fd,
                    "violators": non_prime_in_rhs,
                    "reason": f"Transitive Dependency: FD {sorted(list(lhs))} -> {sorted(list(rhs))} has non-superkey LHS and contains non-prime attributes {sorted(list(non_prime_in_rhs))} in RHS."
                })
    is_3nf = len(violations) == 0
    return is_3nf, violations

def check_bcnf(R, fds, candidate_keys):
    """
    Checks if relation R satisfies BCNF.
    BCNF: For every non-trivial FD X -> Y, X is a superkey.
    """
    violations = []
    for fd in fds:
        lhs = fd["lhs"]
        rhs = fd["rhs"]
        non_trivial_rhs = rhs - lhs
        if not non_trivial_rhs:
            continue
            
        lhs_closure = compute_closure(lhs, fds)
        is_superkey = lhs_closure == R
        
        if not is_superkey:
            violations.append({
                "fd": fd,
                "reason": f"FD {sorted(list(lhs))} -> {sorted(list(rhs))} violates BCNF because LHS {sorted(list(lhs))} is not a superkey."
            })
    is_bcnf = len(violations) == 0
    return is_bcnf, violations

def check_4nf(R, mvds, fds, candidate_keys):
    """
    Checks if relation R satisfies 4NF.
    4NF: For every non-trivial MVD X ->-> Y, X is a superkey.
    """
    violations = []
    for mvd in mvds:
        lhs = mvd["lhs"]
        rhs = mvd["rhs"]
        
        # Non-trivial MVD: Y is not subset of X, and X U Y != R
        if rhs.issubset(lhs) or (lhs | rhs) == R:
            continue
            
        lhs_closure = compute_closure(lhs, fds)
        is_superkey = lhs_closure == R
        
        if not is_superkey:
            violations.append({
                "mvd": mvd,
                "reason": f"MVD {sorted(list(lhs))} ->-> {sorted(list(rhs))} violates 4NF because LHS {sorted(list(lhs))} is not a superkey."
            })
    is_4nf = len(violations) == 0
    return is_4nf, violations

def check_5nf(R, jds, fds, candidate_keys):
    """
    Checks if relation R satisfies 5NF.
    5NF: For every non-trivial Join Dependency Join(R1, R2, ..., Rk), every Ri is a superkey.
    """
    violations = []
    for jd in jds:
        name = jd["name"]
        components = jd["components"]
        
        # Trivial JD: any component contains all attributes of R
        is_trivial = any(comp == R for comp in components)
        if is_trivial:
            continue
            
        non_superkeys = []
        for comp in components:
            comp_closure = compute_closure(comp, fds)
            if comp_closure != R:
                non_superkeys.append(comp)
                
        if non_superkeys:
            violations.append({
                "jd": jd,
                "non_superkeys": non_superkeys,
                "reason": f"Join Dependency {name} violates 5NF because components {[sorted(list(c)) for c in non_superkeys]} are not superkeys."
            })
            
    is_5nf = len(violations) == 0
    return is_5nf, violations

def find_canonical_cover(R, fds):
    """
    Finds the canonical cover (minimal cover) of FDs.
    """
    cover = []
    # 1. Expand RHS to singletons
    for fd in fds:
        for attr in fd["rhs"]:
            cover.append({"lhs": set(fd["lhs"]), "rhs": {attr}})
            
    # 2. Eliminate extraneous LHS attributes
    changed = True
    while changed:
        changed = False
        for i, fd in enumerate(cover):
            lhs = fd["lhs"]
            rhs = list(fd["rhs"])[0]
            if len(lhs) > 1:
                for attr in list(lhs):
                    reduced_lhs = lhs - {attr}
                    closure = compute_closure(reduced_lhs, cover)
                    if rhs in closure:
                        cover[i] = {"lhs": reduced_lhs, "rhs": {rhs}}
                        changed = True
                        break
            if changed:
                break
                
    # 3. Remove redundant FDs
    i = 0
    while i < len(cover):
        fd = cover[i]
        lhs = fd["lhs"]
        rhs = list(fd["rhs"])[0]
        
        G = cover[:i] + cover[i+1:]
        closure = compute_closure(lhs, G)
        if rhs in closure:
            cover.pop(i)
        else:
            i += 1
            
    # Combine FDs with same LHS
    combined = {}
    for fd in cover:
        lhs_tuple = tuple(sorted(list(fd["lhs"])))
        if lhs_tuple not in combined:
            combined[lhs_tuple] = set()
        combined[lhs_tuple].update(fd["rhs"])
        
    result = [{"lhs": set(lhs), "rhs": rhs} for lhs, rhs in combined.items()]
    result.sort(key=lambda x: (sorted(list(x["lhs"])), sorted(list(x["rhs"]))))
    return result

def decompose_3nf(R, fds, candidate_keys):
    """
    Decomposes relation R into 3NF relations using Bernstein's Synthesis.
    Returns: (list of relation sets, minimal cover FDs, key relation added if any)
    """
    min_cover = find_canonical_cover(R, fds)
    
    relations = []
    for fd in min_cover:
        rel = fd["lhs"] | fd["rhs"]
        if rel not in relations:
            relations.append(rel)
            
    # Check if any relation contains a candidate key
    has_key = False
    for rel in relations:
        for key in candidate_keys:
            if key.issubset(rel):
                has_key = True
                break
        if has_key:
            break
            
    added_key = None
    if not has_key and candidate_keys:
        added_key = candidate_keys[0]
        relations.append(added_key)
        
    # Remove proper subsets
    i = 0
    while i < len(relations):
        rel1 = relations[i]
        is_subset = False
        for j, rel2 in enumerate(relations):
            if i != j and rel1.issubset(rel2):
                is_subset = True
                break
        if is_subset:
            relations.pop(i)
        else:
            i += 1
            
    relations.sort(key=lambda x: sorted(list(x)))
    return relations, min_cover, added_key

def project_fds(R_sub, fds):
    """
    Projects a set of FDs onto a sub-relation R_sub.
    """
    projected = []
    R_sub_list = list(R_sub)
    # Generate all subsets of R_sub to find functional dependencies
    # Limit search size to prevent exponential blowup in large tables
    max_subset_size = min(len(R_sub), 5)
    for r in range(1, max_subset_size + 1):
        for comb in itertools.combinations(R_sub_list, r):
            lhs = set(comb)
            closure = compute_closure(lhs, fds)
            rhs = (closure & R_sub) - lhs
            if rhs:
                projected.append({"lhs": lhs, "rhs": rhs})
                
    return find_canonical_cover(R_sub, projected)

def decompose_bcnf_trace(R_curr, original_fds, trace=None):
    """
    BCNF Decomposition with step-by-step trace of violating FDs.
    Returns: (list of relations, trace list)
    """
    if trace is None:
        trace = []
        
    proj_fds = project_fds(R_curr, original_fds)
    
    violating_fd = None
    for fd in proj_fds:
        lhs = fd["lhs"]
        rhs = fd["rhs"]
        non_trivial_rhs = rhs - lhs
        if not non_trivial_rhs:
            continue
        closure = compute_closure(lhs, proj_fds)
        if not R_curr.issubset(closure):
            violating_fd = fd
            break
            
    if violating_fd is None:
        return [R_curr], trace
        
    X = violating_fd["lhs"]
    Y = violating_fd["rhs"]
    
    R1 = X | Y
    R2 = X | (R_curr - Y)
    
    trace_entry = {
        "relation": R_curr,
        "violating_fd": violating_fd,
        "split_into": (R1, R2)
    }
    trace.append(trace_entry)
    
    sub_rels1, trace = decompose_bcnf_trace(R1, original_fds, trace)
    sub_rels2, trace = decompose_bcnf_trace(R2, original_fds, trace)
    
    return sub_rels1 + sub_rels2, trace

def check_dependency_preservation(D, fds, R):
    """
    Verifies if a decomposition D preserves the original FDs.
    """
    preserved_fds = []
    failed_fds = []
    
    for fd in fds:
        lhs = fd["lhs"]
        rhs = fd["rhs"]
        
        Z = set(lhs)
        while True:
            Z_old = set(Z)
            for Ri in D:
                intersection = Z & Ri
                closure = compute_closure(intersection, fds)
                Z = Z | (closure & Ri)
            if Z == Z_old:
                break
                
        if rhs.issubset(Z):
            preserved_fds.append(fd)
        else:
            failed_fds.append(fd)
            
    is_preserving = len(failed_fds) == 0
    return is_preserving, preserved_fds, failed_fds

def check_lossless_join(D, fds, R):
    """
    Verifies if a decomposition D has a lossless-join property using the Chase Algorithm.
    Returns: (boolean is_lossless, list of dicts representing final Chase table)
    """
    R_list = sorted(list(R))
    D_list = [set(Ri) for Ri in D]
    
    # 1. Initialize Chase Table
    table = []
    for i, Ri in enumerate(D_list):
        row = {}
        for j, attr in enumerate(R_list):
            if attr in Ri:
                row[attr] = f"a_{j}"
            else:
                row[attr] = f"b_{i}_{j}"
        table.append(row)
        
    # 2. Run Chase Equivalence
    changed = True
    iterations = 0
    max_iterations = 100
    
    while changed and iterations < max_iterations:
        changed = False
        iterations += 1
        
        for fd in fds:
            lhs = fd["lhs"]
            rhs = fd["rhs"]
            if not lhs or not rhs:
                continue
                
            # Find partitions of row indices matching on LHS attributes
            partitions = {}
            for idx, row in enumerate(table):
                key = tuple(row[attr] for attr in sorted(list(lhs)))
                if key not in partitions:
                    partitions[key] = []
                partitions[key].append(idx)
                
            # Equate RHS attributes for matching rows
            for key, row_indices in partitions.items():
                if len(row_indices) <= 1:
                    continue
                    
                for attr in rhs:
                    vals = [table[idx][attr] for idx in row_indices]
                    a_vals = [v for v in vals if v.startswith("a_")]
                    
                    if a_vals:
                        target_val = a_vals[0]
                    else:
                        target_val = sorted(vals)[0]
                        
                    for idx in row_indices:
                        if table[idx][attr] != target_val:
                            table[idx][attr] = target_val
                            changed = True
                            
    # 3. Check if any row consists entirely of 'a_' variables
    is_lossless = False
    for row in table:
        row_lossless = True
        for j, attr in enumerate(R_list):
            if row[attr] != f"a_{j}":
                row_lossless = False
                break
        if row_lossless:
            is_lossless = True
            break
            
    return is_lossless, table

def parse_attributes(input_str, R=None):
    """
    Parses a comma/whitespace-separated attribute string into a set.

    If R (the full attribute set of the relation) is provided and every
    attribute in R is a single character, a token with no separators
    (e.g. "ACF") is treated as textbook shorthand for {"A", "C", "F"} instead
    of a single unknown attribute literally named "ACF". This mirrors how
    JDs were already parsed, and prevents KeyError crashes downstream when a
    user (or the AI extractor) writes FDs/MVDs like "ACF -> D".
    """
    import re
    cleaned = re.sub(r'[\(\)\{\}\[\]\,]', ' ', input_str)
    tokens = [x.strip() for x in cleaned.split() if x.strip()]

    if not R:
        return set(tokens)

    all_single_char = all(len(a) == 1 for a in R)
    result = set()
    for tok in tokens:
        if tok in R or not all_single_char or len(tok) <= 1:
            result.add(tok)
        elif all(ch in R for ch in tok):
            result.update(tok)
        else:
            # Leave as-is; caller is responsible for surfacing unknown attributes.
            result.add(tok)
    return result

def parse_fds(input_str, R=None):
    fds = []
    lines = input_str.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '->' in line:
            parts = line.split('->')
            if len(parts) == 2:
                lhs_str, rhs_str = parts
                lhs = parse_attributes(lhs_str, R)
                rhs = parse_attributes(rhs_str, R)
                if lhs and rhs:
                    fds.append({"lhs": lhs, "rhs": rhs})
    return fds

def parse_mvds(input_str, R=None):
    mvds = []
    lines = input_str.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        separator = None
        if '->->' in line:
            separator = '->->'
        elif '-->' in line:
            separator = '-->'
            
        if separator:
            parts = line.split(separator)
            if len(parts) == 2:
                lhs_str, rhs_str = parts
                lhs = parse_attributes(lhs_str, R)
                rhs_parts = rhs_str.split('|')
                for r_part in rhs_parts:
                    rhs = parse_attributes(r_part, R)
                    if lhs and rhs:
                        mvds.append({"lhs": lhs, "rhs": rhs})
    return mvds

def parse_jds(input_str, R):
    import re
    jds = []
    lines = input_str.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = re.search(r'(?:Join)?\s*\((.*)\)', line, re.IGNORECASE)
        if match:
            comps_str = match.group(1)
            comp_parts = comps_str.split(',')
            components = []
            for part in comp_parts:
                part = part.strip()
                if not part:
                    continue
                comp_attrs = parse_attributes(part, R)
                if comp_attrs:
                    components.append(comp_attrs)
            if components:
                jds.append({
                    "name": line,
                    "components": components
                })
    return jds

def find_unknown_attributes(R, fds, mvds, jds):
    """
    Returns the set of attributes referenced anywhere in FDs/MVDs/JDs that are
    NOT part of R. Callers should surface this to the user and avoid running
    engine checks (candidate keys, closures, chase, etc.) when it's non-empty,
    since those functions assume every referenced attribute exists in R.
    """
    unknown = set()
    for fd in fds:
        unknown |= (fd["lhs"] | fd["rhs"]) - R
    for mvd in mvds:
        unknown |= (mvd["lhs"] | mvd["rhs"]) - R
    for jd in jds:
        for comp in jd["components"]:
            unknown |= comp - R
    return unknown

def discover_fds_from_dataframe(df, max_lhs_size=2):
    """
    Discovers all minimal functional dependencies holding in a pandas DataFrame.
    df: pandas DataFrame
    max_lhs_size: maximum size of LHS attribute sets to search
    """
    import itertools
    
    # Clean dataframe: drop completely empty rows, convert to string
    df = df.dropna(how='all')
    df = df.astype(str)
    
    columns = list(df.columns)
    fds = []
    
    for A in columns:
        other_cols = [c for c in columns if c != A]
        
        # Check if A is constant
        if df[A].nunique() <= 1:
            fds.append({"lhs": set(), "rhs": {A}})
            continue
            
        found_for_A = []
        
        for r in range(1, min(len(other_cols) + 1, max_lhs_size + 1)):
            for comb in itertools.combinations(other_cols, r):
                lhs = set(comb)
                
                # Check for redundancy
                is_redundant = False
                for prev_lhs in found_for_A:
                    if prev_lhs.issubset(lhs):
                        is_redundant = True
                        break
                if is_redundant:
                    continue
                    
                # Check LHS -> A dependency
                lhs_list = list(lhs)
                unique_lhs = df.drop_duplicates(subset=lhs_list)
                unique_lhs_and_A = df.drop_duplicates(subset=lhs_list + [A])
                
                if len(unique_lhs) == len(unique_lhs_and_A):
                    fds.append({"lhs": lhs, "rhs": {A}})
                    found_for_A.append(lhs)
                    
    # Combine FDs with same LHS
    combined = {}
    for fd in fds:
        lhs_key = tuple(sorted(list(fd["lhs"])))
        if lhs_key not in combined:
            combined[lhs_key] = set()
        combined[lhs_key].update(fd["rhs"])
        
    result = [{"lhs": set(lhs), "rhs": rhs} for lhs, rhs in combined.items()]
    result.sort(key=lambda x: (sorted(list(x["lhs"])), sorted(list(x["rhs"]))))
    return result
