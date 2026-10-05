/*
LAB 06 (advanced) - Operation contracts: a persisted-operation manifest as the contract, schema checks in CI
============================================================================================================
You will learn

  - that a GraphQL client's CONTRACT is already written down: the operations it sends. Build
    tools (Relay compiler, GraphQL Codegen, Apollo's persisted-query manifests) extract them at
    client build time into a MANIFEST of {sha256 -> document}, tagged with the client version

  - the manifest does two jobs at once:
    1. at runtime it is the ALLOWLIST (lab 05): production only executes hashes it knows
    2. in the provider's CI it is the list of contracts every schema change is checked against

  - a schema DIFF written from scratch over graphql-go's TypeMap: removed types/fields/enum
    values, changed field types, new required arguments (breaking); new enum values and
    changed defaults (dangerous)

  - USAGE: walking each operation with graphql.TypeInfo gives the exact schema coordinates it
    touches (Type.field), so a breaking change blocks only when a LIVE client uses it

  - validating every registered operation with graphql.ValidateDocument against the proposed
    schema: the independent second check (catches arguments that became required)

  - a DEPRECATION report: which client versions still read each @deprecated field, i.e. who
    must upgrade before the field can go

    client build --extract ops--> manifest (hash, doc, client@version) --upload--> registry
    |
    provider PR --proposed schema--> [ diff x usage ] + [ validate every op ] --> pass / block

Run it   go run ./GraphQL/labs/golang/06_operation_contracts_and_schema_checks
Twin     python GraphQL/labs/python/06_contract_testing_operations.py (Pact-style response checks)
*/
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"

	"github.com/graphql-go/graphql"
	"github.com/graphql-go/graphql/language/ast"
	"github.com/graphql-go/graphql/language/parser"
	"github.com/graphql-go/graphql/language/source"
	"github.com/graphql-go/graphql/language/visitor"
)

// ============================================================ schema versions ===
// One builder with switches, so every "proposal" is a small, readable delta from v1.
type opts struct {
	dropPrice        bool // remove Product.price
	addPriceMoney    bool // add Product.priceMoney, deprecate price
	dropWeight       bool // remove Product.weightGrams (nobody reads it)
	requireFirst     bool // products(first: Int!) without a default
	nullableDesc     bool // description: String! -> String
	addArchivedValue bool // enum Status gains ARCHIVED
}

func buildSchema(o opts) graphql.Schema {
	statusValues := graphql.EnumValueConfigMap{"ACTIVE": {Value: "ACTIVE"}, "DISCONTINUED": {Value: "DISCONTINUED"}}
	if o.addArchivedValue {
		statusValues["ARCHIVED"] = &graphql.EnumValueConfig{Value: "ARCHIVED"}
	}
	status := graphql.NewEnum(graphql.EnumConfig{Name: "Status", Values: statusValues})
	money := graphql.NewObject(graphql.ObjectConfig{Name: "Money", Fields: graphql.Fields{
		"amount": {Type: graphql.NewNonNull(graphql.Int)}, "currency": {Type: graphql.NewNonNull(graphql.String)},
	}})
	var desc graphql.Output = graphql.NewNonNull(graphql.String)
	if o.nullableDesc {
		desc = graphql.String
	}
	fields := graphql.Fields{
		"id":          {Type: graphql.NewNonNull(graphql.ID)},
		"name":        {Type: graphql.NewNonNull(graphql.String)},
		"description": {Type: desc},
		"status":      {Type: graphql.NewNonNull(status)},
	}
	if !o.dropPrice {
		fields["price"] = &graphql.Field{Type: graphql.NewNonNull(graphql.Int)}
		if o.addPriceMoney {
			fields["price"].DeprecationReason = "use priceMoney"
		}
	}
	if o.addPriceMoney {
		fields["priceMoney"] = &graphql.Field{Type: graphql.NewNonNull(money)}
	}
	if !o.dropWeight {
		fields["weightGrams"] = &graphql.Field{Type: graphql.Int}
	}
	product := graphql.NewObject(graphql.ObjectConfig{Name: "Product", Fields: fields})

	first := &graphql.ArgumentConfig{Type: graphql.Int, DefaultValue: 10}
	if o.requireFirst {
		first = &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.Int)}
	}
	query := graphql.NewObject(graphql.ObjectConfig{Name: "Query", Fields: graphql.Fields{
		"product":  {Type: product, Args: graphql.FieldConfigArgument{"id": {Type: graphql.NewNonNull(graphql.ID)}}},
		"products": {Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(product))), Args: graphql.FieldConfigArgument{"first": first}},
	}})
	s, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		panic(err)
	}
	return s
}

// ================================================================= manifest ===
type Op struct {
	Client, Name, Doc, Hash string
}

func manifest(client string, docs map[string]string) []Op {
	var out []Op
	for name, doc := range docs {
		h := sha256.Sum256([]byte(doc))
		out = append(out, Op{client, name, doc, hex.EncodeToString(h[:])})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out
}

func parse(doc string) *ast.Document {
	d, err := parser.Parse(parser.ParseParams{Source: source.NewSource(&source.Source{Body: []byte(doc)})})
	if err != nil {
		panic(err)
	}
	return d
}

// coordinates walks an operation with TypeInfo, which tracks "which type am I inside" through
// nesting, aliases and fragments, so `p: product { ... }` still records Query.product.
func coordinates(s *graphql.Schema, doc string) map[string]bool {
	used := map[string]bool{}
	ti := graphql.NewTypeInfo(&graphql.TypeInfoConfig{Schema: s})
	visitor.Visit(parse(doc), visitor.VisitWithTypeInfo(ti, &visitor.VisitorOptions{
		KindFuncMap: map[string]visitor.NamedVisitFuncs{
			"Field": {Kind: func(p visitor.VisitFuncParams) (string, interface{}) {
				if f, ok := p.Node.(*ast.Field); ok && ti.ParentType() != nil {
					used[ti.ParentType().Name()+"."+f.Name.Value] = true
				}
				return visitor.ActionNoChange, nil
			}},
		},
	}), nil)
	return used
}

// ============================================================== schema diff ===
type Change struct {
	Breaking bool
	Coord    string // Type.field (or Type for a whole type)
	What     string
}

func fieldsOf(t graphql.Type) graphql.FieldDefinitionMap {
	if o, ok := t.(*graphql.Object); ok {
		return o.Fields()
	}
	return nil
}

func diff(old, new graphql.Schema) []Change {
	var out []Change
	names := make([]string, 0)
	for n := range old.TypeMap() {
		if !strings.HasPrefix(n, "__") {
			names = append(names, n)
		}
	}
	sort.Strings(names)
	for _, tn := range names {
		ot, nt := old.TypeMap()[tn], new.TypeMap()[tn]
		if nt == nil {
			out = append(out, Change{true, tn, "type removed"})
			continue
		}
		if oe, ok := ot.(*graphql.Enum); ok {
			ne := nt.(*graphql.Enum)
			have := map[string]bool{}
			for _, v := range ne.Values() {
				have[v.Name] = true
			}
			for _, v := range oe.Values() {
				if !have[v.Name] {
					out = append(out, Change{true, tn + "." + v.Name, "enum value removed"})
				}
				delete(have, v.Name)
			}
			for v := range have {
				out = append(out, Change{false, tn, "enum value " + v + " added (exhaustive switches break)"})
			}
		}
		of, nf := fieldsOf(ot), fieldsOf(nt)
		fnames := make([]string, 0, len(of))
		for n := range of {
			fnames = append(fnames, n)
		}
		sort.Strings(fnames)
		for _, fn := range fnames {
			coord := tn + "." + fn
			o, n := of[fn], nf[fn]
			if n == nil {
				out = append(out, Change{true, coord, "field removed"})
				continue
			}
			if o.Type.String() != n.Type.String() {
				out = append(out, Change{true, coord, fmt.Sprintf("type %s -> %s", o.Type, n.Type)})
			}
			oldArgs := map[string]*graphql.Argument{}
			for _, a := range o.Args {
				oldArgs[a.Name()] = a
			}
			for _, a := range n.Args {
				oa := oldArgs[a.Name()]
				_, required := a.Type.(*graphql.NonNull)
				required = required && a.DefaultValue == nil
				switch {
				case oa == nil && required:
					out = append(out, Change{true, coord, "new required argument " + a.Name()})
				case oa != nil && required && (oa.DefaultValue != nil || fmt.Sprint(oa.Type) != fmt.Sprint(a.Type)):
					out = append(out, Change{true, coord, fmt.Sprintf("argument %s is now required", a.Name())})
				case oa != nil && fmt.Sprint(oa.DefaultValue) != fmt.Sprint(a.DefaultValue):
					out = append(out, Change{false, coord, fmt.Sprintf("default of %s changed", a.Name())})
				}
			}
		}
	}
	return out
}

// ==================================================================== check ===
func check(prod, proposed graphql.Schema, ops []Op) (bool, []string) {
	ok := true
	var lines []string
	usage := make([]map[string]bool, len(ops))
	for i, op := range ops {
		usage[i] = coordinates(&prod, op.Doc)
	}
	for _, c := range diff(prod, proposed) {
		var users []string
		for i, op := range ops {
			if usage[i][c.Coord] {
				users = append(users, op.Client+" "+op.Name)
			}
		}
		switch {
		case !c.Breaking:
			lines = append(lines, fmt.Sprintf("warning   %-20s %s", c.Coord, c.What))
		case len(users) > 0:
			ok = false
			lines = append(lines, fmt.Sprintf("BREAKING  %-20s %s; used by %s", c.Coord, c.What, strings.Join(users, ", ")))
		default:
			lines = append(lines, fmt.Sprintf("unused    %-20s %s; no registered operation reads it", c.Coord, c.What))
		}
	}
	for _, op := range ops {
		res := graphql.ValidateDocument(&proposed, parse(op.Doc), graphql.SpecifiedRules)
		if !res.IsValid {
			ok = false
			lines = append(lines, fmt.Sprintf("INVALID   %s %s: %s", op.Client, op.Name, res.Errors[0].Message))
		}
	}
	return ok, lines
}

func must(cond bool, msg string) {
	if !cond {
		panic("FAILED: " + msg)
	}
}

func has(lines []string, prefix, contains string) bool {
	for _, l := range lines {
		if strings.HasPrefix(l, prefix) && strings.Contains(l, contains) {
			return true
		}
	}
	return false
}

func main() {
	v1 := buildSchema(opts{})
	web := manifest("web@3.4", map[string]string{
		"ProductPage": `query ProductPage($id: ID!) { product(id: $id) { id name price description } }`,
		"Teaser":      `query Teaser($id: ID!) { p: product(id: $id) { ...Brief } } fragment Brief on Product { name }`,
	})
	ios := manifest("ios@7.1", map[string]string{
		"Catalogue": `query Catalogue { products { id name description status } }`,
	})
	registry := append(append([]Op{}, web...), ios...)

	fmt.Println("== 1. the manifest: what each client build shipped ==")
	for _, op := range registry {
		used := coordinates(&v1, op.Doc)
		keys := make([]string, 0, len(used))
		for k := range used {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		fmt.Printf("   %s  %-8s %-12s %v\n", op.Hash[:12], op.Client, op.Name, keys)
	}
	must(coordinates(&v1, web[1].Doc)["Query.product"] && coordinates(&v1, web[1].Doc)["Product.name"],
		"alias + fragment resolved to real coordinates")

	fmt.Println("\n== 2. at runtime the same manifest is the allowlist ==")
	allowed := map[string]bool{}
	for _, op := range registry {
		allowed[op.Hash] = true
	}
	evil := sha256.Sum256([]byte(`{ products(first: 100000) { id } }`))
	fmt.Printf("   known hash %s... -> execute;  ad-hoc query %s... -> PersistedQueryNotFound\n",
		registry[0].Hash[:8], hex.EncodeToString(evil[:])[:8])
	must(allowed[registry[0].Hash] && !allowed[hex.EncodeToString(evil[:])], "allowlist")

	proposals := []struct {
		name   string
		o      opts
		wantOK bool
		expect func([]string) bool
	}{
		{"A. add priceMoney, deprecate price", opts{addPriceMoney: true}, true,
			func(l []string) bool { return len(l) == 0 }},
		{"B. remove Product.price", opts{dropPrice: true}, false,
			func(l []string) bool { return has(l, "BREAKING", "web@3.4 ProductPage") }},
		{"C. remove Product.weightGrams", opts{dropWeight: true}, true,
			func(l []string) bool { return has(l, "unused", "Product.weightGrams") }},
		{"D. products(first: Int!) with no default", opts{requireFirst: true}, false,
			func(l []string) bool { return has(l, "INVALID", "ios@7.1 Catalogue") }},
		{"E. description String! -> String", opts{nullableDesc: true}, false,
			func(l []string) bool { return has(l, "BREAKING", "ios@7.1") && !has(l, "INVALID", "") }},
		{"F. Status gains ARCHIVED", opts{addArchivedValue: true}, true,
			func(l []string) bool { return has(l, "warning", "ARCHIVED") }},
	}
	fmt.Println("\n== 3. schema checks on proposed changes (diff x usage + validate every op) ==")
	for _, p := range proposals {
		ok, lines := check(v1, buildSchema(p.o), registry)
		fmt.Printf("\n-- %s --\n", p.name)
		if len(lines) == 0 {
			fmt.Println("   no changes that affect clients")
		}
		for _, l := range lines {
			fmt.Println("   " + l)
		}
		verdict := "PASS"
		if !ok {
			verdict = "BLOCKED"
		}
		fmt.Println("   => " + verdict)
		must(ok == p.wantOK && p.expect(lines), p.name)
	}
	fmt.Println("\n   C passes although a plain diff calls it breaking; E fails although every")
	fmt.Println("   operation still validates. You need BOTH the usage-aware diff and validation.")

	fmt.Println("\n== 4. deprecation report: who must upgrade before price can go ==")
	expanded := buildSchema(opts{addPriceMoney: true})
	for tn, t := range expanded.TypeMap() {
		for fn, f := range fieldsOf(t) {
			if f.DeprecationReason == "" || strings.HasPrefix(tn, "__") {
				continue
			}
			var users []string
			for _, op := range registry {
				if coordinates(&expanded, op.Doc)[tn+"."+fn] {
					users = append(users, op.Client+" "+op.Name)
				}
			}
			fmt.Printf("   %s.%s (%s): still read by %v\n", tn, fn, f.DeprecationReason, users)
			must(len(users) == 1 && users[0] == "web@3.4 ProductPage", "one reader left")
		}
	}
	web35 := manifest("web@3.5", map[string]string{
		"ProductPage": `query ProductPage($id: ID!) { product(id: $id) { id name priceMoney { amount currency } description } }`,
	})
	contracted := buildSchema(opts{addPriceMoney: true, dropPrice: true})
	okWhileOld, _ := check(expanded, contracted, registry)
	okAfter, _ := check(expanded, contracted, append(append([]Op{}, ios...), web35...))
	fmt.Printf("   drop price while web@3.4 is live: %v;  after web@3.4 is retired: %v\n", okWhileOld, okAfter)
	must(!okWhileOld && okAfter, "contract step gated on the registry")

	fmt.Println("\nOK")
}
