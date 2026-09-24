/*
FOUNDATION LEVEL 04 - Nested object types: resolvers calling resolvers
=========================================================================
Every field so far returned a scalar - a leaf. The moment a field returns an
OBJECT type, the client must say which of that object's fields it wants, and
the response grows a level deeper. This is where GraphQL stops looking like a
function call and starts looking like a graph: one query walks from a report,
to its owner, to that owner's team, in one round trip.

THE ONE IDEA TO TAKE AWAY - the resolver chain:

	A resolver's return value becomes the SOURCE (p.Source) of the resolvers
	one level down. `report` returns a Report; the `owner` field's resolver
	then runs with that Report as p.Source, and returns a User; the `team`
	resolver runs with that User as p.Source. Nobody passes anything
	explicitly. Each resolver only knows about its own parent.

	That also means depth costs work: a nested field's resolver runs once per
	parent object. Three reports, each with an owner, is 1 + 3 resolver calls -
	and if each owner hit a database that would be the famous N+1 problem
	(solved with dataloaders in ../labs/, deliberately out of scope here).

You will learn
  - how to define an object type (NewObject) and return it from a field
  - that selecting an object requires selecting fields INSIDE it
  - the resolver chain: parent return value -> child resolver's p.Source
  - that a field with no Resolve uses the DEFAULT resolver: read the
    same-named field off the parent struct
  - that nested fields can take arguments too, at any depth

Run it   go run ./GraphQL/Foundation/golang/04_nested_object_types
*/
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/graphql-go/graphql"
)

// The internal data model. Note OwnerID and TeamID: they exist in our data
// but are NOT part of the schema, because they are our plumbing, not the
// client's business. The graph hides them behind `owner` and `team`.
type Team struct {
	Name   string
	Region string
}

type User struct {
	Name   string
	Email  string
	TeamID string
}

type Report struct {
	ID      string
	Title   string
	OwnerID string
}

var (
	teams   = map[string]Team{"t1": {Name: "platform", Region: "eu-west"}}
	usersDB = map[string]User{"u1": {Name: "Ada", Email: "ada@example.com", TeamID: "t1"}}
	reports = []Report{
		{ID: "r1", Title: "Q1 uptime", OwnerID: "u1"},
		{ID: "r2", Title: "Q2 uptime", OwnerID: "u1"},
	}
	calls = map[string]int{}
)

func buildSchema() graphql.Schema {
	// Fields with no Resolve use the DEFAULT resolver: "read the field of the
	// same name off p.Source". Most fields in real schemas are exactly this.
	teamType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Team",
		Fields: graphql.Fields{
			"name":   {Type: graphql.NewNonNull(graphql.String)},
			"region": {Type: graphql.NewNonNull(graphql.String)},
		},
	})

	userType := graphql.NewObject(graphql.ObjectConfig{
		Name: "User",
		Fields: graphql.Fields{
			"name":  {Type: graphql.NewNonNull(graphql.String)},
			"email": {Type: graphql.NewNonNull(graphql.String)},
			"team": {
				Type: graphql.NewNonNull(teamType),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					// p.Source here is the User that `owner` returned.
					calls["team"]++
					return teams[p.Source.(User).TeamID], nil
				},
			},
		},
	})

	reportType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Report",
		Fields: graphql.Fields{
			"id":    {Type: graphql.NewNonNull(graphql.ID)},
			"title": {Type: graphql.NewNonNull(graphql.String)},
			"owner": {
				Type: graphql.NewNonNull(userType),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					// p.Source is the Report that the parent field returned.
					// This resolver runs ONCE PER REPORT in the parent list.
					calls["owner"]++
					return usersDB[p.Source.(Report).OwnerID], nil
				},
			},
			"summary": {
				// Nested fields take arguments exactly like top-level ones do.
				Type: graphql.NewNonNull(graphql.String),
				Args: graphql.FieldConfigArgument{
					"maxLength": {Type: graphql.Int, DefaultValue: 10},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					title := p.Source.(Report).Title
					if n := p.Args["maxLength"].(int); n < len(title) {
						return title[:n], nil
					}
					return title, nil
				},
			},
		},
	})

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"reports": {
				Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(reportType))),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					return reports, nil
				},
			},
			"report": {
				Type: reportType, // nullable: an unknown id is null, not an error
				Args: graphql.FieldConfigArgument{
					"id": {Type: graphql.NewNonNull(graphql.ID)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					for _, r := range reports {
						if r.ID == p.Args["id"].(string) {
							return r, nil
						}
					}
					return nil, nil
				},
			},
		},
	})

	schema, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		log.Fatal(err)
	}
	return schema
}

func run(schema graphql.Schema, title, query string) *graphql.Result {
	result := graphql.Do(graphql.Params{Schema: schema, RequestString: query})
	out, _ := json.Marshal(result)
	fmt.Printf("\n# %s\n", title)
	fmt.Printf("query    : %s\n", strings.Join(strings.Fields(query), " "))
	fmt.Printf("response : %s\n", out)
	return result
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	schema := buildSchema()

	fmt.Println("=== the schema, as SDL: three object types, wired together ===")
	fmt.Println(`type Query {
  reports: [Report!]!
  report(id: ID!): Report
}

type Report {
  id: ID!
  title: String!
  owner: User!
  summary(maxLength: Int = 10): String!
}

type User {
  name: String!
  email: String!
  team: Team!
}

type Team {
  name: String!
  region: String!
}`)

	// Asking for an object WITHOUT choosing fields inside it is meaningless,
	// so the schema rejects it. GraphQL has no "give me the whole object".
	result := run(schema, "1. selecting an object with no sub-selection is an error", `{ report(id: "r1") }`)
	must(result.Data == nil, "data is null")
	must(strings.Contains(result.Errors[0].Message, "must have a sub selection"), "sub-selection required")

	result = run(schema, "2. one level deep: only the report's own fields", `{ report(id: "r1") { id title } }`)
	report := result.Data.(map[string]any)["report"].(map[string]any)
	must(report["id"] == "r1" && report["title"] == "Q1 uptime" && len(report) == 2, "flat report")
	must(calls["owner"] == 0, "owner was not requested, so its resolver did not run")

	result = run(schema, "3. two levels: the owner resolver runs with the Report as its parent",
		`{ report(id: "r1") { title owner { name email } } }`)
	report = result.Data.(map[string]any)["report"].(map[string]any)
	owner := report["owner"].(map[string]any)
	must(owner["name"] == "Ada" && owner["email"] == "ada@example.com", "owner resolved")
	fmt.Println("resolver calls:", calls)
	must(calls["owner"] == 1 && calls["team"] == 0, "one owner call, no team call")

	result = run(schema, "4. three levels: report -> owner -> team, one round trip",
		`{ report(id: "r1") { title owner { name team { name region } } } }`)
	report = result.Data.(map[string]any)["report"].(map[string]any)
	team := report["owner"].(map[string]any)["team"].(map[string]any)
	must(team["name"] == "platform" && team["region"] == "eu-west", "team resolved")
	fmt.Println("resolver calls:", calls)
	must(calls["team"] == 1, "team resolver ran once")
	fmt.Println("   -> in REST this is three requests (/reports/r1, /users/u1, /teams/t1)")

	// The chain repeats per parent: 2 reports -> the owner resolver runs twice.
	before := calls["owner"]
	result = run(schema, "5. a LIST of objects: the child resolver runs once per parent",
		"{ reports { title owner { name } } }")
	must(len(result.Data.(map[string]any)["reports"].([]any)) == 2, "two reports")
	fmt.Printf("owner resolver calls for 2 reports: %d\n", calls["owner"]-before)
	must(calls["owner"]-before == 2, "once per parent")
	fmt.Println("   -> 1 + N resolver calls. With a database behind `owner` that is the N+1 problem (see ../labs/)")

	result = run(schema, "6. a nested field taking its own argument", `{ report(id: "r2") { summary(maxLength: 2) } }`)
	report = result.Data.(map[string]any)["report"].(map[string]any)
	must(report["summary"] == "Q2", "nested argument")

	fmt.Println("\nOK")
}
