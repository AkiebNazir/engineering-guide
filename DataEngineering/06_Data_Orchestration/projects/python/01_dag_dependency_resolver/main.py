def topological_sort(dag):
    in_degree = {u: 0 for u in dag}
    for u in dag:
        for v in dag[u]:
            if v not in in_degree:
                in_degree[v] = 0
            in_degree[v] += 1

    queue = [u for u in in_degree if in_degree[u] == 0]
    order = []

    while queue:
        u = queue.pop(0)
        order.append(u)
        for v in dag.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    if len(order) == len(in_degree):
        return order
    else:
        raise ValueError("Graph has a cycle")

if __name__ == "__main__":
    dag = {
        'A': ['B', 'C'],
        'B': ['D'],
        'C': ['D'],
        'D': ['E'],
        'E': []
    }
    
    print("DAG:")
    for k, v in dag.items():
        print(f"  {k} -> {v}")
    
    print("\nExecution Order:")
    try:
        order = topological_sort(dag)
        print(" -> ".join(order))
    except ValueError as e:
        print(e)
