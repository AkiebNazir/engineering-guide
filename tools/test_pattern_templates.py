"""
Run every template in webapp/static/dsa-patterns.js against real test cases.

The pattern playbooks show these templates as "write this from memory" code,
so each one must actually run and give the right answers. Randomised checks
compare against a brute force where one is cheap. Pure Python — the JS file is
parsed with a regex, no node needed.

    python3 tools/test_pattern_templates.py        # prints "51 templates passed"
"""
import collections, itertools, random, re, sys
from pathlib import Path

JS = Path(__file__).resolve().parent.parent / "webapp" / "static" / "dsa-patterns.js"


def load_playbooks():
    text = JS.read_text()
    out = {}
    # topic blocks start with  '<NN_slug>': {  at two-space indent
    parts = re.split(r"\n  '(\d\d_[a-z0-9_]+)': \{", text)
    for topic, body in zip(parts[1::2], parts[2::2]):
        tpls = re.findall(r"title: '((?:[^'\\]|\\.)*)',\s*code: String\.raw`(.*?)`", body, re.S)
        out[topic] = {"templates": [{"title": t, "code": c} for t, c in tpls]}
    return out


pb = load_playbooks()


PRELUDE = '''
class ListNode:
    def __init__(self, val=0, next=None): self.val, self.next = val, next
class TreeNode:
    def __init__(self, val=0, left=None, right=None): self.val, self.left, self.right = val, left, right
def ll(xs):
    head = None
    for x in reversed(xs): head = ListNode(x, head)
    return head
def lv(h):
    out = []
    while h: out.append(h.val); h = h.next
    return out
def tree(xs):
    if not xs: return None
    nodes = [None if x is None else TreeNode(x) for x in xs]
    kids = nodes[::-1]; root = kids.pop()
    for n in nodes:
        if n:
            if kids: n.left = kids.pop()
            if kids: n.right = kids.pop()
    return root
'''

TESTS = {
 '01_arrays_hashing': ['''
assert two_sum([2,7,11,15], 9) == [0,1]
assert two_sum([3,2,4], 6) == [1,2]
assert two_sum([3,3], 6) == [0,1]
''', '''
g = sorted(sorted(x) for x in group_anagrams(["eat","tea","tan","ate","nat","bat"]))
assert g == [["ate","eat","tea"],["bat"],["nat","tan"]], g
'''],
 '02_two_pointers': ['''
assert two_sum_sorted([2,7,11,15], 9) == [0,1]
assert two_sum_sorted([1,3,4,6], 10) == [2,3]
''', '''
a=[0,0,1,1,1,2,2,3,3,4]; k=remove_duplicates(a); assert k==5 and a[:k]==[0,1,2,3,4]
'''],
 '03_sliding_window': ['''
assert longest_at_most_k_distinct("eceba", 2) == 3
assert longest_at_most_k_distinct("aa", 1) == 2
for _ in range(300):
    s=''.join(random.choice('abc') for _ in range(random.randint(0,12))); k=random.randint(0,3)
    brute=max([j-i for i in range(len(s)+1) for j in range(i,len(s)+1) if len(set(s[i:j]))<=k] or [0])
    assert longest_at_most_k_distinct(s,k)==brute,(s,k)
''', '''
assert max_sum_fixed([1,12,-5,-6,50,3], 4) == 51
'''],
 '04_prefix_sum': ['''
assert subarray_sum_equals_k([1,1,1], 2) == 2
assert subarray_sum_equals_k([1,2,3], 3) == 2
for _ in range(300):
    a=[random.randint(-3,3) for _ in range(random.randint(0,10))]; k=random.randint(-3,3)
    assert subarray_sum_equals_k(a,k)==sum(1 for i in range(len(a)) for j in range(i+1,len(a)+1) if sum(a[i:j])==k)
''', '''
r=RangeSum([-2,0,3,-5,2,-1]); assert r.query(0,2)==1 and r.query(2,5)==-1 and r.query(0,5)==-3
'''],
 '05_binary_search': ['''
a=[1,3,3,5,8]
assert first_true(0, 4, lambda i: a[i] >= 3) == 1
assert first_true(0, 4, lambda i: a[i] >= 9) == 5
assert first_true(0, 4, lambda i: a[i] >= 0) == 0
''', '''
assert min_eating_speed([3,6,7,11], 8) == 4
assert min_eating_speed([30,11,23,4,20], 5) == 30
assert min_eating_speed([30,11,23,4,20], 6) == 23
'''],
 '06_stack': ['''
assert next_greater([2,1,2,4,3]) == [4,2,4,-1,-1]
''', '''
assert is_valid("()[]{}") and is_valid("{[]}") and not is_valid("(]") and not is_valid("([)]") and not is_valid("(")
'''],
 '07_queue_deque': ['''
q=MyQueue(); q.push(1); q.push(2); assert q.peek()==1; assert q.pop()==1; q.push(3); assert q.pop()==2; assert q.pop()==3; assert q.empty()
''', '''
assert max_sliding_window([1,3,-1,-3,5,3,6,7], 3) == [3,3,5,5,6,7]
assert max_sliding_window([5,5,1], 2) == [5,5]
'''],
 '08_linked_list': ['''
assert lv(reverse_list(ll([1,2,3,4,5]))) == [5,4,3,2,1]
assert reverse_list(None) is None
''', '''
assert middle_node(ll([1,2,3,4,5])).val == 3 and middle_node(ll([1,2,3,4,5,6])).val == 4
h=ll([3,2,0,-4]); t=h
while t.next: t=t.next
t.next=h.next; assert has_cycle(h) and not has_cycle(ll([1,2]))
'''],
 '09_recursion_backtracking': ['''
assert sorted(map(tuple,subsets([1,2,3]))) == sorted(tuple(c) for r in range(4) for c in itertools.combinations([1,2,3],r))
''', '''
assert sorted(map(tuple,permutations([1,2,3]))) == sorted(itertools.permutations([1,2,3]))
'''],
 '10_trees': ['''
assert diameter(tree([1,2,3,4,5])) == 3 and diameter(tree([1,2])) == 1
''', '''
assert level_order(tree([3,9,20,None,None,15,7])) == [[3],[9,20],[15,7]] and level_order(None) == []
'''],
 '11_binary_search_tree': ['''
assert is_valid_bst(tree([2,1,3])) and not is_valid_bst(tree([5,1,4,None,None,3,6])) and not is_valid_bst(tree([5,4,6,None,None,3,7]))
''', '''
assert kth_smallest(tree([3,1,4,None,2]), 1) == 1 and kth_smallest(tree([5,3,6,2,4,None,None,1]), 3) == 3
'''],
 '12_heap_priority_queue': ['''
assert kth_largest([3,2,1,5,6,4], 2) == 5 and kth_largest([3,2,3,1,2,4,5,5,6], 4) == 4
''', '''
m=MedianFinder()
xs=[5,15,1,3,8,7,9,10,20,2]; seen=[]
for x in xs:
    m.addNum(x); seen.append(x); s=sorted(seen); n=len(s)
    med = s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2
    assert m.findMedian()==med
'''],
 '13_trie': ['''
t=Trie(); t.insert("apple"); assert t.search("apple") and not t.search("app") and t.startsWith("app")
t.insert("app"); assert t.search("app") and not t.startsWith("b")
'''],
 '14_graphs': ['''
g=[list("11110"),list("11010"),list("11000"),list("00000")]; assert num_islands(g)==1
g=[list("11000"),list("11000"),list("00100"),list("00011")]; assert num_islands(g)==3
''', '''
grid=[[0,0,0],[1,1,0],[0,0,0]]
assert shortest_steps(grid,(0,0),(2,0))==6 and shortest_steps([[0,1],[1,0]],(0,0),(1,1))==-1
''', '''
o=topo_order(4,[(1,0),(2,0),(3,1),(3,2)]); pos={v:i for i,v in enumerate(o)}
assert len(o)==4 and pos[1]<pos[0] and pos[2]<pos[0] and pos[3]<pos[1]
assert topo_order(2,[(0,1),(1,0)])==[]
'''],
 '15_advanced_graphs': ['''
d=DSU(5); assert d.union(0,1) and d.union(1,2) and not d.union(0,2) and d.find(3)!=d.find(0)
''', '''
assert dijkstra(4,[(1,0,1),(1,2,1),(2,3,1)],1) == [1,0,1,2]
assert dijkstra(3,[(0,1,4),(0,2,1),(2,1,1)],0) == [0,2,1]
'''],
 '16_dp_1d': ['''
assert rob([1,2,3,1])==4 and rob([2,7,9,3,1])==12 and rob([])==0
''', '''
assert coin_change([1,2,5],11)==3 and coin_change([2],3)==-1 and coin_change([1],0)==0
'''],
 '17_dp_2d': ['''
assert lcs("abcde","ace")==3 and lcs("abc","def")==0
''', '''
assert unique_paths(3,7)==28 and unique_paths(3,2)==3 and unique_paths(1,1)==1
'''],
 '18_greedy': ['''
assert max_subarray([-2,1,-3,4,-1,2,1,-5,4])==6 and max_subarray([-3,-1,-2])==-1
''', '''
assert can_jump([2,3,1,1,4]) and not can_jump([3,2,1,0,4])
'''],
 '19_intervals': ['''
assert merge([[1,3],[2,6],[8,10],[15,18]])==[[1,6],[8,10],[15,18]] and merge([[1,4],[2,3]])==[[1,4]]
''', '''
assert min_meeting_rooms([[0,30],[5,10],[15,20]])==2 and min_meeting_rooms([[7,10],[2,4]])==1 and min_meeting_rooms([[1,5],[5,10]])==1
'''],
 '20_bit_manipulation': ['''
assert single_number([4,1,2,1,2])==4 and count_set_bits(11)==3 and count_set_bits(128)==1
'''],
 '21_math_geometry': ['''
assert abs(my_pow(2.0,10)-1024)<1e-9 and abs(my_pow(2.0,-2)-0.25)<1e-12 and my_pow(3,0)==1
''', '''
assert reverse_digits(1230)==321 and reverse_digits(7)==7
'''],
 '22_sorting_algorithms': ['''
for _ in range(200):
    a=[random.randint(-5,5) for _ in range(random.randint(0,15))]; assert merge_sort(a)==sorted(a)
''', '''
for _ in range(200):
    a=[random.randint(0,2) for _ in range(random.randint(0,15))]; b=a[:]; sort_colors(b); assert b==sorted(a)
'''],
 '23_string_algorithms': ['''
assert prefix_function("aabaaab")==[0,1,0,1,2,2,3]
for _ in range(400):
    t=''.join(random.choice('ab') for _ in range(random.randint(0,10))); p=''.join(random.choice('ab') for _ in range(random.randint(0,4)))
    assert find(t,p)==t.find(p),(t,p)
'''],
 '24_matrix': ['''
assert spiral_order([[1,2,3],[4,5,6],[7,8,9]])==[1,2,3,6,9,8,7,4,5]
assert spiral_order([[1,2,3,4],[5,6,7,8],[9,10,11,12]])==[1,2,3,4,8,12,11,10,9,5,6,7]
assert spiral_order([[1],[2],[3]])==[1,2,3] and spiral_order([[1,2,3]])==[1,2,3]
''', '''
m=[[1,2,3],[4,5,6],[7,8,9]]; rotate(m); assert m==[[7,4,1],[8,5,2],[9,6,3]]
'''],
 '25_design': ['''
c=LRUCache(2); c.put(1,1); c.put(2,2); assert c.get(1)==1; c.put(3,3); assert c.get(2)==-1; c.put(4,4)
assert c.get(1)==-1 and c.get(3)==3 and c.get(4)==4
c=LRUCache(2); c.put(2,1); c.put(2,2); assert c.get(2)==2; c.put(1,1); c.put(4,1); assert c.get(2)==-1
'''],
 '26_segment_tree_fenwick': ['''
a=[1,3,5]; f=Fenwick(3)
for i,x in enumerate(a): f.add(i,x)
assert f.range_sum(0,2)==9; f.add(1,2-3); assert f.range_sum(0,2)==8 and f.range_sum(1,1)==2
for _ in range(100):
    n=random.randint(1,12); a=[0]*n; f=Fenwick(n)
    for _ in range(20):
        i=random.randrange(n); d=random.randint(-5,5); a[i]+=d; f.add(i,d)
        l=random.randrange(n); r=random.randrange(l,n); assert f.range_sum(l,r)==sum(a[l:r+1])
'''],
 '27_algorithms': ['''
random.seed(1)
cnt=collections.Counter(tuple(shuffle([1,2,3])) for _ in range(60000))
assert len(cnt)==6 and max(cnt.values())/min(cnt.values())<1.1, cnt
cnt=collections.Counter(reservoir_pick(iter(range(5))) for _ in range(50000))
assert len(cnt)==5 and max(cnt.values())/min(cnt.values())<1.1, cnt
'''],
 '28_recursion_backtracking': ['''
assert rob_tree(tree([3,2,3,None,3,None,1]))==7 and rob_tree(tree([3,4,5,1,3,None,1]))==9
''', '''
assert [num_trees(n) for n in range(1,8)]==[1,2,5,14,42,132,429]
'''],
}

fails = 0; ran = 0
for t, p in pb.items():
    tests = TESTS[t]
    assert len(tests) == len(p['templates']), (t, len(tests), len(p['templates']))
    for tpl, test in zip(p['templates'], tests):
        g = {}
        try:
            exec(compile("import random, itertools, collections\n" + PRELUDE + tpl['code'] + "\n" + test, f'{t}:{tpl["title"]}', 'exec'), g)
            ran += 1
        except Exception as e:
            fails += 1; print('FAIL', t, tpl['title'], repr(e))
print(f'{ran} templates passed, {fails} failed')
sys.exit(1 if fails or not ran else 0)
