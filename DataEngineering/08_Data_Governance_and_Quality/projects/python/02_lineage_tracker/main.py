class LineageNode:
    def __init__(self, name):
        self.name = name
        self.downstream = []

    def add_downstream(self, node):
        self.downstream.append(node)

    def print_lineage(self, level=0):
        print("  " * level + "-> " + self.name)
        for child in self.downstream:
            child.print_lineage(level + 1)

raw = LineageNode("raw_transactions")
stg = LineageNode("stg_transactions")
fct = LineageNode("fct_daily_sales")
mart = LineageNode("mart_finance_dashboard")

raw.add_downstream(stg)
stg.add_downstream(fct)
fct.add_downstream(mart)

print("Data Lineage Graph:")
raw.print_lineage()
